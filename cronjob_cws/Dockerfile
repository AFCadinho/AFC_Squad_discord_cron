FROM python:3.11-slim-bullseye

WORKDIR /app

# Install cron and other system deps, install poetry
RUN apt-get update && apt-get install -y cron && \
    pip install poetry

# Install Python deps
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-root

# Add project files
COPY . .

# Add cron job
COPY crontabfile /crontabfile
RUN crontab /crontabfile

# Create log file
RUN touch /var/log/cron.log

# Run cron in foreground
CMD ["cron", "-f"]
