import json as jn
import zipfile as zf
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from parsers.general import ParserOutput
from visualizer import Visualizeable, top_pie_visualization


class SpotifyOutput(ParserOutput, Visualizeable):
    def __init__(self, uid, playTable: pd.DataFrame, playlists: pd.DataFrame, misc_info):
        self.uid = uid
        # ['endTime', 'artistName', 'trackName', 'msPlayed']
        self.playTable = playTable
        print(self.playTable)
        self.playlists = playlists
        self.misc_info = misc_info

        # song-centric view of data
        self.songTable = self.playTable.drop(columns="endTime")  # meaningless (maybe clobber to make a start time?
        self.songTable = self.songTable.groupby(['artistName', 'trackName'], sort=False).aggregate({
            'artistName': 'first', 'trackName': 'first', 'msPlayed': sum
        })
        self.songTable.reset_index(inplace=True, drop=True)
        self.songTable.sort_values(by=['msPlayed'], inplace=True, ascending=False)

        # artist-centric view of data
        self.artistTable = self.songTable.groupby(['artistName'], sort=False).aggregate({
            'artistName': 'first', 'msPlayed': sum
        })
        self.artistTable.reset_index(inplace=True, drop=True)
        self.artistTable.sort_values(by=['msPlayed'], inplace=True, ascending=False)
        self.total_time = sum(self.songTable['msPlayed'].values)

    @staticmethod
    def service() -> str:
        return "Spotify"

    def visualize(self, root_path: Path):
        instance_path = root_path / self.resource_path()
        if not instance_path.exists():
            # we should recreate
            instance_path.mkdir(exist_ok=True, parents=True)
            self.duration_visualize(instance_path)
            self.pie_visualize(instance_path)

    def duration_visualize(self, output_dir):
        times = self.songTable['msPlayed'].values
        x = range(len(times))
        y = [time / 1000 for time in reversed(times)]
        fig, ax = plt.subplots(tight_layout=True)
        ax.plot(x, y)
        ax.set(xlabel='Number of songs', ylabel='Song duration (secs)', title='Songs with time less than or equal to y')
        ax.grid()
        fig.savefig(output_dir / "song_playtimes.png")

        ax.set_yscale("log")
        ax.set(xlabel='Number of songs', ylabel='Log song duration (secs)',
               title='Songs with time less than or equal to y')
        fig.savefig(output_dir / "song_playtimes_log.png")

    def pie_visualize(self, output_dir):
        slice_count = 20
        labels_and_sources = (
            ("top_20_playtimes", self.songTable["msPlayed"].values, self.songTable["trackName"].values),
            ("top_20_artists", self.artistTable["msPlayed"].values, self.artistTable["artistName"].values),
        )

        for label, pie_sources, pie_labels in labels_and_sources:
            top_pie_visualization(label, output_dir, pie_sources, pie_labels, slice_count=slice_count,
                                  total=self.total_time)


# return a table of plays, with songs, artists, and playtimes
def parse_spotify(filepath, reduced):
    playTable = pd.DataFrame(columns=["endTime", "artistName", "trackName", "msPlayed"])
    playlists = None
    misc_info = {}
    with zf.ZipFile(filepath, 'r') as zipObj:
        # Get list of files names in zip
        fileList = zipObj.namelist()
        # Iterate over the list of file names in given list & print them
        for filename in fileList:
            if "Playlist" in filename:
                # playlists
                data = zipObj.read(filename)
                playlist_data_part = jn.loads(data.decode("utf-8"))["playlists"]
                other = pd.DataFrame.from_records(playlist_data_part)
                if playlists is None:
                    playlists = other
                else:
                    r, c = playlists.shape
                    playlists = pd.concat([playTable, other], copy=False)
                    assert (playlists.shape == (r + other.shape[0], c))
            elif "StreamingHistory" in filename:
                # streaming history
                data = zipObj.read(filename)
                streaming_data_part = jn.loads(data.decode("utf-8"))
                other = pd.DataFrame.from_records(streaming_data_part)
                r, c = playTable.shape
                playTable = pd.concat([playTable, other], copy=False)
                assert (playTable.shape == (r + other.shape[0], c))
            elif "UserData" in filename:
                data = zipObj.read(filename)
                misc_info = jn.loads(data.decode("utf-8"))

    # now clean the playTable
    playTable.drop(playTable.loc[playTable["msPlayed"] == 0.0].index, inplace=True)
    # Epoch times are more convenient
    # The time is in UTC, so convert from there
    playTable['endTime'] = (pd.to_datetime(playTable['endTime']).values.astype('int64') // 1e6).astype('int64')
    return SpotifyOutput(1, playTable, playlists, misc_info)
