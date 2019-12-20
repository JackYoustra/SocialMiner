import argparse as ap
import logging as lg
from pathlib import Path

from parsers.general import parse

# noinspection PyArgumentList
lg.basicConfig(
    level=lg.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        lg.StreamHandler()
    ])

if __name__ == '__main__':
    parser = ap.ArgumentParser()
    # we parse all of the sources and determine which parser to use automatically
    parser.add_argument("sources", metavar="S", type=str, nargs="+", help="A series of sources from which to parse")
    args = parser.parse_args()

    base_path = Path("../out/")

    for source in args.sources:
        path = Path(source)
        if not path.is_file():
            lg.error("{} is not a file".format(path.resolve()))
            exit(1)
        result = parse(source)
        if result is None:
            lg.warning("Couldn't find a parser for {} - skipping".format(path.name))
        else:
            print("Parsed {}".format(str(result)))
            result.visualize(base_path)
