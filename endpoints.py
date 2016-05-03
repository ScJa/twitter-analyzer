__author__ = 'Filip'

from urllib.parse import urlparse, parse_qs

from web import WebApp
from databases.neo4j import GraphDB


ENDPOINT = WebApp(__name__)
NEO4J = GraphDB()

# ednpoints for queries.html

@ENDPOINT.protected_route('/most_influential_persons')
def most_influential_persons():
    request = ENDPOINT.get_request()
    q = 'match(u:user) WHERE u.followers_count > %s AND u.tweets_favorite_count > %s AND u.tweets_retweet_count > %s ' \
        'return u.name, u.followers_count, u.tweets_retweet_count, u.tweets_favorite_count order by u.followers_count limit %s'
    results = NEO4J.query(q % (request.args['min_fol'], request.args['min_fav'], request.args['min_ret'], request.args['limit']))

    keys = ['u.name', 'u.tweets_favorite_count', 'u.tweets_retweet_count', 'u.followers_count']
    table = '''<table class="table tablesorter" id="resultTable">
            <thead><tr><th>Username</th><th>Favorites Count</th><th>Retweet Count</th><th>Folowers Count</th></tr></thead>
            <tbody>%s</tbody></table><script>$("#resultTable").tablesorter();</script>'''

    table_body = []
    for user in results.records:
        row = []
        for key in keys: row.append(user[key])
        table_body.append('<tr>'+''.join(['<td>%s</td>' % elem for elem in row])+'</tr>')

    return table % ('\n'.join(table_body))

def user_interests():

    url = '/user_interests?interest=Focused'
    url_query = parse_qs(urlparse(url).query, keep_blank_values=True)

    interest = 'Focused'
    limit = 10


    if interest == 'Focused':
        cql_query = 'match(u:user)-[r:mentions]->(t:topic_name) return u.name, t.name, sum(r.count), u.statuses_count' \
                    ' order by (sum(r.count)/u.statuses_count) desc  limit %s;'
        results = NEO4J.query(cql_query % str(limit))
    if interest == 'Broad':
        print()

    keys = ['u.name', 't.name']

    table = '''<table class="table tablesorter" id="resultTable">
            <thead> <tr> <th>username</th> <th>Focused on topic</th></tr> </thead>
            <tbody>%s</tbody></table><script>$("#resultTable").tablesorter();</script>'''

    table_body = []

    for topic in results.records:
        row = []
        for key in keys: row.append(topic[key])
        table_body.append('<tr>'+''.join(['<td>%s</td>' % elem for elem in row])+'</tr>')

    return table % ('\n'.join(table_body))

@ENDPOINT.protected_route('/suggests_based_existing')
def suggests_based_existing():
    url = '/suggests_based_existing?user_name=LamatthewsTony'
    url_query = parse_qs(urlparse(url).query, keep_blank_values=True)

    username = url_query['user_name'][0]
    limit = 10

    cql_query = 'match(u:user)-[r:mentions]->(t:topic_name) where u.name = \'%s\' return distinct t.name, r.count limit %s;';
    results = NEO4J.query(cql_query % (username, str(limit)))

    keys = ['t.name', 'r.count']
    table = '''<table class="table tablesorter" id="resultTable">
            <thead> <tr> <th>Topic name</th> <th>Mention count</th></tr> </thead>
            <tbody>%s</tbody></table><script>$("#resultTable").tablesorter();</script>'''

    table_body = []

    for topic in results.records:
        row = []
        for key in keys: row.append(topic[key])
        table_body.append('<tr>'+''.join(['<td>%s</td>' % elem for elem in row])+'</tr>')

    return table % ('\n'.join(table_body))

@ENDPOINT.protected_route('/suggests_based_potential')
def suggests_based_potential():
    url = '/suggests_based_potential?user_name=AyeMeng&relation=0'
    url_query = parse_qs(urlparse(url).query, keep_blank_values=True)

    username = url_query['user_name'][0]
    limit = 10

    cql_query = 'match(u1:user)-[r1:replies_to]->(u2:user), ' \
                '(u2:user)-[m2:mentions]->(t2:topic_name) ' \
                'where (m2.count>0) and u1<>u2 and u1.name = \'%s\' ' \
                'return distinct t2.name, sum(m2.count) as m_sum , count(m2) as m_count ' \
                'order by sum(m2.count) desc limit %s'

    results = NEO4J.query(cql_query % (username, str(limit)))

    keys = ['t2.name', 'm_sum', 'm_count']


    #TODO change the titles in table header
    table = '''<table class="table tablesorter" id="resultTable">
            <thead><tr> <th>Topic name</th> <th>Potential interest</th> <th>Potential interest</th> </tr></thead>
            <tbody>%s</tbody></table><script>$("#resultTable").tablesorter();</script>'''

    table_body = []
    for topic in results.records:
        row = []
        for key in keys: row.append(topic[key])
        table_body.append('<tr>'+''.join(['<td>%s</td>' % elem for elem in row])+'</tr>')

    return table % ('\n'.join(table_body))


if __name__ == '__main__':
    print(user_interests())

