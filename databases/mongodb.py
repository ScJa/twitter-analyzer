# -*- coding: utf-8 -*-

import logging, pymongo, random


class MongoDB():

    def __init__(self, user, pwd, dbname='local', host='127.0.0.1'):
        self.logger = logging.getLogger(MongoDB.__name__)
        self.client = pymongo.MongoClient(host)
        self.tweet_collection = self.client[dbname]['aic_project']
        self.ads_collection = self.client[dbname]['aic_project_ads']

    def add_tweet(self, tweet):
        if not self.has_tweet(tweet['tweet']['id_str']):
            self.tweet_collection.insert_one(dict(tweet.items()))

    def get_tweet(self, tweet_id_str):
        return self.tweet_collection.find_one({'tweet.id_str': tweet_id_str})

    def has_tweet(self, tweet_id_str):
        return not self.get_tweet(tweet_id_str=tweet_id_str) is None

    def get_tweets(self, **kwargs):
        return self.tweet_collection.find(kwargs)

    def count_tweets(self, **kwargs):
        return self.tweet_collection.count(kwargs)

    def update_tweet(self, query, update):
        return self.tweet_collection.update(query, update)

    def add_advertisement(self, name, keywords, ad_text):
        """
        @:param ad_text can be a single string or a list of strings
        """
        name = name.strip()
        if type(keywords) in [list, set]:
            keywords = [element.strip() for element in keywords if len(element)>0]
        else:
            keywords = [keywords.strip()]

        if type(ad_text) in [list, set]:
            ad_text = [element.strip() for element in ad_text if len(element)>0]
        else:
            ad_text = [ad_text.strip()]

        ad = self.get_advertisement(name=name)
        if ad is None:
            return self.ads_collection.insert_one(dict(name=name, keywords=keywords, advertisements=[ad_text]))
        else:
            ad['keywords'].extend([kw for kw in keywords if not kw in ad['keywords']])
            if type(ad_text) == str: ad_text = [ad_text]
            ad['advertisements'].extend([text for text in ad_text if not text in ad['advertisements']])
            return self.ads_collection.update({'name': name}, ad)

    def get_all_advertisements(self):
        return self.ads_collection.find()

    def get_advertisement(self, **kwargs):
        return self.ads_collection.find_one(kwargs)

    def has_advertisement(self, **kwargs):
        return not self.ads_collection(**kwargs) is None

    def get_document_count(self):
        return {'tweets': self.tweet_collection.count(), 'ads': self.ads_collection.count()}

    def get_random_advertisment(self, topic):
        ad = self.get_advertisement(name=topic)
        if ad is None or len(ad['advertisements']) == 0: return ''
        advertisements = ad['advertisements'][0]
        if len(advertisements) == 0: return ''
        index = random.randint(0, len(advertisements)-1)
        return advertisements[index]

"""
For later:  set all tweets to 'not processed by analyzer':

db.aic_project.update({ "analyzer.processed": true }, { "$set": { "analyzer.processed": false } }, { multi: true })

db.aic_project.update({ "analyzer.processed": true }, { "$set": { "analyzer.retweets_favorites": null } }, { multi: true })
"""

