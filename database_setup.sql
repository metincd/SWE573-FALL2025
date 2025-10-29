-- PostgreSQL Database Setup için SQL komutları
-- Bu komutları TablePlus'ta ya da psql terminalinde çalıştırın

-- 1. Veritabanı kullanıcısı oluştur
CREATE USER hive_user WITH PASSWORD 'hive_password';

-- 2. Veritabanı oluştur
CREATE DATABASE hive_db;

-- 3. Kullanıcıya veritabanı üzerinde tam yetki ver
GRANT ALL PRIVILEGES ON DATABASE hive_db TO hive_user;

-- 4. Kullanıcının veritabanı oluşturma yetkisi (migration'lar için gerekli)
ALTER USER hive_user CREATEDB;

-- TablePlus Connection Settings:
-- Host: localhost
-- Port: 5432
-- Database: hive_db
-- Username: hive_user
-- Password: hive_password