#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging, json

from flask import request, abort, send_from_directory

from crawler.main import StreamCrawler, ApiCrawler
from common.constants import WEBAPP_PORT, WEBAPP_LOG_FILE, LOGLEVEL, LOGFORMAT
from common.constants import PG_DB, PG_HOST, PG_PWD, PG_USER,NEO4J_FRONTEND_URL
from common.constants import MONGO_DB, MONGO_HOST, MONGO_PWD, MONGO_USER, MONGO_FRONTEND_URL
from common.constants import NEO4J_HOST, NEO4J_PWD, NEO4J_USER
from databases.mongodb import MongoDB
from databases.postgres import PostgresDB
from analyzer.master import AnalyzerMaster
from web import WebApp
from databases.neo4j import GraphDB


logging.basicConfig(format=LOGFORMAT, filename=WEBAPP_LOG_FILE, level=LOGLEVEL, filemode="w+")
logging.getLogger().addHandler(logging.StreamHandler())

ENDPOINT = WebApp(__name__)
CRAWLER = {'stream': StreamCrawler(), 'api': ApiCrawler()}
MASTER = AnalyzerMaster()

NEO4J = GraphDB(user=NEO4J_USER, pwd=NEO4J_PWD, host=NEO4J_HOST)
POSTGRES = PostgresDB(PG_USER, PG_PWD, PG_DB, PG_HOST)
MONGO = MongoDB(MONGO_USER, MONGO_PWD, dbname=MONGO_DB, host=MONGO_HOST)

logging.getLogger('werkzeug').setLevel(logging.ERROR)      # Flask
logging.getLogger('httpstream').setLevel(logging.ERROR)    # Neo4J
logging.getLogger('py2neo.cypher').setLevel(logging.ERROR) # Neo4J

@ENDPOINT.errorhandler(500)
def page_not_found(e):
    ENDPOINT.logger.exception(e)
    return send_from_directory('web', 'error.html')

@ENDPOINT.route('/')
def index():
    return send_from_directory('web', 'index.html')

@ENDPOINT.route('/login.html')
def login():
    return send_from_directory('web', 'login.html')

@ENDPOINT.route('/logout')
def logout():
    ENDPOINT.logout()
    return send_from_directory('web', 'login.html')

@ENDPOINT.route('/auth', methods=['GET', 'POST'])
def auth():
    ENDPOINT.auth(request.values['user'], request.values['pwd'])
    return send_from_directory('web', 'index.html')

@ENDPOINT.route('/<name>.js')
def js(name):
    return send_from_directory('web', name+'.js')

@ENDPOINT.route('/<name>.css')
def css(name):
    return send_from_directory('web', name+'.css')

@ENDPOINT.route('/<name>.png')
def png(name):
    return send_from_directory('web', name+'.png')

@ENDPOINT.route('/<name>.gif')
def gif(name):
    return send_from_directory('web', name+'.gif')

@ENDPOINT.protected_route('/<name>.html')
def send_file(name):
    return send_from_directory('web', name+'.html')

@ENDPOINT.protected_route('/fonts/<name>')
def fonts(name):
    logging.getLogger('werkzeug').error('aaa: %s' % type(send_from_directory('web/fonts', name)))
    return send_from_directory('web/fonts', name)

@ENDPOINT.protected_route('/topics/add', methods=['POST'])
def topics_add():
    ENDPOINT.logger.info('Adding %s' % request.form['name'])
    database = MongoDB(MONGO_USER, MONGO_PWD, dbname=MONGO_DB, host=MONGO_HOST)
    result = database.add_advertisement(request.form['name'], request.form['keywords'].split('\n'), request.form['ad_text'])
    ENDPOINT.logger.info(result)
    return send_from_directory('web', 'index.html')

@ENDPOINT.protected_route('/topics/delete', methods=['POST'])
def topics_delete():
    # TODO
    return ''

@ENDPOINT.protected_route('/log')
def log():
    return send_from_directory('', WEBAPP_LOG_FILE)

@ENDPOINT.protected_route('/neo4j')
def neo4j():
    return '<iframe src="%s" style="width:100%%; min-height:800px"></iframe>' % NEO4J_FRONTEND_URL

@ENDPOINT.protected_route('/mongodb')
def mongodb():
    return '<iframe src="%s" style="width:100%%; min-height:800px"></iframe>' % MONGO_FRONTEND_URL

@ENDPOINT.protected_route('/databases/<name>')
def databases_details(name):
    if name == 'postgres':
        return json.dumps({'count': POSTGRES.get_user_count()})
    elif name == 'mongo':
        return json.dumps({'count': MONGO.get_document_count()})
    elif name == 'neo4j':
        return json.dumps({'count': NEO4J.get_user_count()})
    else:
        return '?'

@ENDPOINT.protected_route('/db_counts')
def databases_counts():
    return {'postgres': POSTGRES.get_user_count(),
            'mongo': MONGO.get_document_count(),
            'neo4j': NEO4J.get_user_count()}


def get_crawler(name):
    if name in CRAWLER:
        return CRAWLER[name]
    else:
        abort(401)

@ENDPOINT.protected_route('/crawler/status/<crawler>')
def crawler_status(crawler):
    crawler = get_crawler(crawler)
    time = crawler.time_last_tweet.isoformat() if crawler.time_last_tweet else None
    info = {'running': crawler.is_running(),
            'successful': crawler.count_inserted_success,
            'failed': crawler.count_inserted_failed, 'time': time,
            'rejected_lang': crawler.count_language_rejects}
    return json.dumps(info)

@ENDPOINT.protected_route('/crawler/toggle/<crawler>')
def crawler_toggle(crawler):
    return json.dumps({'running': get_crawler(crawler).toggle()})

@ENDPOINT.protected_route('/crawler/last_tweet/<crawler>')
def crawler_last_tweet(crawler):
    return json.dumps(get_crawler(crawler).last_tweet)

@ENDPOINT.protected_route('/crawler/db_info')
def crawler_db_info():
    return json.dumps(get_crawler('api').get_database_info())

@ENDPOINT.protected_route('/analyzer/toggle')
def analyzer_toggle():
    if MASTER.running:
        MASTER.stop()
    else:
        MASTER.start()
    return analyzer_status()

@ENDPOINT.protected_route('/analyzer/status')
def analyzer_status():
    status = {"running":MASTER.running}
    if MASTER.thread: status.update(MASTER.statistics.status)
    return json.dumps(status)


# ednpoints for queries.html

def make_table(header, keys, results):
    thead = '<tr style="cursor:pointer;">'+(''.join(['<th>%s</th>' % head for head in header]))+'</tr>'
    tbody = []
    for res in results:
        row = []
        for key in keys: row.append(res[key])
        tbody.append('<tr>'+''.join(['<td>%s</td>' % elem for elem in row])+'</tr>')
    tbody = ''.join(tbody)
    table = '<table id="resultTable" class="table tablesorter"><thead>%s</thead><tbody>%s</tbody></table>' % (thead, tbody)
    script = '<script>$("#resultTable").tablesorter();</script>'
    return table+script


# @ENDPOINT.protected_route('/list_users')
# def list_users():
#     request = ENDPOINT.get_request()
#     q = '''match(u:user) where  u.followers_count>0 and u.tweets_retweet_count>0 and u.tweets_favorite_count>0
#             return u.name, u.followers_count, u.tweets_retweet_count, u.tweets_favorite_count
#             order by u.followers_count limit %s'''
#     results = NEO4J.query(q % request.args['limit'])
#     header = ['Username', 'Favorites Count', 'Retweet Count', 'Followers Count']
#     keys = ['u.name', 'u.tweets_favorite_count', 'u.tweets_retweet_count', 'u.followers_count']
#     return make_table(header, keys, results)

@ENDPOINT.protected_route('/most_influential_persons')
def most_influential_persons():
    request = ENDPOINT.get_request()

    q = 'match(u:user) WHERE u.followers_count > %s AND u.tweets_favorite_count > %s AND u.tweets_retweet_count > %s ' \
        'return u.name, u.followers_count, u.tweets_retweet_count, u.tweets_favorite_count order by u.followers_count DESC limit %s'
    results = NEO4J.query(q % (request.args['min_fol'], request.args['min_fav'], request.args['min_ret'], request.args['limit']))

    keys = ['u.name', 'u.tweets_favorite_count', 'u.tweets_retweet_count', 'u.followers_count']
    header = ['Username', 'Favorites Count', 'Retweet Count', 'Followers Count']
    return make_table(header, keys, results)

@ENDPOINT.protected_route('/user_interests')
def user_interests():
    request = ENDPOINT.get_request()

    if request.args['interest'] == 'focused':
        # cql_query = 'MATCH (u:user)-[r:mentions]->(t:topic_name) ' \
        #             'WITH (toFloat(sum(r.count))/ toFloat(u.statuses_count)) AS metric, u, r, t '\
        #             'WHERE metric>0 '\
        #             'RETURN u.name, sum(r.count), u.statuses_count,  metric, COUNT(DISTINCT t.name) AS topic_count ' \
        #             'ORDER BY metric DESC, topic_count ASC LIMIT %s;'
        cql_query = 'MATCH (u:user)-[r:mentions]->(t:topic_name) ' \
                    'WITH (toFloat(sum(r.count))/ toFloat(u.statuses_count)) AS metric, u.name AS name, ' \
                    'sum(r.count) AS mentions_count, u.statuses_count AS tweets, COUNT(DISTINCT t.name) AS topic_count '\
                    'WHERE metric>0 '\
                    'RETURN name, mentions_count, tweets, metric, topic_count ' \
                    'ORDER BY metric DESC, topic_count DESC LIMIT %s;'
        keys = ['name', 'mentions_count', 'tweets', 'metric', 'topic_count']
        header = ['Username', 'Mentions', 'Tweets', 'Metric', 'Topics']

    elif request.args['interest'] == 'broad':
        cql_query = 'MATCH (u:user)-[r:mentions]->(t:topic_name) ' \
                    'WITH (toFloat(sum(r.count))/ toFloat(u.statuses_count)) AS metric, u.name AS name, ' \
                    'sum(r.count) AS mentions_count, u.statuses_count AS tweets, COUNT(DISTINCT t.name) AS topic_count '\
                    'WHERE metric>0 '\
                    'RETURN name, mentions_count, tweets, metric, topic_count ' \
                    'ORDER BY topic_count DESC, metric ASC LIMIT %s;'
        keys = ['name', 'mentions_count', 'tweets', 'metric', 'topic_count']
        header = ['Username', 'Mentions', 'Tweets', 'Metric', 'Topics']

    else:
        return send_from_directory('web', 'error.html')


    results = NEO4J.query(cql_query % request.args['limit']).records
    return make_table(header, keys, results)

def make_topic_panel(topic, text):
    return '''<div class="panel panel-default panel-success"><div class="panel-heading">Ad for Topic: %s</div>
            <div class="panel-body">%s</div></div>''' % (topic, text)

@ENDPOINT.protected_route('/suggests_based_existing')
def suggests_based_existing():
    request = ENDPOINT.get_request()
    username = request.args['user_name']
    limit = request.args['limit']

    if len(username) > 0: username = 'where u.name = "%s"' % username

    cql_query = '''match(u:user)-[r:mentions]->(t:topic_name) %s return
        distinct u.name, t.name, r.count order by r.count desc limit %s;'''

    results = NEO4J.query(cql_query % (username, limit))
    keys = ['u.name', 't.name', 'r.count']
    header = ['User', 'Topic', 'Mentions Count']
    table = make_table(header, keys, results)

    ads = []
    for result in results:
        topic = result['t.name']
        ads.append(make_topic_panel(topic, MONGO.get_random_advertisment(topic)))
    return '%s<hr>%s' % (table, ''.join(ads))


@ENDPOINT.protected_route('/suggests_based_potential')
def suggests_based_potential():
    request = ENDPOINT.get_request()
    username = request.args['user_name']
    relation = request.args['relation']
    limit = request.args['limit']

    if len(username) > 0: username = 'and u1.name = "%s"' % username

    cql_query = 'match(u1:user)-[r1:%s]->(u2:user), ' \
                '(u2:user)-[m2:mentions]->(t2:topic_name) ' \
                'where (m2.count>0) and u1<>u2 %s ' \
                'return distinct u1.name, t2.name, sum(m2.count) as m_sum, count(u2.name) AS u_count ' \
                'order by m_sum desc limit %s'

    #AyeMeng
    results = NEO4J.query(cql_query % (relation, username, limit))
    keys = ['u1.name', 't2.name', 'm_sum', 'u_count']
    header = ['User', 'Topic', 'x Times Mentioned', 'Mentioned by x Users']
    table =  make_table(header, keys, results)

    ads = []
    for result in results:
        topic = result['t2.name']
        ads.append(make_topic_panel(topic, MONGO.get_random_advertisment(topic)))
    return '%s<hr>%s' % (table, ''.join(ads))


@ENDPOINT.protected_route('/quick_search')
def quick_search():
    name = ENDPOINT.get_request().args['name']
    if len(name) > 3:
        return make_table(['Quick-Search Suggestions'], ['screen_name'], POSTGRES.quicksearch(name))
        #return make_table(['Quick-Search Suggestions'], ['u.name'], NEO4J.quicksearch(name))
    else:
        return ''





if __name__ == '__main__':
    ENDPOINT.logger.info('Starting Flask endpoint for webapp.')
    ENDPOINT.run(host='0.0.0.0', port=WEBAPP_PORT)


#Fitness 4264 ---- 15,776266416510318949343339587242
#Books 3578 ---- 18,801006148686416992733370598099
#Beauty 3311 ---- 20,317124735729386892177589852008
#Fashion 1099 ---- 61,210191082802547770700636942675
#Car 67270 ---- 1
#Food 1606 ---- 41,886674968866749688667496886675
#Movies 3034 ---- 22,172050098879367172050098879367
#Computer 7915 ---- 8,4990524320909665192672141503474

#die werte dynamisch ausrechnen mit "match(u:user)-[r:mentions]->(t:topic_name) return t,count(r)"
#alles durch car dividieren