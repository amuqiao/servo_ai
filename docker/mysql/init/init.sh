#!/bin/bash
set -e

mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <<-EOSQL
    CREATE DATABASE IF NOT EXISTS \`$MYSQL_DATABASE\`;
    USE \`$MYSQL_DATABASE\`;
    $(cat /docker-entrypoint-initdb.d/init.sql)
EOSQL