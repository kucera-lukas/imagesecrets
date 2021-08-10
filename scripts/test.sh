#!/usr/bin/env bash

SRC="image_secrets"

poetry run mypy $SRC
poetry run pytest --cov=$SRC --cov-report=xml
