import contextlib
import logging
from datetime import datetime
from time import sleep

import psycopg2
from config import app_settings
from constants import QUERY, Messages
from psycopg2.extras import RealDictCursor
from utils import (JsonFileStorage, State, create_elk_index, download_to_elk,
                   transform_data_for_elk)

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    storage = JsonFileStorage(file_path=app_settings.elk_storage_file)
    create_elk_index()
    while True:
        state = State(storage=storage)
        with (
            contextlib.closing(
                psycopg2.connect(
                    **app_settings.postgres_dsn, cursor_factory=RealDictCursor
                )
            ) as conn,
            conn.cursor() as cursor
        ):
            modified = state.get_state(app_settings.state_key)
            logger.info(Messages.CURRENT_STATE.value, modified)
            params = modified or datetime.min
            cursor.execute(QUERY, (params, ) * 3)
            while results := cursor.fetchmany(app_settings.batch_size):
                download_to_elk(rows=transform_data_for_elk(rows=results))
                state.set_state(app_settings.state_key, str(datetime.now()))
        logger.info(Messages.ELK_SLEEP.value, app_settings.sleep_time)
        sleep(app_settings.sleep_time)
