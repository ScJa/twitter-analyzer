# -*- coding: utf-8 -*-
from py2neo import Graph, Node, Relationship
from common.constants import NEO4J_HOST, NEO4J_PWD, NEO4J_USER

class GraphDB():

    def __init__(self, user=NEO4J_USER, pwd=NEO4J_PWD, host=NEO4J_HOST):
        self.graph = Graph("http://%s:%s@%s/db/data/" % (user, pwd, host))

    def query(self, query_str, stream=False):
        if stream:
            return self.graph.cypher.stream(query_str)
        else:
            return self.graph.cypher.execute(query_str)

    def create_relation_user_to_topic(self, user, relation, topic_name):
        userNode = self.graph.find_one("user", 'id', user.id_str)
        if not userNode:
            userNode = self.create_node_from_user(user)
            self.graph.create(userNode)

        topicNode = self.graph.find_one("topic_name", 'name', topic_name)
        if not topicNode:
            topicNode = Node("topic_name", name = topic_name)
            self.graph.create(topicNode)

        relationship = self.graph.match_one(userNode, relation, topicNode)
        if not relationship:
            relationship = Relationship(userNode, relation, topicNode, count = 1)
            self.graph.create(relationship)
        else:
            relationship.properties['count'] += 1
            relationship.push()

    # Relations: follows eventuell favourites, retweets

    def create_relation_user_to_user(self, userA, relation, userB):
        userANode = self.graph.find_one("user", 'id', userA.id_str)
        userBNode = self.graph.find_one("user", 'id', userB.id_str)

        if not userANode:
            userANode = self.create_node_from_user(userA)
            self.graph.create(userANode)

        if not userBNode:
            userBNode = self.create_node_from_user(userB)
            self.graph.create(userBNode)

        relationship = self.graph.match_one(userANode, relation, userBNode)
        if not relationship:
            relationship = Relationship(userANode, relation, userBNode, count = 1)
            self.graph.create(relationship)
        else:
            relationship.properties['count'] += 1
            relationship.push()

    def increment_user_counter(self, user, counter, n):
        userNode = self.graph.find_one("user", 'id', user.id_str)
        if not userNode:
            userNode = self.create_node_from_user(user)
            self.graph.create(userNode)

        if counter in userNode.properties:
            userNode.properties[counter] += n
        else:
            userNode.properties[counter] = n
        userNode.push()

    def get_all_users(self):
        users = []
        for u in self.graph.find('user'):
            users.append({'name': u.properties['screen_name'], 'id_str': u.properties['id']})
        return users

    def create_node_from_user(self, user):
        userNode = Node("user", name=user.screen_name, id=user.id_str, followers_count=user.followers_count,
            friends_count=user.friends_count, statuses_count=user.statuses_count, favourites_count=user.favourites_count)
        return userNode

    def quicksearch(self, username, limit=10):
        cql_query = "match(u:user) WHERE u.name =~ '%s.*' RETURN DISTINCT u.name LIMIT %s;"
        return self.query(cql_query % (username, limit))

    def get_user_count(self):
        cql_query = "match(u:user) RETURN count(DISTINCT u) AS c;"
        for row in self.query(cql_query):
            return row['c']
        return 0


