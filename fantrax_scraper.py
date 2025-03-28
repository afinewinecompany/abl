import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_fantrax_standings(league_url: str) -> pd.DataFrame:
    """
    Scrape standings data from a Fantrax league page.

    Args:
        league_url (str): URL of the Fantrax league standings page

    Returns:
        pd.DataFrame: A DataFrame containing team standings data
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(league_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to load page. Status code: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")

    if not table:
        raise Exception("Could not find standings table on the page.")

    headers = [th.text.strip() for th in table.find("thead").find_all("th")]

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.text.strip() for td in tr.find_all("td")]
        rows.append(cells)

    df = pd.DataFrame(rows, columns=headers)

    return df