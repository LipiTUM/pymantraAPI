# pymantradb-api

## Build

Clone the repository `git clone https://github.com/LipiTUM/pymantraAPI.git`.

To build the application, copy `.env.template` to `.env` and execute
`docker compose up --build -d`.

The API is available as `http://localhost:8084`. The port can be adpated in the
`.env` file.

### Production build

To create a production build of the application, in the `.env` file, set the
DJANGO_DEBUG variable to 0, generate a secure password for the
DJANGO_SECRET_KEY and database passwords.

To create a secure build of the application, please adapt the following
variables in the `.env` file:

* DJANGO_DEBUG (set to 0)
* DJANGO_SECRET_KEY
* DJANGO_ADMIN_USER
* DJANGO_ADMIN_PASSWORD
* NEO4J_USER
* NEO4J_PASSWORD
* SQL_PASSWORD

If the default main port (`NGINX_PORT`) 8084 is taken on your system, you will
also need to change it.

Further, you should remove the neo4j ports in the `docker-compose.yml` file,
since this exposes the neo4j database.

If you plan to make the API reachable for users outside, we also encourage to
set limits on `NGINX_MAX_BODY_SIZE`.


### Use database dumps

The neo4j database is initialized from a dump, which may take some time to load.
The database images can also start of a previously dumped state.

#### Neo4j

To use your own Neo4j database dumps you can mount them to the directory
`/dumps` as .dump file generated with `neo4j-admin`. Currently, the dump format
needs to be compatible with neo4j version 4.4.11.

