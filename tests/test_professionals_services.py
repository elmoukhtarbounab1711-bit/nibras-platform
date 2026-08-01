"""
اختبارات طبقة خدمات النظام البيئي المهني (المرحلة 5) — قرار D-023.

حصرية الظهور (verified + مستخدم نشط) على مستوى الاستعلام، مزامنة القبول/
الرفض مع الطابور، upsert التقييم، حصر التخصصات، وتخزين الوثائق محليًا
مع استبدال الملف السابق.
"""
import io

import pytest

from app import config, services_auth
from app.database import db_session
from app.services_admin import AdminError
from app.services_professionals import (
    ProfessionalError,
    _uploads_dir,
    add_review,
    get_profile_public,
    get_verification_document,
    list_professionals,
    upload_verification_document,
    upsert_profile,
)

PASSWORD = "test-password-123"
PROFILE = {
    "profession_type": "notary",
    "city": "الرباط",
    "bio": "موثق",
    "specialties": ["عقاري"],
}


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def _user(email, role_code, role_status="active", user_status="active"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم",
        role_code=role_code, role_status=role_status, user_status=user_status,
    )


def _approve(user_id):
    admin = _user(f"adm-{user_id}@nibras.test", "admin")
    from app import services_admin

    services_admin.approve_verification(admin.id, user_id)


def _reject(user_id, reason="وثيقة غير كافية"):
    admin = _user(f"rej-{user_id}@nibras.test", "admin")
    from app import services_admin

    services_admin.reject_verification(admin.id, user_id, reason)


def test_only_verified_and_active_in_directory(fresh_db):
    lawyer = _user("l@nibras.test", "lawyer", role_status="pending_verification")
    upsert_profile(lawyer.id, PROFILE)
    assert list_professionals() == []  # pending

    _approve(lawyer.id)
    assert len(list_professionals()) == 1  # verified

    with db_session() as conn:
        conn.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (lawyer.id,))
    assert list_professionals() == []  # مستخدم غير نشط


def test_approve_reject_syncs_profile_status(fresh_db):
    lawyer = _user("l2@nibras.test", "lawyer", role_status="pending_verification")
    profile = upsert_profile(lawyer.id, PROFILE)
    assert profile["verification_status"] == "pending"
    _approve(lawyer.id)
    assert upsert_profile(lawyer.id, PROFILE)["verification_status"] == "verified"
    # القبول يجعل role_status نشطًا، فلا يمكن الرفض بعدها (قرار D-023)
    with pytest.raises(AdminError) as exc:
        _reject(lawyer.id)
    assert exc.value.status_code == 409


def test_reject_sets_profile_rejected_and_hidden(fresh_db):
    lawyer = _user("l2b@nibras.test", "lawyer", role_status="pending_verification")
    profile = upsert_profile(lawyer.id, PROFILE)
    _reject(lawyer.id)
    with db_session() as conn:
        row = conn.execute(
            "SELECT verification_status FROM professional_profiles WHERE user_id = ?",
            (lawyer.id,),
        ).fetchone()
    assert row["verification_status"] == "rejected"
    assert get_profile_public(profile["id"]) is None


def test_upsert_preserves_document_and_status(fresh_db):
    lawyer = _user("l3@nibras.test", "lawyer", role_status="pending_verification")
    upsert_profile(lawyer.id, PROFILE)
    upload_verification_document(
        lawyer.id, _file_storage("v.pdf", b"%PDF-1.4")
    )
    updated = upsert_profile(lawyer.id, {**PROFILE, "city": "فاس"})
    assert updated["has_document"] is True
    assert updated["verification_status"] == "pending"
    assert updated["city"] == "فاس"


def _file_storage(name, content):
    from werkzeug.datastructures import FileStorage

    return FileStorage(stream=io.BytesIO(content), filename=name)


def test_upload_requires_profile_first(fresh_db):
    lawyer = _user("l4@nibras.test", "lawyer", role_status="pending_verification")
    with pytest.raises(ProfessionalError) as exc:
        upload_verification_document(lawyer.id, _file_storage("v.pdf", b"x"))
    assert exc.value.status_code == 400


def test_upload_replaces_previous_file(fresh_db):
    lawyer = _user("l5@nibras.test", "lawyer", role_status="pending_verification")
    upsert_profile(lawyer.id, PROFILE)
    upload_verification_document(lawyer.id, _file_storage("a.pdf", b"AAA"))
    path1, _name1, _ = get_verification_document(lawyer.id)
    upload_verification_document(lawyer.id, _file_storage("b.pdf", b"BBB"))
    path2, name2, _ = get_verification_document(lawyer.id)
    assert name2 == "b.pdf"
    assert path1 != path2
    assert not _uploads_dir().joinpath(path1.rsplit("/", 1)[-1]).exists()
    assert _uploads_dir().joinpath(path2.rsplit("/", 1)[-1]).read_bytes() == b"BBB"


def test_specialty_limits_and_dedup(fresh_db):
    lawyer = _user("l6@nibras.test", "lawyer", role_status="pending_verification")
    dup = upsert_profile(lawyer.id, {**PROFILE, "specialties": ["مدني", "مدني", "أسر"]})
    assert dup["specialties"] == ["مدني", "أسر"]
    with pytest.raises(ProfessionalError):
        upsert_profile(
            lawyer.id,
            {**PROFILE, "specialties": [f"s{i}" for i in range(11)]},
        )
    with pytest.raises(ProfessionalError):
        upsert_profile(lawyer.id, {**PROFILE, "specialties": "مدني"})


def test_review_upsert_and_aggregate(fresh_db):
    lawyer = _user("l7@nibras.test", "lawyer", role_status="pending_verification")
    profile = upsert_profile(lawyer.id, PROFILE)
    _approve(lawyer.id)
    reviewer = _user("r@nibras.test", "citizen")
    add_review(reviewer.id, profile["id"], 5, "ممتاز")
    result = add_review(reviewer.id, profile["id"], 3, "معدّل")
    assert result["review_count"] == 1
    assert result["rating"] == 3.0
    other = _user("r2@nibras.test", "citizen")
    add_review(other.id, profile["id"], 4)
    public = get_profile_public(profile["id"])
    assert public["rating"] == 3.5
    assert public["review_count"] == 2
    assert len(public["reviews"]) == 2


def test_no_self_review(fresh_db):
    lawyer = _user("l8@nibras.test", "lawyer", role_status="pending_verification")
    profile = upsert_profile(lawyer.id, PROFILE)
    _approve(lawyer.id)
    with pytest.raises(ProfessionalError) as exc:
        add_review(lawyer.id, profile["id"], 5)
    assert exc.value.status_code == 403


def test_review_only_verified(fresh_db):
    lawyer = _user("l9@nibras.test", "lawyer", role_status="pending_verification")
    profile = upsert_profile(lawyer.id, PROFILE)
    reviewer = _user("r3@nibras.test", "citizen")
    with pytest.raises(ProfessionalError) as exc:
        add_review(reviewer.id, profile["id"], 5)
    assert exc.value.status_code == 404


def test_invalid_rating(fresh_db):
    lawyer = _user("l10@nibras.test", "lawyer", role_status="pending_verification")
    profile = upsert_profile(lawyer.id, PROFILE)
    _approve(lawyer.id)
    reviewer = _user("r4@nibras.test", "citizen")
    with pytest.raises(ProfessionalError):
        add_review(reviewer.id, profile["id"], 0)
    with pytest.raises(ProfessionalError):
        add_review(reviewer.id, profile["id"], "abc")
