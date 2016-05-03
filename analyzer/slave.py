import time
import logging
import os
import queue

from . import topics, tweetparser, modes
from .statistics import Statistics
from databases.mongodb import MongoDB
from databases.postgres import PostgresDB, Userdata
from common.constants import PG_USER, PG_PWD, PG_HOST, PG_DB, MONGO_USER, MONGO_PWD, MONGO_DB, MONGO_HOST
from common.twitterAPI import TwitterSearchApi
from databases.neo4j import GraphDB


def run(*args):
    slave = Analyzer(*args)
    slave.run()


class Analyzer():
    def __init__(self, queue, name, stat_queue, mode):
        self.queue = queue
        statistics = Statistics(stat_queue)
        self.ctx = Context(name, statistics)
        self.pid = os.getpid()
        self.mode = mode or modes.DefaultMode()

        topics.load_topics(self.ctx.mongo)

    def run(self):
        running = True
        self.ctx.logger.info("Starting slave with PID %d", self.pid)

        while running:
            try:
                try:
                    item = self.queue.get(timeout=10)
                    self.process_tweet(item)
                    time.sleep(0.01)
                except queue.Empty:
                    time.sleep(1)

            except KeyboardInterrupt:
                self.ctx.logger.warning("Interrupted, terminating slave.")
                running = False

    def process_tweet(self, tweet):
        t = Tweet(tweet, self.ctx)
        t.analyze(self.mode)
        t.set_processed()


class Tweet():
    def __init__(self, o, ctx):
        self.o = o
        self.ctx = ctx

        self.user_o = o.get('user', {})
        self.tweet_o = o.get('tweet', {})

        self.tweet_o = o.get('tweet', {})
        self.text = self.tweet_o.get('text', '')
        self.screen_name = self.user_o.get('screen_name')
        self.user_id = self.user_o.get('id_str')

        self.user = self.ctx.get_user_by_id(self.user_id)


    def analyze(self, mode):
        mode.analyze(self)

        # commented
        #self.analyze_ats()

        self.ctx.statistics.add_tweet(self.o)

    def set_processed(self):
        self.ctx.set_processed(self.o)

    def analyze_topics(self):
        ts = topics.mine_topics(self.text)

        for t in ts:
            self.add_relation_user_to_topic(self.user, 'mentions', t)

    def analyze_relations(self):
        other_id = self.tweet_o.get('in_reply_to_user_id_str')
        if other_id:
            other_user = self.ctx.get_user_by_id(other_id)
            self.add_relation_user_to_user(self.user, 'replies_to', other_user)

    def analyze_ats(self):
        ats = tweetparser.extract_ats(self.text)
        for at in ats:
            other_user = self.ctx.get_user_by_screen_name(at)
            self.add_relation_user_to_user(self.user, 'comments', other_user)

    def analyze_retweets(self):
        retweet_count = self.tweet_o.get('retweet_count')
        if retweet_count:
            self.ctx.increment_user_counter(self.user, 'tweets_retweet_count', retweet_count)

    def analyze_favorites(self):
        favourites_count = self.tweet_o.get('favorite_count')
        if favourites_count:
            self.ctx.increment_user_counter(self.user, 'tweets_favorite_count', favourites_count)

    def add_relation_user_to_topic(self, user, relation, topic_name):
        self.ctx.add_relation_user_to_topic(user, relation, topic_name)

    def add_relation_user_to_user(self, user, relation, other_user):
        self.ctx.add_relation_user_to_user(user, relation, other_user)


class Context():
    def __init__(self, name, statistics):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        self.sql = PostgresDB(PG_USER, PG_PWD, PG_DB, PG_HOST)
        self.mongo = MongoDB(user=MONGO_USER, pwd=MONGO_PWD, dbname=MONGO_DB, host=MONGO_HOST)
        self.twitter = TwitterSearchApi()
        self.graph = GraphDB()
        self.statistics = statistics

    def add_relation_user_to_topic(self, user, relation, topic_name):
        if user and topic_name:
            self.graph.create_relation_user_to_topic(user, relation, topic_name)
        self.logger.debug("%30s -(%10s)-> %s", user, relation, topic_name)

        self.statistics.add_relation(relation)
        self.statistics.add_topic(topic_name)

    def add_relation_user_to_user(self, user, relation, other_user):
        if user and other_user:
            self.graph.create_relation_user_to_user(user, relation, other_user)
        self.logger.debug("%30s -(%10s)-> %s", user, relation, other_user)

        self.statistics.add_relation(relation)

    def increment_user_counter(self, user, counter, n):
        if user:
            self.graph.increment_user_counter(user, counter, n)
        print("%30s %s += %d" % (user, counter, n))


    def get_user_by_id(self, id):
        if not id:
            return None
        return self.sql.get_user(id)

        # if not u:
        #     try:
        #         u = self.__user_from_twitter(self.twitter.lookup_users(user_id=id)[0])
        #     except (twitter.api.TwitterError, urllib.error.HTTPError) as e:
        #         self.logger.warning("Unable to lookup user by user_id=%s: %s", id, str(e))
        #     except Exception as e:
        #         self.logger.error("Unable to lookup user by user_id=%s", id, exc_info=e)
        # return u

    def get_user_by_screen_name(self, screen_name):
        raise RuntimeError("We don't do that anymore.")
        # u = self.sql.get_user_by_screen_name(screen_name)
        #
        # if not u:
        #     try:
        #         u = self.__user_from_twitter(self.twitter.lookup_users(screen_name=screen_name)[0])
        #     except (twitter.api.TwitterError, urllib.error.HTTPError) as e:
        #         self.logger.warning("Unable to lookup user by screen_name=%s: %s", screen_name, str(e))
        #     except Exception as e:
        #         self.logger.error("Unable to lookup user by screen_name=%s", screen_name, exc_info=e)
        # return u

    def set_processed(self, o):
        self.mongo.update_tweet({'_id': o['_id']}, { '$set': { 'analyzer.processed': True, 'analyzer.retweets_favorites': True } })

    def __user_from_twitter(self, userdata):
        u = Userdata(id_str = userdata['id_str'],
                     screen_name = userdata['screen_name'],
                     followers_count = userdata['followers_count'],
                     friends_count = userdata['friends_count'],
                     statuses_count = userdata['statuses_count'],
                     favourites_count = userdata['favourites_count'])

        return u
