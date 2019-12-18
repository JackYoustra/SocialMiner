import zipfile as zf
import logging as lg
from abc import ABCMeta, abstractmethod
from parsers.fb import parse_facebook
from parsers.spotify import parse_spotify


def ParserOutput(metaclass=ABCMeta):
    def __init__(self, ):
        pass

    @staticmethod
    @abstractmethod
    def service():
        pass

def isSpotify(fileList):
    for file in fileList:
        if file[-5:] != ".json" and file[7:] != "Read Me First.pdf" and file[-1] != "/":
            lg.debug("Can't find spotify because found {}".format(file))
            return False
    return True

# return a pandas table with a list of messages, and a pandas table with a list of conversations
# Each message has a reference to its conversation
def parse(filepath):
    parser = None
    if zf.is_zipfile(filepath):
        with zf.ZipFile(filepath, 'r') as zipObj:
            # Get list of files names in zip
            fileList = zipObj.namelist()
            # Iterate over the list of file names in given list & print them
            if "messages/" in fileList:
                # we're probably facebook
                parser = parse_facebook
            elif isSpotify(fileList):
                parser = parse_spotify

    if parser is None:
        return None
    return parser(filepath)
