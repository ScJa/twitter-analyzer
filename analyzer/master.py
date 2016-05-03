import time
import logging
import threading
import os
from multiprocessing import Process, Queue

from databases.mongodb import MongoDB
from common.constants import MONGO_USER, MONGO_PWD, MONGO_DB, MONGO_HOST
from . import slave, topics, modes
from .statistics import Statistics


class AnalyzerMaster():
    def __init__(self, slave_count = 6):
        self.logger = logging.getLogger("analyzer.master")
        self.slave_count = slave_count
        self.thread = None
        self.running = False

        # to be set by clients
        self.mode = modes.DefaultMode()
        self.single = False

    def start(self):
        self.logger.info("Initializing analyzer ...")
        self.queue = Queue(100)
        self.stat_queue = Queue(100)
        self.statistics = Statistics(self.stat_queue)

        self.logger.debug("Creating %d slaves", self.slave_count)
        self.slaves = [self.__create_slave(i) for i in range(self.slave_count)]

        self.logger.debug("Connecting to MongoDB")
        self.mongo = MongoDB(user=MONGO_USER, pwd=MONGO_PWD, dbname=MONGO_DB, host=MONGO_HOST)


        self.logger.debug("Loading topics  ...")
        topics.load_topics(self.mongo)
        self.logger.debug("Loaded %d topics.", len(topics.TOPICS))

        self.thread = threading.Thread(target=self.run)
        self.running = True
        self.thread.start()

        self.statistics.start()

        self.logger.info("Analyzer initialization complete.")

    def run(self):
        self.logger.info("Starting analyzer with PID %d", os.getpid())
        self.__start_slaves()

        while self.running:
            try:
                self.logger.info("Starting tweet analysis ...")
                self.__run()
                if self.single:
                    self.running = False
                    self.logger.info("Analyzed all remaining tweets. Done.")
                else:
                    self.logger.info("Analyzed all remaining tweets. Sleeping for a while ...")

            except KeyboardInterrupt:
                self.logger.warning("Interrupted, exiting.")
                self.running = False

            except:
                self.logger.error("Exception in the master, retrying in a few seconds.", exc_info = True)
                time.sleep(5)

        self.statistics.stop()

        self.logger.info("Waiting for slaves to terminate ...")
        self.__join_slaves()
        self.logger.info("Analysis has ended.")

    def __run(self):
        tweets = self.mode.query(self.mongo)

        for tweet in tweets:
            # send tweet to slaves
            self.queue.put(tweet)
            time.sleep(0.01)
            if not self.running:
                break

    def stop(self):
        self.running = False
        self.statistics.stop()

    def __create_slave(self, index):
        name = "analyzer.slave-%d" % index
        return Process(target = slave.run, args=[self.queue, name, self.stat_queue, self.mode], name=name)

    def __start_slaves(self):
        self.logger.info("Starting %d analyzer slaves ...", len(self.slaves))

        for slave in self.slaves:
            slave.start()

    def __join_slaves(self):
        self.queue.close()
        for slave in self.slaves:
            slave.join()
