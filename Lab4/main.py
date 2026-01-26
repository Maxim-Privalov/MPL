from bs4 import BeautifulSoup
import pandas as pd
import requests
import random
import time
import re

MIN_DELAY = 45
MAX_DELAY = 120
MAX_RETRIES = 4
BACKOFF_FACTOR = 2

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

REFERERS = [
    "https://www.vesselfinder.com/",
    "https://www.vesselfinder.com/vessels",
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.vesselfinder.com/search",
]

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

LINK_FILE = "Links.xlsx"
RESULT_FILE = "result.xlsx"


class VesselFinderParser:
    def __init__(self, headers_base, user_agents, referers):
        self.session = requests.Session()
        self.headers_base = headers_base
        self.user_agents = user_agents
        self.referers = referers

    def _get_random_headers(self):
        headers = self.headers_base.copy()
        headers["User-Agent"] = random.choice(self.user_agents)
        headers["Referer"] = random.choice(self.referers)
        headers["Accept-Language"] = random.choice([
            "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "en-US,en;q=0.9,ru-RU;q=0.8",
            "de-DE,de;q=0.9,en-US;q=0.8"
        ])
        return headers

    def __fetch_soup(self, url, retries = MAX_RETRIES):
        for attempt in range(retries):
            try:
                headers = self._get_random_headers()
                resp = self.session.get(url, headers=headers, timeout=25)
                
                if resp.status_code == 429:  # Too Many Requests
                    wait = (BACKOFF_FACTOR ** attempt) * 30 + random.randint(10, 30)
                    print(f"429 Too Many Requests. Ждём {wait} сек...")
                    time.sleep(wait)
                    continue
                    
                if resp.status_code in (403, 503):
                    print(f"{resp.status_code} — возможно блокировка. Попытка {attempt+1}/{retries}")
                    time.sleep(random.uniform(20, 60))
                    continue

                resp.raise_for_status()
                return BeautifulSoup(resp.text, "html.parser")

            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    print(f"Не удалось загрузить {url} после {retries} попыток: {e}")
                    return None
                wait = (BACKOFF_FACTOR ** attempt) * 15 + random.randint(10, 25)
                print(f"Ошибка запроса (попытка {attempt+1}/{retries}). Ждём {wait:.1f} сек...")
                time.sleep(wait)


    def get_details_link_from_search(self, search_url):
        soup = self.__fetch_soup(search_url)
        if not soup:
            return None

        table = soup.find("table")
        if not table:
            print(f"Таблица не найдена — {search_url}")
            return None

        rows = table.find_all("tr")
        if len(rows) - 1 != 1:
            print(f"{search_url}: найдено {len(rows)-1} судов -> пропускаем")
            return None

        a_tag = rows[1].find("a")
        if not a_tag or "href" not in a_tag.attrs:
            print(f"Нет ссылки на детали — {search_url}")
            return None

        return "https://www.vesselfinder.com" + a_tag["href"]

    def extract_vessel_data(self, details_url):
        soup = self.__fetch_soup(details_url)
        if not soup:
            return None

        name_elem = soup.find("h1")
        name = name_elem.text.strip() if name_elem else "N/A"

        info_table = soup.find("table")
        data = {}

        if info_table:
            for tr in info_table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) == 2:
                    key = tds[0].text.strip()
                    value = tds[1].text.strip()
                    data[key] = value

        imo = data.get("IMO", "N/A")
        mmsi = data.get("MMSI", "N/A")
        vessel_type = data.get("AIS тип", "N/A")

        if imo == "N/A" or mmsi == "N/A":
            for val in data.values():
                if isinstance(val, str):
                    match = re.search(r"(\d{7})\D+(\d{9})", val)
                    if match:
                        imo_cand, mmsi_cand = match.groups()
                        if imo == "N/A" and len(imo_cand) == 7 and imo_cand.isdigit():
                            imo = imo_cand
                        if mmsi == "N/A" and len(mmsi_cand) == 9 and mmsi_cand.isdigit():
                            mmsi = mmsi_cand
                        if imo != "N/A" and mmsi != "N/A":
                            break

        return {
            "Name": name,
            "IMO": imo,
            "MMSI": mmsi,
            "Type": vessel_type,
            "Source URL": ""
        }



def process_links(links, headers_base, user_agents, referers, output_file, first_write=True):
    parser = VesselFinderParser(headers_base, user_agents, referers)
    successful_vessel_count = 0

    for url in links:
        delay = random.uniform(16, 32)
        print(f"Ждём {delay:.1f} сек перед {url}")
        time.sleep(delay)

        try:
            details_url = parser.get_details_link_from_search(url)
            if not details_url:
                continue

            vessel_data = parser.extract_vessel_data(details_url)
            if not vessel_data:
                continue
            
            vessel_data["Source URL"] = url

            df_new = pd.DataFrame([vessel_data])
            successful_vessel_count += 1
            if first_write:
                df_new.to_excel(output_file, index=False)
                first_write = False
            else:
                with pd.ExcelWriter(output_file, mode="a", if_sheet_exists="overlay", engine="openpyxl") as writer:
                    startrow = writer.sheets["Sheet1"].max_row
                    df_new.to_excel(writer, index=False, header=False, startrow=startrow)

            print(f"Обработано и сохранено: {url} -> {vessel_data['Name']}")

        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue

    if successful_vessel_count > 0:
        print(f"Число сохранённых суден {successful_vessel_count}")
        print("Результаты сохранены в result.xlsx")
    else:
        print("Не найдено ни одного валидного судна")


if __name__ == "__main__":
    df_links = pd.read_excel("Links.xlsx")
    links = df_links["Ссылка"].tolist()[16:]
    process_links(links, HEADERS_BASE, USER_AGENTS, REFERERS, RESULT_FILE, first_write=True)