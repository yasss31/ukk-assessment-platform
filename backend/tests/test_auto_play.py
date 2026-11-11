"""
tests/test_auto_play.py - Pengujian Fitur AWS Auto Play
"""
from app.services.auto_play_manager import AWSAutoPlayManager
from app.database.storage import storage


def test_autoplay_config_toggle():
    # Update config to enabled
    cfg = AWSAutoPlayManager.update_config(is_enabled=True, interval_minutes=120)
    assert cfg.is_enabled is True
    assert cfg.interval_minutes == 120
    assert cfg.last_status == "SCHEDULED"

    # Update config to disabled
    cfg2 = AWSAutoPlayManager.update_config(is_enabled=False)
    assert cfg2.is_enabled is False
    assert cfg2.last_status == "DISABLED"


def test_autoplay_logs():
    logs = storage.get_autoplay_logs(limit=10)
    assert isinstance(logs, list)
    assert len(logs) > 0
    # Cek log terakhir ada action
    assert "action" in logs[0]
