"""
tests/test_troubleshooting.py - Pengujian Smart Feedback & Troubleshooting Engine
"""
from app.services.troubleshooting_kb import TroubleshootingKB
from app.models.schemas import ErrorSeverity, IndicatorResult, IndicatorStatus, RubricProfile, RubricIndicator
from app.services.assessment_engine import AWSAssessmentEngine
from app.models.schemas import AWSCredentialInput


def test_troubleshooting_kb_matches():
    # Test 03.02 (EFS Security Group)
    guide = TroubleshootingKB.get_guide(
        code="03.02",
        expected="mbg-sg-efs source: mbg-sg-fe",
        actual="Port 2049 tidak ditemukan",
        error_message="Port 2049 tidak ditemukan"
    )
    assert guide.severity == ErrorSeverity.CRITICAL
    assert "2049" in guide.what_is_wrong
    assert "NFS" in guide.why_wrong
    assert len(guide.how_to_fix) > 0
    assert len(guide.how_to_verify) > 0
    assert "Security Groups" in guide.fix_location


def test_troubleshooting_fallback_unknown_code():
    guide = TroubleshootingKB.get_guide(
        code="CUSTOM.99",
        expected="Custom Value",
        actual="Actual Value"
    )
    assert guide.severity == ErrorSeverity.MAJOR
    assert "CUSTOM.99" in guide.what_is_wrong
    assert guide.actual_found == "Actual Value"
