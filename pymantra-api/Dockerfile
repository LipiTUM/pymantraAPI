FROM python:3.10

# clone and prepare the pymantra-package repository
COPY patches patches
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install pipeline and docker-entrypoint dependencies
RUN apt-get update && apt-get install -y \
 netcat-openbsd \
 sqlite3

# install virtual environment to /opt/venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


# install python project dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# TODO: change to pip install pymantra once implemented properly
# install the pymantra-package from the cloned git repository
RUN pip install pymantra

# bundle app source
COPY . .

# prepare the start command
EXPOSE 80
RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
