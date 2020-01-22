import logging as lg
import zipfile as zf
from abc import abstractmethod

from visualizer import Pathnamed


class ParserOutput(Pathnamed):
    @staticmethod
    @abstractmethod
    def service() -> str:
        pass

    def resource_path(self) -> str:
        return self.service()

    def __str__(self):
        return self.service()


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
            # Put imports here because want to load tensorflow into child: https://github.com/tensorflow/tensorflow/issues/5448
            if "messages/" in fileList:
                # we're probably facebook
                from parsers.fb import parse_facebook
                parser = parse_facebook
            elif isSpotify(fileList):
                from parsers.spotify import parse_spotify
                parser = parse_spotify

    if parser is None:
        return None
    return parser(filepath)

