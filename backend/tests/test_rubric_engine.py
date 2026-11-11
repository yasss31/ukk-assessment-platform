"""
tests/test_rubric_engine.py - Pengujian Mesin Rubrik & Kalkulasi Nilai
"""
from app.services.rubric_engine import RubricEngine
from app.database.storage import storage
from app.models.schemas import RubricProfile, IndicatorResult, IndicatorStatus, RubricIndicator


def test_default_rubric_profile():
    profile = storage.get_rubric("default-ukk-mbg-rev1")
    assert profile is not None
    assert profile.id == "default-ukk-mbg-rev1"
    assert len(profile.indicators) >= 17
    assert abs(profile.total_weight - 100.0) < 0.1


def test_score_calculation():
    profile = RubricProfile(
        id="test-rubric",
        name="Test Rubric",
        description="Testing calculation",
        indicators=[
            RubricIndicator(
                id="ind-1",
                code="VPC.01",
                name="VPC Check",
                category="Network",
                expected_value="10.0.0.0/16",
                weight=10.0,
                check_method="aws_api_vpc"
            ),
            RubricIndicator(
                id="ind-2",
                code="RDS.01",
                name="RDS Check",
                category="Database",
                expected_value="mbg-rds-mysql",
                weight=20.0,
                check_method="aws_api_rds"
            )
        ]
    )

    indicators_eval = [
        IndicatorResult(
            indicator_id="ind-1",
            code="VPC.01",
            name="VPC Check",
            category="Network",
            expected="10.0.0.0/16",
            actual="10.0.0.0/16",
            status=IndicatorStatus.PASS,
            score=10.0,
            weight=10.0,
            evidence="VPC matches CIDR 10.0.0.0/16"
        ),
        IndicatorResult(
            indicator_id="ind-2",
            code="RDS.01",
            name="RDS Check",
            category="Database",
            expected="mbg-rds-mysql",
            actual="Not Found",
            status=IndicatorStatus.FAIL,
            score=0.0,
            weight=20.0,
            evidence="RDS instance not found"
        )
    ]

    final_score, pass_count, fail_count, skip_count, error_count, warning_count = RubricEngine.calculate_score(indicators_eval, profile)
    # Total weight = 30. Earned = 10. Pct = (10/30)*100 = 33.3
    assert final_score == 33.3
    assert pass_count == 1
    assert fail_count == 1
    assert skip_count == 0
    assert error_count == 0
    assert warning_count == 0
