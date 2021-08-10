#!/usr/bin/env bash

SRC="image_secrets"

poetry run mypy $SRC --verbose
poetry run pytest --verbose --cov=$SRC --cov-report=xml
