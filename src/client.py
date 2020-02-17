import argparse as ap
import itertools as it
import logging as lg
from multiprocessing.pool import Pool
from pathlib import Path

from parsers.general import parse, combined_services

# noinspection PyArgumentList
lg.basicConfig(
    level=lg.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        lg.StreamHandler()
    ])


def process_source(source, reduced):
    path = Path(source)
    if not path.is_file():
        lg.error("{} is not a file".format(path.resolve()))
        exit(1)
    result = parse(source, reduced)
    if result is None:
        lg.warning("Couldn't find a parser for {} - skipping".format(path.name))
    else:
        print("Parsed {}".format(str(result)))
        result.visualize(base_path)
    return result


if __name__ == '__main__':
    parser = ap.ArgumentParser()
    # we parse all of the sources and determine which parser to use automatically
    parser.add_argument("sources", metavar="source", type=str, nargs="+",
                        help="A series of sources from which to parse")
    parser.add_argument("-r", "--reduced", help="Operate on a reduced from the input. Useful for testing.")
    args = parser.parse_args()

    base_path = Path("out/")

    source_pool = Pool()
    # can't do multiprocessing with parent TF: https://github.com/tensorflow/tensorflow/issues/5448
    parsed_representations = source_pool.starmap(process_source, it.product(args.sources, [args.reduced]))
    print([x.service() for x in parsed_representations])
    combined_services(parsed_representations)
