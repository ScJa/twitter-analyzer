# -*- coding: utf-8 -*-
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

Base = declarative_base()
class Userdata(Base):
    """
    Maps to the table users in the postgres db.
    """
    __tablename__ = 'twitter_userdata'
    id_str = Column(String, primary_key=True)
    screen_name = Column(String)
    followers_count = Column(Integer)
    friends_count = Column(Integer)
    statuses_count = Column(Integer)
    favourites_count = Column(Integer)

    def __str__(self):
        return "@{}({})".format(self.screen_name, self.id_str)


class PostgresDB():

    def __init__(self, user, pwd, dbname, host='127.0.0.1'):
        self.logger = logging.getLogger(PostgresDB.__name__)
        self.engine = create_engine('postgresql://%s:%s@%s/%s' % (user, pwd, host, dbname), echo=False)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Provide a transactional scope around a series of operations."""
        return self.Session()

    def insert_or_update_user(self, id_str, **other_user_data):
        if self.has_user(id_str):
            self.update_user(id_str, **other_user_data)
        else:
            self.insert_user(id_str, **other_user_data)

    def update_user(self, id_str, **other_user_data):
        session = self.get_session()
        try:
            update(Userdata).where(Userdata.id_str == id_str).values(**other_user_data)
            session.commit()
        except Exception as ex:
            self.logger.exception(ex)
            session.rollback()
        finally:
            session.close()

    def insert_user(self, id_str, **other_user_data):
        session = self.get_session()
        try:
            session.add(Userdata(id_str=id_str, **other_user_data))
            session.commit()
        except Exception as ex:
            self.logger.exception(ex)
            session.rollback()
        finally:
            session.close()

    def get_user(self, id_str):
        session = self.get_session()
        try:
            return session.query(Userdata).filter(Userdata.id_str == id_str).one()
        except Exception as ex:
            return None
        finally:
            session.close()

    def get_user_by_screen_name(self, screen_name):
        session = self.get_session()
        try:
            return session.query(Userdata).filter(Userdata.screen_name == screen_name).one()
        except Exception as ex:
            return None
        finally:
            session.close()

    def get_all_users(self):
        session = self.get_session()
        return session, session.query(Userdata).yield_per(1000)

    def get_user_count(self):
        session = self.get_session()
        count = 0
        try:
            count = session.query(Userdata.id_str).count()
        except Exception as ex:
            self.logger.exception(ex)
        finally:
            session.close()
        return count

    def get_users_with_followers(self, min_count, result_limit=None):
        session = self.get_session()
        try:
            query = session.query(Userdata).filter(Userdata.followers_count >= min_count)
            if result_limit: query = query.limit(result_limit)
            return query.all()
        except Exception as ex:
            self.logger.exception(ex)
        finally:
            session.close()

    def has_user(self, id_str):
        return not self.get_user(id_str) is None

    def quicksearch(self, username, limit=10):
        sql = "SELECT DISTINCT screen_name FROM twitter_userdata WHERE screen_name LIKE :name LIMIT :limit"
        return [row for row in self.engine.execute(text(sql), name=('%s%%' % username), limit=limit)]