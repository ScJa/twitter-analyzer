# -*- coding: utf-8 -*-

import logging, threading
from twitter import Twitter, OAuth, TwitterStream
from common.constants import LOGLEVEL
from common.constants import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_TOKEN, TWITTER_TOKEN_SECRET
from twitter.api import TwitterDictResponse, TwitterListResponse

"""
Stefan: Twitter needs OAuth authentification. The credentials below are from a dummy account.
"""

def print_tweets(elem, level=0):
    tabs = ''.join(['\t']*level)
    if type(elem) == TwitterListResponse or type(elem) == list:
        for e in elem:
            if type(elem) in [TwitterListResponse, list, dict, TwitterDictResponse]:
                print_tweets(e, level+1)
            else:
                print('%s%s' % (tabs, elem))
    elif type(elem) == TwitterDictResponse or type(elem) == dict:
        for key, value in elem.items():
            if type(value) in [TwitterListResponse, list, dict, TwitterDictResponse]:
                print("%s%s:" % (tabs, key))
                print_tweets(value, level+1)
            else:
                print('%s%s: %s' % (tabs, key, value))

class TwitterSearchApi():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LOGLEVEL)
        auth = OAuth(TWITTER_TOKEN, TWITTER_TOKEN_SECRET, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        self.twitter = Twitter(auth=auth)

    def search(self, query, count=100, result_type='recent', lang='en', **kwargs):
        """
        :param query: The query string.
        :param kwargs: Optional parameter dictionary.
        :return: The API response as JSON
        """
        search_params = {'q': query, 'count': count, 'result_type': result_type, 'lang': lang}
        search_params.update(kwargs)
        self.logger.debug('Twitter API search: %s' % search_params)
        return self.twitter.search.tweets(**search_params)

    def get_user_timeline(self, user_id, count=200):
        if count > 200:
            self.logger.warn('Count > 200. The API returns at maximum 200 tweets per timeline request!')
        return self.twitter.statuses.user_timeline(user_id=user_id, count=count)

    def lookup_users(self, **kwargs):
        """
        :param kwargs:
        :return: List of user objects
         lookup supports a list of up to 100 users (user_id) as input
         only 60 requests per 15 minutes
        """
        return self.twitter.users.lookup(**kwargs)


class TwitterStreamingApi():

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LOGLEVEL)
        auth = OAuth(TWITTER_TOKEN, TWITTER_TOKEN_SECRET, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        self.stream = TwitterStream(auth=auth, domain='stream.twitter.com')
        self.stream_thread = None
        self.stream_listeners = dict()

        if Twitter(auth=auth).account.verify_credentials():
            self.logger.info('Successfully connected to twitter.')
        else:
            raise Exception('Could not connect to twitter!')

    def stop_stream(self):
        self.stream_thread = None

    def start_stream(self):
        if self.stream_thread is None:
            self.stream_thread = threading.Thread(target=self.run)
            self.stream_thread.start()

    def is_stream_running(self):
        return self.stream_thread is not None

    def add_stream_listener(self, listener, callback):
        self.stream_listeners[listener] = callback

    def call_handle_stream_data(self, tweet):
        for listener, callback in self.stream_listeners.items():
            try:
                callback(tweet)
            except Exception as ex:
                self.logger.error(ex)

    def run(self):
        self.logger.info('Twitter thread started.')
        try:

            for tweet in self.stream.statuses.sample():
                if self.stream_thread is None:
                    self.logger.info('Twitter thread stopped by user.')
                    break
                elif 'hangup' in tweet and tweet['hangup']:
                    self.logger.error('Twitter stream closed by remote end!')
                    break
                elif 'timeout' in tweet and tweet['timeout']:
                    self.logger.error('Twitter stream timed out!')
                    break
                elif len(self.stream_listeners) == 0:
                    self.logger.info('Twitter thread stopped. No listeners.')
                    break
                else:
                    self.call_handle_stream_data(tweet)

        except Exception as ex:
            self.logger.error(ex)

        self.stream_thread = None
