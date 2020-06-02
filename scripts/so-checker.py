import sys
import requests
import calendar
import logging

from sqli import check

from bs4 import BeautifulSoup

from textwrap import dedent
from argparse import ArgumentParser
from datetime import datetime
from itertools import chain


def date_argument(arg):
    if arg == "today":
        return (datetime.utcnow()
                .replace(hour=0, minute=0, second=0, microsecond=0))

    else:
        return datetime.strptime(arg, "%Y-%m-%d")

_parser = ArgumentParser(description="Find vulnerable Python from SO")
_parser.add_argument("tags", nargs="*",
                     default=["sql"],
                     help="Search posts tagged with tags")
_parser.add_argument("--from-date", type=date_argument,
                     help="Filter against creation_date")
_parser.add_argument("--page-size", type=int, default=100,
                     help="Maximum items per page")
_parser.add_argument("--log", default="info")

_SITE = "stackoverflow"
_FILTER = "!5-dm_.B4KdW3(tKMnD-gYaOdS-mkdxhSIbFHRm"


def fetch_post_soup(item):
    bs = [item["body"]]

    if "answers" in item:
        bs += [a["body"] for a in item["answers"]]

    return (BeautifulSoup(body, "lxml") for body in bs)


def fetch(tags, from_date, page_size):
    url = 'https://api.stackexchange.com/2.2/questions'
    params = dict(
        page=1,
        pagesize=page_size,
        order="desc",
        sort="creation",
        tagged=';'.join(["python"] + list(tags)),
        site=_SITE,
        filter=_FILTER,
    )

    if from_date:
        params["fromdate"] = calendar.timegm(from_date.utctimetuple())

    resp = requests.get(url, params=params)
    items = resp.json()["items"]
    for it in items:
        link = it["link"]
        created = datetime.utcfromtimestamp(it["creation_date"])
        soups = fetch_post_soup(it)
        codes = chain.from_iterable(soup.select("code") for soup in soups)
        poisoned = []
        for code in codes:
            source = dedent(code.text)
            try:
                poisoned.extend(check(source))

            except Exception as e:
                # Just ignore
                pass

        if poisoned:
            print("{:%Y-%m-%d} {}:".format(created, link))
            for p in poisoned:
                print("#{}: {}".format(p.get_lineno(), p.get_source()))

if __name__ == "__main__":
    args = _parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper()))
    try:
        fetch(tags=args.tags,
              from_date=args.from_date,
              page_size=args.page_size)

    except KeyboardInterrupt:
        pass
