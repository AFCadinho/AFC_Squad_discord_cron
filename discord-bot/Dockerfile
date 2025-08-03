FROM python:3.11-slim-bullseye

WORKDIR /app

RUN pip install poetry

RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y fonts-dejavu-core postgresql-client-16 && \
    apt-get clean

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . /app/

EXPOSE 10000

CMD [ "poetry", "run", "python", "main.py" ]