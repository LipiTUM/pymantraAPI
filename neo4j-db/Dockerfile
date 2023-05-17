FROM neo4j:4.4.11

WORKDIR /startup

# Install patch
RUN apt-get update && apt-get install -y \
	patch python3 python3-pip

COPY patches patches
COPY dumps /dumps

RUN patch docker-entrypoint.sh patches/database_init_4_4_11.patch

RUN pip install gdown
RUN gdown --folder https://drive.google.com/drive/folders/1YnW3etEWtai4nU2DKBwjVYCPkghn1FxR?usp=share_link
RUN mv API/neo4j.dump /dumps/neo4j.dump

RUN echo $(ls -l /dumps/*.dump)

EXPOSE 7474 7687

ENTRYPOINT ["tini", "-g", "--", "/startup/docker-entrypoint.sh"]
CMD ["neo4j"]
