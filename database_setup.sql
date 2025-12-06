-- PostgreSQL Database Setup için SQL komutları

CREATE USER hive_user WITH PASSWORD 'hive_password';

CREATE DATABASE hive_db;

GRANT ALL PRIVILEGES ON DATABASE hive_db TO hive_user;

ALTER USER hive_user CREATEDB;

-- TablePlus Connection Settings:
-- Host: localhost
-- Port: 5432
-- Database: hive_db
-- Username: hive_user
-- Password: hive_password