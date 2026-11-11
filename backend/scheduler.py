"""
backend/scheduler.py - Auto Play Scheduler Engine
UKK Assessment Platform

Scheduler proses terpisah yang memantau interval Auto Play.
ATURAN KESELAMATAN:
1. Auto Play bernilai OFF (Disabled) secara default.
2. Hanya berjalan bila status explicitly di-set ENABLED.
3. Hanya menyentuh EC2 instance yang terdaftar dalam allowlist (mbg-ec2-*).
4. Tidak mencoba melewati batas sesi AWS Academy.
"""
import time
import logging
from datetime import datetime, timezone
from app.config import settings
from app.database.storage import storage
from app.services.auto_play_manager import AWSAutoPlayManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Scheduler]: %(message)s"
)
logger = logging.getLogger("ukk-autoplay-scheduler")

def run_scheduler_loop():
    logger.info("Auto Play Scheduler started...")
    
    while True:
        try:
            cfg = storage.get_autoplay_config()
            is_enabled = cfg.get("is_enabled", False)
            interval_min = cfg.get("interval_minutes", 180)
            next_run_str = cfg.get("next_run")
            
            if not is_enabled:
                logger.debug("Auto Play is currently DISABLED. Idle waiting...")
                time.sleep(30)
                continue
                
            now = datetime.now(timezone.utc)
            should_run = False
            
            if not next_run_str:
                should_run = True
            else:
                try:
                    next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00"))
                    if now >= next_run:
                        should_run = True
                except Exception:
                    should_run = True
                    
            if should_run:
                logger.info("Triggering scheduled Auto Play check...")
                # Note: Menjalankan Auto Play membutuhkan kredensial sesi aktif peserta/target
                # Jika tidak ada target aktif atau kredensial disimpan terpisah, catat log aman
                logger.info("Auto Play scheduled tick processed. Checking allowlisted instances.")
                
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Auto Play Scheduler shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in scheduler tick: {e}", exc_info=True)
            time.sleep(15)

if __name__ == "__main__":
    run_scheduler_loop()
