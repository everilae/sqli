from __future__ import print_function
import sys
import requests
from sqli import check
from bs4 import BeautifulSoup
from textwrap import dedent
from argparse import ArgumentParser

_parser = ArgumentParser(description="Find vulnerable Python from SO")
_parser.add_argument("tags", nargs="*",
                     default=["sql"],
                     help="Search posts tagged with tags")


def fetch_post_soup(link):
    resp = requests.get(link)
    return BeautifulSoup(resp.text, "lxml")


def fetch(tags):
    url = 'https://api.stackexchange.com/2.2/questions'
    params = dict(
        page=1,
        pagesize=100,
        order="desc",
        sort="creation",
        tagged=';'.join(["python"] + list(tags)),
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
                poisoned = check(source)
                if poisoned:
                    print(link, ':')
                    for p in poisoned:
                        print("#{}: {}".format(p.get_lineno(), p.get_source()))
                    break

            except Exception as e:
                # Just ignore
                pass

if __name__ == "__main__":
    args = _parser.parse_args()
    try:
        fetch(args.tags)

    except KeyboardInterrupt:
        pass
