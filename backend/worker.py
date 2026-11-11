"""
backend/worker.py - Assessment Background Worker
UKK Assessment Platform

Worker proses terpisah yang memproses antrean tugas penilaian (batch evaluation),
sinkronisasi periodik laporan ke Google Sheets, dan tugas asinkron lainnya.
"""
import time
import logging
from datetime import datetime
from app.config import settings
from app.database.storage import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker]: %(message)s"
)
logger = logging.getLogger("ukk-assessment-worker")

def run_worker_loop():
    logger.info("Assessment Worker started and running...")
    logger.info(f"Target Storage Mode: {'Google Sheets + Fallback' if storage.sheets.is_connected else 'Local Storage'}")
    
    while True:
        try:
            # 1. Heartbeat check & Queue polling
            # Di masa depan antrean Redis/DB dapat di-consume di sini
            participants = storage.list_participants()
            logger.debug(f"[Heartbeat] Active participants registered: {len(participants)}")
            
            # Polling interval 10 detik
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Assessment Worker stopping due to KeyboardInterrupt...")
            break
        except Exception as e:
            logger.error(f"Error in Assessment Worker loop: {e}", exc_info=True)
            time.sleep(5)

if __name__ == "__main__":
    run_worker_loop()
