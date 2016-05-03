# -*- coding: utf-8 -*-
import logging
import threading
import time
import random
from datetime import datetime

from twitter.api import TwitterHTTPError

from common.twitterAPI import TwitterStreamingApi, TwitterSearchApi
from common import time_in_millis
from common.constants import LOGLEVEL, PG_DB, PG_HOST, PG_PWD, PG_USER, TWITTER_CRAWLER_ACCEPTED_LANGS
from common.constants import MONGO_DB, MONGO_HOST, MONGO_PWD, MONGO_USER, TWITTER_CRAWLER_TIMELINE_RPM
from databases.mongodb import MongoDB
from databases.postgres import PostgresDB

class Crawler():

    def __init__(self):
        """
        :return:
        """
        self.logger = logging.getLogger(Crawler.__name__)
        self.logger.setLevel(LOGLEVEL)
        self.postgres = PostgresDB(PG_USER, PG_PWD, PG_DB, PG_HOST)
        self.mongo = MongoDB(MONGO_USER, MONGO_PWD, dbname=MONGO_DB, host=MONGO_HOST)
        self.count_inserted_success = 0
        self.count_inserted_failed = 0
        self.count_language_rejects = 0
        self.time_last_tweet = None
        self.last_tweet = {}

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def is_running(self):
        raise NotImplementedError

    def toggle(self):
        running = self.is_running()
        if running:
            self.stop()
        else:
            self.start()
        return not running

    def handle_tweet(self, tweet):
        if 'user' not in tweet: return
        try:
            extracted = self.extract(tweet)
            if extracted['tweet']['lang'] in TWITTER_CRAWLER_ACCEPTED_LANGS:
                self.last_tweet = extracted
                self.time_last_tweet = datetime.now()
                self.write_to_database(extracted)
                self.write_to_document_store(extracted)
                self.count_inserted_success += 1
            else:
                self.count_language_rejects += 1
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(tweet)
            self.count_inserted_failed += 1

    def handle_all_tweets(self, tweet_list):
        for tweet in tweet_list:
            self.handle_tweet(tweet)

    def write_to_database(self, tweet):
        user_data = dict(tweet['user'])
        id_str = user_data.pop('id_str')
        self.postgres.insert_or_update_user(id_str, **user_data)

    def write_to_document_store(self, tweet):
        self.mongo.add_tweet(tweet)

    def extract(self, tweet):
        if 'timestamp_ms' in tweet:
            timestamp_ms = tweet['timestamp_ms']
        else:
            #created_at: Sun Nov 08 21:36:01 +0000 2015
            date = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
            timestamp_ms = time_in_millis(date)

        data = {
            'user': {'id_str': tweet['user']['id_str'],
                     'screen_name': tweet['user']['screen_name'],
                     'followers_count': tweet['user']['followers_count'],
                     'friends_count': tweet['user']['friends_count'],
                     'statuses_count': tweet['user']['statuses_count'],
                     'favourites_count': tweet['user']['favourites_count']
            },
            'tweet': {
                'id_str': tweet['id_str'],
                'in_reply_to_user_id_str': tweet['in_reply_to_user_id_str'],
                'timestamp_ms': timestamp_ms,
                'text': tweet['text'],
                'in_reply_to_status_id_str': tweet['in_reply_to_status_id_str'],
                'retweet_count': tweet['retweet_count'],
                'lang': tweet['lang'],
                'country_code': tweet['place']['country_code'] if tweet['place'] else None,
                'favorite_count': tweet['favorite_count']
            },
            'analyzer': {
                'processed': False
            },
            'crawler': {
                'timestamp_ms': time_in_millis(datetime.now())
            }
        }
        return data

    def get_database_info(self):
        return {'PostgreSQL': {'count': self.postgres.get_user_count()},
                'MongoDB': {'count': self.mongo.get_document_count()}}


class StreamCrawler(Crawler):

    def __init__(self):
        super().__init__()
        self.twitter = TwitterStreamingApi()
        self.twitter.add_stream_listener(self, self.handle_tweet)

    def start(self):
        self.twitter.start_stream()
        return self.twitter.is_stream_running()

    def stop(self):
        self.twitter.stop_stream()
        return self.twitter.is_stream_running()

    def is_running(self):
        return self.twitter.is_stream_running()


class ApiCrawler(Crawler):

    def __init__(self):
        super().__init__()
        self.thread = None
        self.twitter = TwitterSearchApi()

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def stop(self):
        self.thread = None

    def is_running(self):
        return self.thread is not None

    def run(self):
        self.logger.info('API Crawler started.')
        timeout_in_sec = 60.0 / TWITTER_CRAWLER_TIMELINE_RPM
        session, result = self.postgres.get_all_users()
        start = random.randint(0, self.postgres.get_user_count())
        index = 0

        try:

            for user in result:
                if not self.is_running():
                    break
                elif index < start:
                    index += 1
                else:
                    try:
                        self.handle_all_tweets(self.twitter.get_user_timeline(user.id_str))
                        time.sleep(timeout_in_sec)
                    except TwitterHTTPError as http_error:
                        self.logger.exception(http_error)
                        time.sleep(60)
                    except Exception as ex:
                        self.logger.exception(ex)

        except Exception as ex:
            self.logger.exception(ex)

        finally:
            session.close()

        self.thread = None
        self.logger.info('API Crawler ended.')
