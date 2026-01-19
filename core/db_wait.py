# core/db_wait.py
import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

def wait_for_db(engine, retries: int = 30, sleep_s: float = 1.0) -> None:
    last_err = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as e:
            last_err = e
            time.sleep(sleep_s)
    raise last_err