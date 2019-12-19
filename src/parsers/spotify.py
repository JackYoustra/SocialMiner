import json as jn
import zipfile as zf
import pandas as pd

from parsers.general import ParserOutput
from visualizer import DurationVisualizeable


class SpotifyOutput(ParserOutput, DurationVisualizeable):
    def __init__(self, uid, playTable):
        self.uid = uid
        self.playTable = playTable

    @staticmethod
    def service() -> str:
        return "Spotify"

    def sorted_playtimes(self):
        return sorted(self.playTable["msPlayed"])


# return a table of plays, with songs, artists, and playtimes
def parse_spotify(filepath):
    playTable = pd.DataFrame(columns=["endTime", "artistName", "trackName", "msPlayed"])
    with zf.ZipFile(filepath, 'r') as zipObj:
        # Get list of files names in zip
        fileList = zipObj.namelist()
        # Iterate over the list of file names in given list & print them
        for filename in fileList:
            if "Playlist" in filename:
                # playlists

                pass
            elif "StreamingHistory" in filename:
                # streaming history
                data = zipObj.read(filename)
                streaming_data_part = jn.loads(data.decode("utf-8"))
                other = pd.DataFrame.from_records(streaming_data_part)
                r, c = playTable.shape
                playTable = pd.concat([playTable, other], copy=False)
                assert (playTable.shape == (r + other.shape[0], c))
            pass

    # now clean the playTable
    playTable.drop(playTable.loc[playTable["msPlayed"] == 0.0].index, inplace=True)
    return SpotifyOutput(1, playTable)
