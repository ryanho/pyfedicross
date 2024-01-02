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

# Run the application
ENTRYPOINT ["python"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]