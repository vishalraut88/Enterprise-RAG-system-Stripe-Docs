from bs4 import BeautifulSoup

class table_extract:
    
    def __init__(self,html_content):
        self.html = html_content

    def extract_table(self):
        soup = BeautifulSoup(self.html, 'html.parser')

        tables = []
        for t in soup.find_all("table"):
            rows = []
            for tr in t.find_all("tr"):
                cells = [c.get_text(" ").replace("\n","").strip() for c in tr.find_all(["th","td"])]
                if (cells):
                    rows.append(cells)
            if rows:
                tables.append(rows)
                print(tables)

            t.decompose()

        return soup