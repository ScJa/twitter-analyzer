
class Mode():
    def query(self, mongo):
        raise NotImplemented

    def _get_tweets(self, mongo, conditions):
        return mongo.get_tweets(**conditions)

    def analyze(self, tweet):
        raise NotImplemented

class DefaultMode(Mode):
    def query(self, mongo):
        return self._get_tweets(mongo, { 'analyzer.processed': False })

    def analyze(self, tweet):
        tweet.analyze_topics()
        tweet.analyze_relations()
        tweet.analyze_retweets()
        tweet.analyze_favorites()


class RetweetsFavoritesMode(Mode):
    def query(self, mongo):
        return self._get_tweets(mongo, {
            '$and': [
                {'analyzer.processed': True},
                {'analyzer.retweets_favorites': None},
                {'$or': [
                    {'tweet.retweet_count': { '$gt': 0 }},
                    {'tweet.favourites_count': { '$gt': 0 }}
                ]}
            ]
        })

    def analyze(self, tweet):
        tweet.analyze_retweets()
        tweet.analyze_favorites()


def get(name):
    if not name or name == 'default':
        return DefaultMode()
    elif name == 'retweets_favorites':
        return RetweetsFavoritesMode()
