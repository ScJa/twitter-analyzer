#Twitter Analyzer

##Authors: Belk Stefan, Falb Klaus, Causevic Amra, Rydzi Filip, Schneider Jakob

Relational Database: PostgreSQL

Document Store: MongoDB

Graph Database: Neo4j

Programming Language: Python 3

Interface: HTML, JavaScript

## Dependencies:
Linux Packages: python3 python3-pip postgresql postgresql-contrib postgresql-server-dev-all mongodb-org

Python Packages: twitter pymongo sqlalchemy psycopg2

## How to install:
1. sudo apt-get install python3 python3-pip postgresql postgresql-contrib postgresql-server-dev-all mongodb-org
2. sudo pip3 install twitter pymongo sqlalchemy psycopg2
3. connect to postgres database and create a new user "aic" and a new database "aic_project" (change the config.py if you use other names and passwords)
4. execute "create_table.sql" from the project folder to create the twitter_userdata table
5. [optional] install a web frontent for mongodb (e.g.rockmongo) and enter its url and port into the config.py 
6. [optional] create the local databases aic_project and aic_project_ads in your mongodb (or otherwise they will be automatically created on data insertion)
7. [optional] create indices in your mongodb on tweet.id_str and analyzer.processed for the aic_project database
8. install neo4j as stated at http://neo4j.com/download-thanks-beta/?edition=community&release=3.0.0-M02&flavour=unix&_ga=1.48996326.1333989759.1454166537

## How to run:
1. go into the project folder and execute "python3 web.py" (this call will block your terminal)
2. open your browser and go to "http://localhost:5000" (change config.py before startup for another port)
3. you will have to log in the first time you visit the page (change config.py for other login credentials)
4. go to the crawler and analyzer tabs to run crawler and analyzer threads
5. go to the queries tab to execute queries against the graph database

