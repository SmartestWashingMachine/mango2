import re

# From: https://stackoverflow.com/questions/4836710/is-there-a-built-in-function-for-string-natural-sort
natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split("(\d+)", s)]
