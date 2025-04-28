FROM python:3.12-slim

ENV DOCKER_ENVIRON=1

WORKDIR /app
COPY pyproject.toml /app/
RUN python -m venv venv \
  && venv/bin/pip install .

COPY . /app

EXPOSE 8000
VOLUME ["/data"]

RUN chmod +x /app/start.sh

# Run the application
ENTRYPOINT ["/app/start.sh"]