
# step2_extract_content.py
import asyncio
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional

import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import trafilatura
from tqdm.asyncio import tqdm as tqdm_async

INPUT_URLS_FILE = "data/stripe_urls.txt"
OUTPUT_JSONL = "data/stripe_docs.jsonl"
CONCURRENCY = 12
TIMEOUT = 25
USER_AGENT = "EnterpriseRAGBot/1.0 (+contact: your-email@example.com)"

# ---------- Utility structures ----------
@dataclass
class PageDoc:
    url: str
    title: Optional[str]
    h1: Optional[str]
    headings: List[str]
    content: List[str]  # clean paragraphs
    code_blocks: List[str]  # optional, useful later

def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_paragraphs(text: str) -> List[str]:
    paras = [clean_text(p) for p in re.split(r"\n{2,}", text) if clean_text(p)]
    return paras

# ---------- Extraction strategies ----------
def extract_with_main(html: str) -> Optional[PageDoc]:
    soup = BeautifulSoup(html, "lxml")

    # Title
    title = None
    if soup.title and soup.title.string:
        title = clean_text(soup.title.string)

    # Prefer <main>
    main = soup.find("main")
    if not main:
        # heuristic fallbacks for stripe-like docs containers
        main = soup.select_one("article, .DocsMarkdown, .docs-markdown, .DocContent, .doc-content")
    if not main:
        return None

    # Remove obvious non-content nodes occasionally present
    for selector in ["nav", "header", "footer", "aside", ".toc", ".TableOfContents", ".on-this-page"]:
        for node in main.select(selector):
            node.decompose()

    # Headings
    headings = []
    for h in main.select("h1, h2, h3, h4"):
        txt = clean_text(h.get_text(" "))
        if txt:
            headings.append(txt)

    # Capture h1 separately
    h1_tag = main.find("h1")
    h1 = clean_text(h1_tag.get_text(" ")) if h1_tag else None

    # Extract code blocks (optional—useful for dev docs)
    code_blocks = []
    for pre in main.find_all("pre"):
        txt = pre.get_text("\n")
        txt = txt.strip("\n")
        if txt:
            code_blocks.append(txt)

    # Extract text paragraphs from main
    # Keep list items and paragraphs
    texts = []
    for el in main.find_all(["p", "li"]):
        t = clean_text(el.get_text(" "))
        if t:
            texts.append(t)

    # Fallback to full main text if paragraph extraction is sparse
    if len(texts) < 3:
        body_text = clean_text(main.get_text("\n"))
        texts = [p for p in split_paragraphs(body_text) if p]

    # Filter out boilerplate phrases
    noise_patterns = [
        r"^on this page$",
        r"^navigation$",
        r"^cookie(s)?$",
        r"^privacy$",
        r"^legal$",
    ]
    final_paras = []
    for t in texts:
        low = t.lower()
        if any(re.search(pat, low) for pat in noise_patterns):
            continue
        # drop very short UI crumbs
        if len(t) < 20 and " " not in t:
            continue
        final_paras.append(t)

    if not final_paras:
        return None

    return PageDoc(
        url="",
        title=title,
        h1=h1,
        headings=headings,
        content=final_paras,
        code_blocks=code_blocks,
    )

def extract_with_trafilatura(html: str) -> Optional[PageDoc]:
    txt = trafilatura.extract(html, include_comments=False, include_tables=True, favor_precision=True)
    if not txt:
        return None
    paras = split_paragraphs(txt)
    if len(paras) < 1:
        return None
    return PageDoc(
        url="",
        title=None,
        h1=None,
        headings=[],
        content=paras,
        code_blocks=[],
    )

# ---------- Network + pipeline ----------
class FetchError(Exception):
    pass

@retry(
    reraise=True,
    retry=retry_if_exception_type(FetchError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=6),
)
async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=TIMEOUT) as resp:
        if resp.status != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
            raise FetchError(f"Bad status or content-type: {resp.status} {resp.headers.get('Content-Type','')}")
        return await resp.text()

async def process_url(session: aiohttp.ClientSession, url: str) -> Optional[PageDoc]:
    try:
        html = await fetch_html(session, url)
    except Exception:
        return None

    doc = extract_with_main(html)
    if not doc:
        doc = extract_with_trafilatura(html)
    if not doc:
        return None

    doc.url = url

    # Add an extra light cleanup pass: remove nav-y leftovers
    cleaned = []
    for p in doc.content:
        if len(p) < 3:
            continue
        if re.search(r"(©|all rights reserved|cookies|privacy|terms)", p, re.I):
            continue
        cleaned.append(p)
    doc.content = cleaned or doc.content
    return doc

async def main(input_file=INPUT_URLS_FILE, output_file=OUTPUT_JSONL):
    # Load URLs
    with open(input_file, "r", encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip()]

    conn = aiohttp.TCPConnector(limit=CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=TIMEOUT, sock_read=TIMEOUT)
    async with aiohttp.ClientSession(
        connector=conn,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    ) as session, aiofiles.open(output_file, "w", encoding="utf-8") as out:

        sem = asyncio.Semaphore(CONCURRENCY)

        async def bounded(u):
            async with sem:
                return await process_url(session, u)

        tasks = [bounded(u) for u in urls]
        results = []
        async for coro in tqdm_async.as_completed(tasks, total=len(tasks), desc="Extracting"):
            doc = await coro
            if doc:
                await out.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")

if __name__ == "__main__":
    asyncio.run(main())
