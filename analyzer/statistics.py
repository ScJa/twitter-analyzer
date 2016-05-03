import threading
from datetime import datetime

class Statistics():
    def __init__(self, queue):
        self.tweet_count = 0
        self.last_tweet = {}
        self.relations = {}
        self.topics = {}
        self.__queue = queue

    def start(self):
        self.__start_time = datetime.now()
        self.__thread = threading.Thread(target=self.run)
        self.__running = True
        self.__thread.start()

    def run(self):
        while self.__running:
            t, data = self.__queue.get()

            if t == 'tweet':
                self.tweet_count += 1
                self.last_tweet = data
            elif t == 'relation':
                add_to_dict(self.relations, data)
            elif t == 'topic':
                add_to_dict(self.topics, data)

    def stop(self):
        self.__running = False

    @property
    def status(self):
        return {
            'tweet_count': self.tweet_count,
            'relations': self.relations,
            'topics': self.topics,
            'uptime': str(self.uptime),
            'tweets_per_minute': "%.2f" % self.tweets_per_minute
        }

    @property
    def uptime(self):
        return datetime.now() - self.__start_time

    @property
    def tweets_per_minute(self):
        minutes = float(self.uptime.total_seconds()) / 60.0
        return float(self.tweet_count) / minutes

    def add_tweet(self, tweet):
        self.__queue.put(('tweet', tweet))

    def add_relation(self, relation):
        self.__queue.put(('relation', relation))

    def add_topic(self, topic_name):
        self.__queue.put(('topic', topic_name))


def add_to_dict(d, key):
    if key not in d:
        d[key] = 0
    d[key] += 1
