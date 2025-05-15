FROM postgres:16

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=admin
ENV POSTGRES_DB=flats_db

COPY init.sql /docker-entrypoint-initdb.d/