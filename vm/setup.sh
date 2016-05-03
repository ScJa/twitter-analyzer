#!/bin/bash


## MongoDB
# adapted from: http://thejackalofjavascript.com/vagrant-mean-box/

apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | tee /etc/apt/sources.list.d/mongodb.list
apt-get update
apt-get install -y mongodb-org

# Edit mongod.conf to listen on all interfaces
sed -i "s/bind_ip = 127.0.0.1/bind_ip = 0.0.0.0/" /etc/mongod.conf
service mongod restart

## PostgreSQL
# adapted from: https://github.com/jackdb/pg-app-dev-vm/blob/master/Vagrant-setup/bootstrap.sh

APP_DB_USER=aic
APP_DB_PASS=$APP_DB_USER
APP_DB_NAME=$APP_DB_USER

PG_VERSION=9.3

apt-get update
#apt-get -y upgrade

apt-get -y install "postgresql-$PG_VERSION" "postgresql-contrib-$PG_VERSION"

PG_CONF="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
PG_DIR="/var/lib/postgresql/$PG_VERSION/main"

# Edit postgresql.conf to change listen address to '*':
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"

# Append to pg_hba.conf to add password auth:
echo "host    all             all             all                     md5" >> "$PG_HBA"

# Explicitly set default client_encoding
echo "client_encoding = utf8" >> "$PG_CONF"

# Restart so that all new config is loaded:
service postgresql restart

cat << EOF | su - postgres -c psql
-- Create the database user:
CREATE USER $APP_DB_USER WITH PASSWORD '$APP_DB_PASS';

-- Create the database:
CREATE DATABASE $APP_DB_NAME WITH OWNER = $APP_DB_USER;
EOF

## Neo4J


#!/bin/bash

echo
echo "Installing Java..."
cd /usr/local
wget -nv -O jre-7u45-linux-x64.gz http://javadl.sun.com/webapps/download/AutoDL?BundleId=81812
tar -xf jre-7u45-linux-x64.gz
rm jre-7u45-linux-x64.gz
ln -s /usr/local/jre1.7.0_45/bin/java /usr/bin/java

echo
echo "Installing Neo4j..."
cd /etc
wget -nv http://dist.neo4j.org/neo4j-community-2.2.5-unix.tar.gz
tar -xf neo4j-community-2.2.5-unix.tar.gz
rm neo4j-community-2.2.5-unix.tar.gz
ln -s /etc/neo4j-community-2.2.5/bin/neo4j /usr/bin/neo4j

echo
echo "Updating Neo4j Config..."
sed -i 's/#org\.neo4j\.server\.webserver\.address=0\.0\.0\.0/org.neo4j.server.webserver.address=0.0.0.0/' /etc/neo4j-community-2.2.5/conf/neo4j-server.properties

echo
echo "Starting Neo4j..."
#neo4j start



# Rest
apt-get -y install git python3
