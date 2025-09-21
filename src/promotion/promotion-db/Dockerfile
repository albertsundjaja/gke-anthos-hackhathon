FROM postgres:16.6-alpine@sha256:56e87f5517713be839c1ce724ec275cb46579fb05edbb0887f26f60faebe7f0d

# Files for initializing the database.
COPY initdb/0-promotion-schema.sql /docker-entrypoint-initdb.d/
RUN chmod 755 /docker-entrypoint-initdb.d/0-promotion-schema.sql