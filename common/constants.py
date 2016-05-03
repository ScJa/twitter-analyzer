# -*- coding: utf-8 -*-
LOGLEVEL = 'INFO'
LOGFORMAT = "%(levelname) 7s:%(name) 18s: %(message)s"

TWITTER_TOKEN = 'insert here'
TWITTER_TOKEN_SECRET = 'insert here'
TWITTER_CONSUMER_KEY = 'insert here'
TWITTER_CONSUMER_SECRET = 'insert here'

HOST = 'insert here'

PG_USER = 'aic'
PG_PWD = 'aic_g1t4'
PG_DB = 'aic_project'
PG_HOST = HOST

MONGO_USER = 'aic'
MONGO_PWD = 'aic_g1t4'
MONGO_DB = 'local'
MONGO_HOST = HOST
MONGO_FRONTEND_URL = 'http://'+HOST+':5005'

NEO4J_USER = 'neo4j'
NEO4J_PWD = 'aic_g1t4'
NEO4J_HOST = HOST+':7474'
NEO4J_FRONTEND_URL = 'http://'+HOST+':7474/browser'

TWITTER_CRAWLER_ACCEPTED_LANGS = ['en']

#RPM = requests per minute
TWITTER_CRAWLER_TIMELINE_RPM = 180 / 15     # 180 requests in 15 minutes

ANALYZER_PORT = 5003
ANALYZER_LOG_FILE = 'analyzer.log'

WEBAPP_PORT = 5000
WEBAPP_LOG_FILE = 'webapp.log'
WEBAPP_USER = 'aic'
WEBAPP_PWD = 'aic_g1t4'
