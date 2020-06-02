import argparse
import astunparse
import sys

from . import check

parser = argparse.ArgumentParser()
parser.add_argument("file", nargs="?", type=argparse.FileType("r"),
                     default=sys.stdin)

args = parser.parse_args()
poisoned = check(args.file.read())

print("Possible SQL injections:")
for p in poisoned:
    print("line {}: {}".format(p.get_lineno(), p.get_source()))
