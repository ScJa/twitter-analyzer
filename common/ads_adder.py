import json

from databases.mongodb import MongoDB

if __name__ == '__main__':
    from common.constants import MONGO_DB, MONGO_HOST, MONGO_PWD, MONGO_USER
    db = MongoDB(MONGO_USER, MONGO_PWD, dbname=MONGO_DB, host=MONGO_HOST)

    with open('../doc/ads_json/topic_car.json') as data_file:
        data = json.load(data_file)
        db.add_advertisement(data["name"], data["keywords"], data["advertisements"])
