FROM python:3.9-slim

# python-magic linux only depenency
RUN apt-get update && apt-get install -y libmagic1

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY . /app/

EXPOSE $PORT
CMD uvicorn image_secrets.api.interface:app --host 0.0.0.0 --port "$PORT"
