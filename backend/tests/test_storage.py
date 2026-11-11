"""
tests/test_storage.py - Pengujian Penyimpanan Lokal dan CRUD
"""
import uuid
from app.database.storage import storage
from app.models.schemas import Participant, RubricProfile


def test_participant_crud():
    part_id = f"test-{uuid.uuid4().hex[:6]}"
    p = Participant(
        id=part_id,
        name="Peserta Uji",
        participant_number="UKK-TEST-001",
        student_class="XII TKJ 1",
        school="SMK Negeri 1 Banyumas"
    )
    storage.save_participant(p)

    fetched = storage.get_participant(part_id)
    assert fetched is not None
    assert fetched.name == "Peserta Uji"

    deleted = storage.delete_participant(part_id)
    assert deleted is True
    assert storage.get_participant(part_id) is None


def test_rubrics_persistence():
    rubrics = storage.list_rubrics()
    assert len(rubrics) > 0
    default_p = storage.get_rubric("default-ukk-mbg-rev1")
    assert default_p is not None
    assert "Revisi 1" in default_p.name

