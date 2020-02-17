import numpy as np
import pandas as pd

from parsers.fb import FacebookOutput
from parsers.spotify import SpotifyOutput


def tag_music(fb: FacebookOutput, spotify: SpotifyOutput, event_threshold: int = 20) -> pd.DataFrame:
    # each message has a current song playing, or none to indicate no song playing
    # the song will be referred to by its playTable ID
    # It will return a dataframe of indexes to songs played
    current_song_series = np.full(len(fb.messages.index.values), -1)
    i = -1
    current_spotify_index = -1
    current_spotify_start = 0
    current_spotify_end = -1
    current_spotify_id = 0
    sorted_timestamp_messages = fb.messages.sort_values(by=['timestamp_ms'], kind='mergesort')
    for message_id, timestamp in zip(sorted_timestamp_messages.index.values,
                                     sorted_timestamp_messages['timestamp_ms'].values):
        i += 1
        while (current_spotify_end < timestamp) and current_spotify_index < len(spotify.playTable.index.values):
            current_spotify_index += 1
            current_spotify_end = spotify.playTable['endTime'].values[current_spotify_index]
            current_spotify_start = current_spotify_end - spotify.playTable['msPlayed'].values[current_spotify_index]
            print("spotify start: {}, end: {}, timestamp: {}".format(current_spotify_start, current_spotify_end,
                                                                     timestamp))
            current_spotify_id = spotify.playTable.index.values[current_spotify_index]
        if current_spotify_start > timestamp:
            continue

        assert current_spotify_start <= timestamp <= current_spotify_end
        current_song_series[i] = current_spotify_id

    # t value is now is array with the first entry being the song ID and every subsequent entry a message
    retVal = pd.DataFrame(data=current_song_series, index=sorted_timestamp_messages.index, columns=["song_id"])
    return retVal
