"""
tests/test_resilience_and_routes.py - Verification tests for resilient grading and routes
"""
import pytest
from app.models.schemas import Participant, AWSCredentialInput, IndicatorStatus
from app.routers import assessment_routes
from app.services.troubleshooting_kb import TroubleshootingKB
from app.services.official_rubric_kb import OFFICIAL_ASPEK_METADATA


def test_participant_imported_in_assessment_routes():
    """Verify that Participant is properly imported in assessment_routes module namespace."""
    assert hasattr(assessment_routes, "Participant"), "Participant must be imported in assessment_routes"
    assert assessment_routes.Participant == Participant


def test_troubleshooting_kb_cidr_correctness():
    """Verify that TroubleshootingKB has the correct CIDRs for private subnets (fe-1a=10.20.11.0/24, fe-1b=10.20.12.0/24)."""
    entry = TroubleshootingKB.KB.get("01.03")
    assert entry is not None
    how_to_fix_text = " ".join(entry["how_to_fix"])
    assert "10.20.11.0/24" in how_to_fix_text, "fe-1a must use 10.20.11.0/24"
    assert "10.20.12.0/24" in how_to_fix_text, "fe-1b must use 10.20.12.0/24"
    assert "10.20.10.0/24" not in how_to_fix_text, "10.20.10.0/24 is reserved for be, not fe-1a"


def test_official_rubric_kb_revision_3_metadata():
    """Verify that all 17 aspects reference Revisi 3 and Soal_UKK Cloud Engineer_2627-Rev3.pdf."""
    assert len(OFFICIAL_ASPEK_METADATA) == 17
    for key, meta in OFFICIAL_ASPEK_METADATA.items():
        assert meta["doc_revision"] == "Revisi 3", f"Aspek {key} must reference Revisi 3"
        assert meta["doc_name"] == "Soal_UKK Cloud Engineer_2627-Rev3.pdf", f"Aspek {key} must reference Rev3 PDF"
