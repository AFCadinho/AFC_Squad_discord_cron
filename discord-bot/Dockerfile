FROM python:3.11-slim-bullseye

WORKDIR /app

RUN pip install poetry

RUN apt-get update && apt-get install -y fonts-dejavu-core

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . /app/

EXPOSE 10000

CMD [ "poetry", "run", "python", "main.py" ]