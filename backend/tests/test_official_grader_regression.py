"""
tests/test_official_grader_regression.py - Regression Test Penilaian Resmi UKK MBG
Single Source of Truth: grade.py & Soal_UKK Cloud Engineer_2627-Rev1.pdf
"""
import json
from pathlib import Path
from app.models.schemas import (
    Participant, AWSCredentialInput, IndicatorStatus, ErrorSeverity
)
from app.services.official_grader_adapter import OfficialGraderAdapter


def test_regression_fixture_score_and_aspects():
    """
    Menguji kesesuaian data penilaian resmi grade.py:
    - Nilai akhir: 100.0 / 100
    - Bobot dinilai: 94
    - Poin diperoleh: 94
    - Aspek 09: CPU 60% = PASS
    - Aspek 14: Uji ketahanan ASG = SKIP (tidak mengurangi nilai)
    """
    # Muat fixture laporan grade.py resmi
    fixture_path = Path("d:/LKPD/hasil_penilaian_20261112_104019.json")
    assert fixture_path.is_file(), "Fixture file hasil_penilaian_20261112_104019.json harus tersedia"

    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    # 1. Verifikasi skor grade.py asli
    assert data["nilai_akhir"] == 100.0
    aspek = data["aspek"]
    assert len(aspek) == 17

    # 2. Verifikasi Aspek 09 (ASG CPU 60%)
    asp09 = aspek["09"]
    assert asp09["bobot"] == 7
    assert asp09["rasio"] == 1.0
    assert asp09["skip"] is None
    cpu_checks = [c for c in asp09["checks"] if "CPU 60%" in c["desc"] or "Scaling policy" in c["desc"]]
    assert len(cpu_checks) >= 1
    assert cpu_checks[0]["status"] == "PASS"

    # 3. Verifikasi Aspek 14 (Uji ketahanan Auto Scaling = SKIP)
    asp14 = aspek["14"]
    assert asp14["bobot"] == 6
    assert asp14["skip"] is not None
    assert "dilewati" in asp14["skip"]
    assert asp14["rasio"] == 0.0

    # 4. Verifikasi perhitungan bobot dinilai vs yang dilewati
    bobot_dinilai = sum(v["bobot"] for k, v in aspek.items() if v.get("skip") is None)
    poin_diperoleh = sum(v["bobot"] * v["rasio"] for k, v in aspek.items() if v.get("skip") is None)
    assert bobot_dinilai == 94
    assert poin_diperoleh == 94.0
    final_score = round(100.0 * (poin_diperoleh / bobot_dinilai), 1)
    assert final_score == 100.0
