import gzip as gz
import json as jn
import zipfile as zf
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from models import nlp
from parsers.general import ParserOutput
from visualizer import top_pie_visualization


class NumpyEncoder(jn.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)


class FacebookOutput(ParserOutput):
    def __init__(self, uid, messages, reactions):
        """
        Create a Facebook parser

        Args:
            uid: The facebook user ID. Likely an integer.
            messages: A pandas table keyed on a message id with a conversation id attached.
                For now, the other fields don't matter.
            reactions: A list of reactions that the user has
        """
        self.uid = uid
        self.reactions = reactions

        # really dumb, but we can just slap on a sentiment per-message
        # could take a while to compute
        executor = ThreadPoolExecutor()
        self.messages = messages.dropna('index', 'any', subset=['content'])
        messageTexts = self.messages['content'].values
        map(nlp.evaluate_sentiment, messageTexts)

        cachepath = Path("out/cache")
        sentiment_cache_path = cachepath / "sentiment.txt.gz"
        sentiment_values = {}

        if sentiment_cache_path.exists():
            with gz.open(sentiment_cache_path, 'r') as filehandle:
                sentiment_values = jn.load(filehandle)

        def writeback():
            cachepath.mkdir(parents=True, exist_ok=True)
            with gz.open(sentiment_cache_path, 'wt') as outfile:
                print("Dying with values {}".format(sentiment_values))
                # https://stackoverflow.com/a/27050186/998335
                jn.dump(sentiment_values, outfile, cls=NumpyEncoder)
                outfile.flush()

        def evaluate_sentiment_cached(sentence):
            if sentence in sentiment_values:
                return sentiment_values[sentence]
            result = nlp.evaluate_sentiment(sentence)
            sentiment_values[sentence] = result
            return result

        try:
            sentiments = list(tqdm(executor.map(evaluate_sentiment_cached, messageTexts), total=len(messageTexts)))
        finally:
            # Cache the stuff
            writeback()

        self.messages.assign(sentiment=sentiments)

        def num_words(text) -> int:
            if isinstance(text, float):
                return 1
            return len(text.split())

        # this could be iffy, the concept of "float" is strange here
        def num_characters(text):
            if isinstance(text, float):
                # float formatting
                return len("{0:.3g}".format(text))
            return len(text)

        # takes list of author-message pairs, returns list of entries want to see
        def message_ops(pairs: pd.DataFrame) -> list:
            return [len(pairs.values), sum((num_words(i[-1]) for i in pairs.values)),
                    sum((num_characters(i[-1]) for i in pairs.values))]

        # messenger-centric approach
        grouped = self.messages[['sender_name', 'content', 'sentiment']].groupby(['sender_name'], sort=False)
        self.to_csv("out/Facebook/messages.csv")
        self.author_table = grouped.apply(message_ops)  # NOT the same as the below apply
        cols = ['num_messages', 'num_words', 'num_characters_norm']
        self.author_table = pd.DataFrame(self.author_table.values.tolist(),
                                         index=self.author_table.index,
                                         columns=cols)
        self.author_table.sort_values(cols, ascending=False, inplace=True)

        # space-delimited
        # print(self.messages[self.messages['sender_name'] == 'Jack Youstra'][:10])

    @staticmethod
    def service() -> str:
        return "Facebook"

    def visualize(self, root_path: Path):
        instance_path = root_path / self.resource_path()
        if not instance_path.exists():
            # we should recreate
            instance_path.mkdir(exist_ok=True, parents=True)
            self.pie_visualize(instance_path)

    def pie_visualize(self, path: Path):
        slices = 20
        top_pie_visualization("top {} messengers".format(slices), path,
                              self.author_table['num_messages'].values, self.author_table.index.values,
                              slice_count=slices)
        word_toppers = self.author_table.sort_values('num_words', ascending=False)
        top_pie_visualization("top {} messengers by words".format(slices), path,
                              word_toppers['num_words'].values, word_toppers.index.values, slice_count=slices)
        character_toppers = self.author_table.sort_values('num_characters_norm', ascending=False)
        top_pie_visualization("top {} messengers by normalized characters".format(slices), path,
                              character_toppers['num_characters_norm'].values, character_toppers.index.values, slices)
        top_pie_visualization("Reactions by type", path, self.reactions, self.reactions.index.values)


def parse_facebook(filepath):
    message_frames = []
    reactions = None
    with zf.ZipFile(filepath, 'r') as zipObj:
        # Get list of files names in zip
        fileList = zipObj.namelist()
        # Iterate over the list of file names in given list & print them
        for filename in fileList:
            if "messages/inbox" in filename:
                if filename[-5:] == ".json":
                    # main messages body
                    # the title of the message is currently <name of counterparty or group chat>_<conversationUUID(I think)>
                    # example: messages/inbox/friendlygroupchat_ksfzjduiuw/message_1.json
                    # example: messages/inbox/jackyosutra_kfcznquruw/message_1.json
                    data = zipObj.read(filename)
                    chat_data = jn.loads(data.decode("utf-8"))
                    participants = []
                    conversation_id = chat_data["thread_path"]
                    conversation_id = conversation_id[conversation_id.index("/") + 1:]
                    participant_data = chat_data["participants"]
                    for participant in participant_data:
                        if len(participant) > 1:
                            print("in participant, there's {}".format(participant.keys))
                        participants.append(participant["name"])
                    messages = chat_data["messages"]
                    message_fragment = pd.DataFrame.from_records(messages)
                    message_fragment['conversation_id'] = conversation_id
                    message_frames.append(message_fragment)
            if "likes_and_reactions/posts_and_comments.json" in filename:
                # the reactions portion
                data = zipObj.read(filename)
                reaction_data = jn.loads(data.decode("utf-8"))
                reactions = pd.DataFrame.from_records(reaction_data['reactions'])
                # The actor field here should always be the current user, ditch
                # I have no idea what this attachments field is used for. I'm going to ignore it for now
                thing = reactions["data"].values

                def unpack(reaction_struct):
                    assert len(reaction_struct) == 1
                    return reaction_struct[0]['reaction']['reaction']

                reactions["type"] = [unpack(x) for x in reactions["data"].values]
                reactions.drop(['data', 'attachments'], axis=1, inplace=True)

    final_out = pd.concat(message_frames, copy=False, ignore_index=True, sort=False)

    return FacebookOutput(1, final_out, reactions)
