#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER etl_user WITH PASSWORD 'changeme';
    CREATE DATABASE dummyjson_etl OWNER etl_user;
EOSQL