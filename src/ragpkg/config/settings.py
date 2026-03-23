from dotenv import load_dotenv
import os
load_dotenv()


class AppSettings:
    def __init__(self):
        self.CONCURRENCY = int(os.getenv("RAG_FETCH__CONCURRENCY", 12))
        self.CONNECT_TIMEOUT_SEC = int(os.getenv("RAG_FETCH__CONNECT_TIMEOUT_SEC", 25))
        self.READ_TIMEOUT_SEC = int(os.getenv("RAG_FETCH__READ_TIMEOUT_SEC", 25))
        self.INPUT_URLS_FILE = os.getenv("RAG_INPUT_URLS_FILE", "data/stripe_urls.txt")
        self.LOG_LEVEL = os.getenv("RAG_LOG_LEVEL", "DEBUG")


settings = AppSettings()