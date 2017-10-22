import sys
import astunparse
from . import check

if len(sys.argv) >= 2:
    with open(sys.argv[1]) as f:
        source = f.read()

else:
    source = sys.stdin.read()

poisoned = check(source)

print("Possible SQL injections:")
for p in poisoned:
    print("line {}: {}".format(p.get_lineno(), p.get_source()))
