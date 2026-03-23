# Orchestration: crawl → fetch → extract → normalize → 

# get URLs (crawl/sitemap)
# fetch concurrently
# extract (main → fallback)
# normalize (global + site-specific rules)
# chunk (text + tables)
# embed
# store (vector + doc store)
# Metrics + logging.


from aiohttp import ClientSession, ClientTimeout,TCPConnector
import asyncio
from ragpkg.extraction.extract import text_extract
from ragpkg.config.settings import settings



async def main():

    CONCURRENCY = settings.CONCURRENCY
    TIMEOUT = settings.CONNECT_TIMEOUT_SEC
    url_link = "https://stripe.com/in/guides/payment-methods-guide"

    DEFAULT_TIMEOUT =  ClientTimeout(
                    total=None,
                    sock_connect=TIMEOUT,
                    sock_read=TIMEOUT
                    
    )
    ## TCP Connection
    conn = TCPConnector(limit=CONCURRENCY)
    ## Define TimeoutW
    # timeout = DEFAULT_TIMEOUT

    async with ClientSession(
    connector=conn,
    timeout=DEFAULT_TIMEOUT,

    )as session:
        ## Semaphore for limiting the concurrency
        sem = asyncio.Semaphore(CONCURRENCY)
        extr = text_extract(url_link)
        async with sem:
            print(extr.process_url())

    return 


if __name__ == "__main__":
    asyncio.run(main())