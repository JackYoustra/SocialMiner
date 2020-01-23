# from tensorflow.compat.v1 import ConfigProto
# from tensorflow.compat.v1 import InteractiveSession
#
# # memory explodes without this
# config = ConfigProto()
# config.gpu_options.per_process_gpu_memory_fraction = 1.0
# config.gpu_options.allow_growth = True
# session = InteractiveSession(config=config)

from transformers import pipeline

sentiment_pipeline = pipeline('sentiment-analysis')


def evaluate_sentiment(sentence):
    try:
        pipeline = sentiment_pipeline(sentence)
    except:
        print("evaluating {}".format(sentence), end='')
        print("Oh man")

    return pipeline


if __name__ == '__main__':
    from concurrent.futures.thread import ThreadPoolExecutor
    from tqdm import tqdm
    from random import shuffle

    # three-letter animal names for benchmark
    sources = ["ant", "ape", "auk", "bat", "bee", "bot", "boy", "bug", "", "cat", "cod", "dab", "doe", "dog", "eel",
               "eft", "elk", "emu", "ewe", "fly", "fox", "gnu", "guy", "hen", "hog", "jay", "kea", "kit", "man", "owl",
               "pig", "ram", "rat", "sow", "teg", "yak", "cur", "pen", "roe", "ass"]


    def my_shuffle(thing):
        shuffle(thing)
        return thing


    words = [" ".join(my_shuffle(sources)) for _ in range(1000)]

    executor = ThreadPoolExecutor()

    sentiments = list(tqdm(map(evaluate_sentiment, words), total=len(words)))
    print(sentiments)

    # findings
    # for 100, 15 += ~1s for default, increasing number of workers yields 12s, changing device with lots of workers yields 3s

    # for 1000, device and 100 workers yields 55s
    # 1000 workers yields 3 seconds (???) error in measuring
    # default yields 55 seconds
    # no device yields much longer, probably around three minutes

    # for i9-9980HK without dGPU support, 1000 takes 2 min 30 sec with 20 workers. With 96 workers, takes ~2 min.
    # With default number of workers, takes 1 min 50 secs
