import logging
import os

import sqlalchemy
from fakeredis import FakeRedis
from flask import Flask
from sqlalchemy.schema import MetaData

from iris import controller
from iris.db import tables
from iris.db.tables.events import Events
from iris.db.tables.tickets import Tickets
from iris.db.tables.users import Users

logger = logging.getLogger()


class Config:

    def __init__(self):
        # DB
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_port = int(os.environ.get('DB_PORT')) if os.environ.get('DB_PORT') else 3306
        self.db_username = os.environ.get('DB_USERNAME')
        self.db_passwd = os.environ.get('DB_PASSWD')
        self.db_name = os.environ.get('DB_NAME')

        # Redis
        self.redis_host = os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = int(os.environ.get('REDIS_PORT')) if os.environ.get('REDIS_PORT') else 6627
        self.redis_db = int(os.environ.get('REDIS_DB')) if os.environ.get('REDIS_DB') else 0

    @property
    def db_config(self) -> dict:
        return dict(
            db_host=self.db_host,
            db_port=self.db_port,
            db_username=self.db_username,
            db_passwd=self.db_passwd,
            db_name=self.db_name
        )

    @property
    def redis_config(self) -> dict:
        return dict(
            redis_host=self.redis_host,
            redis_port=self.redis_port,
            redis_db=self.redis_db
        )


class NoStageStated(Exception):
    pass


def init_app():
    app = Flask(__name__)
    app.register_blueprint(controller.controllers)
    config = Config()
    stage = os.environ.get('STAGE', 'TEST').upper()

    # set logging
    if stage in ['TEST', 'STAGING']:
        logger.setLevel(logging.DEBUG)

    app.config['app.logger'] = logger
    if stage == 'TEST':
        engine = sqlalchemy.create_engine('sqlite://')
        metadata = MetaData(bind=engine)
    elif stage in {'STAGING', 'PRODUCTION'}:
        engine, metadata = tables.create_engine_and_metadata(config.db_config)
    else:
        raise NoStageStated

    # init db model
    app.config['app.db.events'] = Events(engine, metadata)
    app.config['app.db.tickets'] = Tickets(engine, metadata, role='writer')
    app.config['app.db.users'] = Users(engine, metadata, role='writer')

    return app


app = init_app()
