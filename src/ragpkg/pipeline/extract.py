import trafilatura
import requests
from bs4 import BeautifulSoup
import re
from pydoc import html
from ragpkg.logs.logger import get_logger


class text_extract:

    def __init__(self,input_url):
        self.url= input_url


    def extract_text_trafilatura(self,html_content):
        extracted_text = trafilatura.extract(html_content)
        return extracted_text



    def extract_using_bs_main(self,html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_text = soup.find('main')
        if extracted_text:
            extracted_text = extracted_text.get_text(separator='\n')
            return extracted_text
        else:
            return 


    def clean_text(self,s: str):
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def split_paragraphs(self,text: str):
        paras = [self.clean_text(p) for p in re.split(r"\n", text) if clean_text(p)]
        return paras

    def process_url(self):

        ### Below steps as part of processing url
        ## 1. Extract text using main
        ## 2. If not extract using trafilatura
        ## 3. Remove Standard words using regex like @copyright etc
        ## 4. call Llm for for removing noise from text
        
        logger = get_logger(__name__)
        logger.info("Starting Processing the URL ...")

        if((self.url is None) | (self.url.strip() == "" )):
            logger.info(f"URL is Invalid. Please provide a valid URL : {url}")
            print("URL is Invalid. Please provide a valid URL.")
            return
        
        response = requests.get(self.url)
        if response.status_code == 200:
            html_content = response.text
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

        extracted_text = self.extract_using_bs_main(html_content)
        if(extracted_text is None):
            extracted_text = self.extract_text_trafilatura(html_content)

        # paras = split_paragraphs(extracted_text)

        return extracted_text