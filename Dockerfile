FROM python:3.11-slim

ENV DOCKER_ENVIRON=1

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY . /app

EXPOSE 8000
VOLUME ["/data"]

RUN chmod +x /app/start.sh

# Run the application
ENTRYPOINT ["/app/start.sh"]