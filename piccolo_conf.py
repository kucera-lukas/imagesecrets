"""Piccolo configuration file."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

load_dotenv()

DB = PostgresEngine(config={"dsn": os.environ["DATABASE_URL"]})
APP_REGISTRY = AppRegistry(apps=["imagesecrets.piccolo_app"])
