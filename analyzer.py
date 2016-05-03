#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry program for the Analyzer
"""
import logging, json, flask, os

from analyzer.master import AnalyzerMaster
from analyzer import modes
from common.constants import ANALYZER_PORT, ANALYZER_LOG_FILE

logging.basicConfig(format="%(levelname) 7s:%(name) 18s: %(message)s", filename=ANALYZER_LOG_FILE, level=logging.INFO, filemode="w+")
logging.getLogger('werkzeug').setLevel(logging.ERROR)      # Flask
logging.getLogger('httpstream').setLevel(logging.ERROR)    # Neo4J
logging.getLogger('py2neo.cypher').setLevel(logging.ERROR) # Neo4J

MASTER = AnalyzerMaster()
ENDPOINT = flask.Flask('analyzer')


@ENDPOINT.route('/')
def index():
    path = os.path.join('analyzer', 'index.html')
    with open(path, 'r') as f:
        return flask.render_template_string(f.read())

@ENDPOINT.route('/status')
def status():
    return json.dumps(MASTER.statistics.status)

@ENDPOINT.route('/log')
def log():
    with open(ANALYZER_LOG_FILE, 'r') as f:
        return f.read()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode")
    parser.add_argument("--single", action='store_true')
    parser.add_argument("--slaves", type=int)
    args = parser.parse_args()

    if args.mode:
        MASTER.mode = modes.get(args.mode)
    if args.single:
        MASTER.single = True
    if args.slaves:
        MASTER.slave_count = args.slaves

    MASTER.start()

    ENDPOINT.logger.info('Starting Flask endpoint for analyzer.')
    ENDPOINT.run(host='0.0.0.0', port=ANALYZER_PORT)
