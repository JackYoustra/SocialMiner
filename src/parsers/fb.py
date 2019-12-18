import json as jn
import zipfile as zf
import pandas as pd

class FacebookOutput:
    def __init__(self, uid):
        self.uid = uid

    @staticmethod
    def service():
        return "Facebook"

def parse_facebook(filepath):
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
                    participant_data = chat_data["participants"]
                    for participant in participant_data:
                        if len(participant) > 1:
                            print("in participant, there's {}".format(participant.keys))
                        participants.append(participant["name"])
                    messages = chat_data["messages"]
                    for message in messages:
                        pass
