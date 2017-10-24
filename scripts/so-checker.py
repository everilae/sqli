from __future__ import print_function
import sys
import requests
from sqli import check
from bs4 import BeautifulSoup
from textwrap import dedent
from argparse import ArgumentParser
from datetime import datetime

_parser = ArgumentParser(description="Find vulnerable Python from SO")
_parser.add_argument("tags", nargs="*",
                     default=["sql"],
                     help="Search posts tagged with tags")

_SITE = "stackoverflow"
_FILTER = "!5-dm_.B4KdW3(tKMnD-gYaOdS-mkdxhSIbFHRm"


def fetch_post_soup(item):
    body = item["body"]

    if "answers" in item:
        body += "\n".join(a["body"] for a in item["answers"])

    return BeautifulSoup(body, "lxml")


def fetch(tags):
    url = 'https://api.stackexchange.com/2.2/questions'
    params = dict(
        page=1,
        pagesize=100,
        order="desc",
        sort="creation",
        tagged=';'.join(["python"] + list(tags)),
        site=_SITE,
        filter=_FILTER,
    )
    resp = requests.get(url, params=params)
    items = resp.json()["items"]
    for it in items:
        link = it["link"]
        created = datetime.utcfromtimestamp(it["creation_date"])
        soup = fetch_post_soup(it)
        for code in soup.select("code"):
            source = dedent(code.text)
            try:
                poisoned = check(source)
                if poisoned:
                    print("{:%Y-%m-%d} {}:".format(created, link))
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
