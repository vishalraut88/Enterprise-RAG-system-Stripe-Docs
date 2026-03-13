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
# from extract import text_extract
from ragpkg.pipeline.extract import text_extract

async def main():

    CONCURRENCY = 12
    TIMEOUT = 25
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


if __name__ == "__main__":
    asyncio.run(main())