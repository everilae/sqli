import sys
import requests
from sqli import check
from bs4 import BeautifulSoup
from textwrap import dedent


def fetch_post_soup(link):
    resp = requests.get(link)
    return BeautifulSoup(resp.text, "lxml")


def fetch():
    url = 'https://api.stackexchange.com/2.2/questions'
    params = dict(
        page=1,
        pagesize=100,
        order="desc",
        sort="creation",
        tagged=';'.join(["python", "sqlite"]),
        site="stackoverflow"
    )
    resp = requests.get(url, params=params)
    items = resp.json()["items"]
    for it in items:
        link = it["link"]
        soup = fetch_post_soup(link)
        for code in soup.select(".post-text code"):
            source = dedent(code.text)
            try:
                if check(source):
                    print(link)
                    break

            except Exception as e:
                # Just ignore
                pass

if __name__ == "__main__":
    try:
        fetch()

    except KeyboardInterrupt:
        pass
