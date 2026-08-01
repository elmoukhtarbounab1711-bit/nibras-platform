"""
اختبارات النظام البيئي المهني (API) — المرحلة 5 (قرار D-023).

التصفح العام يعرض الملفات verified فقط، والملف/الوثيقة للمهنيين، والطابور
قائم مع مزامنة القبول/الرفض لظهور الدليل، والتقييمات مفتوحة (upsert بلا
تقييم ذاتي)، والوثيقة تُنزَّل للأدمن فقط.
"""
import io

import pytest

from app import config, services_auth
from app.database import db_session
from app.routes.auth import _attempts as _auth_attempts

PASSWORD = "test-password-123"

PROFILE = {
    "profession_type": "lawyer",
    "city": "الدار البيضاء",
    "bio": "محامٍ معتمد في القانون المدني",
    "specialties": ["مدني", "أسر"],
}


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _auth_attempts.clear()
    yield
    _auth_attempts.clear()


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code, role_status="active", user_status="active"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم اختبار",
        role_code=role_code, role_status=role_status, user_status=user_status,
    )


def _lawyer(email="lawyer@nibras.test", role_status="pending_verification"):
    return _user(email, "lawyer", role_status=role_status)


def _citizen(email="citizen@nibras.test"):
    return _user(email, "citizen")


def _admin():
    return _user("admin@nibras.test", "admin")


def _create_profile(client, headers, **overrides):
    data = dict(PROFILE)
    data.update(overrides)
    return client.post("/api/professionals/profile", json=data, headers=headers)


def _approve(client, headers, user_id):
    return client.post(f"/api/admin/verification/{user_id}/approve", headers=headers)


def _upload(client, headers, content=b"%PDF-1.4 fake", name="doc.pdf"):
    return client.post(
        "/api/professionals/verify-document",
        data={"document": (io.BytesIO(content), name)},
        headers=headers,
        content_type="multipart/form-data",
    )


def test_profile_requires_auth(client):
    assert client.post("/api/professionals/profile", json=PROFILE).status_code == 401


def test_verify_document_requires_auth(client):
    assert client.post("/api/professionals/verify-document").status_code == 401


def test_reviews_requires_auth(client):
    assert client.post("/api/professionals/1/reviews", json={"rating": 5}).status_code == 401


def test_profile_creation_requires_professional_role(client):
    resp = _create_profile(client, _headers(_citizen()))
    assert resp.status_code == 403


def test_profile_create_is_pending_and_not_listed(client):
    lawyer = _lawyer()
    resp = _create_profile(client, _headers(lawyer))
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["verification_status"] == "pending"
    assert data["specialties"] == ["مدني", "أسر"]
    assert client.get("/api/professionals").get_json() == []


def test_profile_unknown_profession_type(client):
    resp = _create_profile(client, _headers(_lawyer()), profession_type="doctor")
    assert resp.status_code == 400


def test_approved_professional_appears_in_directory(client):
    lawyer = _lawyer()
    profile = _create_profile(client, _headers(lawyer)).get_json()
    admin_h = _headers(_admin())
    assert _approve(client, admin_h, lawyer.id).status_code == 200

    resp = client.get("/api/professionals")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 1
    assert items[0]["id"] == profile["id"]
    assert items[0]["full_name"] == lawyer.full_name
    assert items[0]["specialties"] == ["مدني", "أسر"]
    assert items[0]["review_count"] == 0

    detail = client.get(f"/api/professionals/{profile['id']}").get_json()
    assert detail["profession_type"] == "lawyer"
    assert detail["reviews"] == []


def test_rejected_never_listed(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    client.post(
        f"/api/admin/verification/{lawyer.id}/reject",
        json={"reason": "وثيقة غير كافية"},
        headers=_headers(_admin()),
    )
    assert client.get("/api/professionals").get_json() == []


def test_suspended_user_excluded_from_directory(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    _approve(client, _headers(_admin()), lawyer.id)
    profile_id = _profile_id(client)
    assert len(client.get("/api/professionals").get_json()) == 1
    with db_session() as conn:
        conn.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (lawyer.id,))
    assert client.get("/api/professionals").get_json() == []
    assert client.get(f"/api/professionals/{profile_id}").status_code == 404


def _profile_id(client):
    return client.get("/api/professionals").get_json()[0]["id"]


def test_directory_filters_and_pagination(client):
    admin_h = _headers(_admin())
    for i, (email, city, spec) in enumerate(
        [
            ("l1@nibras.test", "الدار البيضاء", "مدني"),
            ("l2@nibras.test", "الرباط", "أسر"),
            ("l3@nibras.test", "الدار البيضاء", "جنائي"),
        ]
    ):
        lawyer = _lawyer(email)
        _create_profile(client, _headers(lawyer), city=city, specialties=[spec])
        _approve(client, admin_h, lawyer.id)

    base = client.get("/api/professionals").get_json()
    assert len(base) == 3

    by_type = client.get("/api/professionals", query_string={"type": "lawyer"}).get_json()
    assert len(by_type) == 3

    by_city = client.get("/api/professionals", query_string={"city": "الرباط"}).get_json()
    assert len(by_city) == 1 and by_city[0]["city"] == "الرباط"

    by_spec = client.get("/api/professionals", query_string={"specialty": "مدني"}).get_json()
    assert len(by_spec) == 1

    page = client.get("/api/professionals", query_string={"limit": 2, "offset": 2}).get_json()
    assert len(page) == 1

    bad = client.get("/api/professionals", query_string={"type": "doctor"})
    assert bad.status_code == 400


def test_contact_phone_visibility(client):
    admin_h = _headers(_admin())
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer), phone="0612345678", contact_preference="platform")
    _approve(client, admin_h, lawyer.id)
    item = client.get("/api/professionals").get_json()[0]
    assert "phone" not in item

    lawyer2 = _lawyer("visible@nibras.test")
    _create_profile(client, _headers(lawyer2), phone="0699999999", contact_preference="visible")
    _approve(client, admin_h, lawyer2.id)
    item2 = client.get("/api/professionals").get_json()[1]
    assert item2["phone"] == "0699999999"


def test_verify_document_requires_profile_first(client):
    lawyer = _lawyer()
    resp = _upload(client, _headers(lawyer))
    assert resp.status_code == 400


def test_verify_document_bad_extension(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    resp = _upload(client, _headers(lawyer), name="doc.exe")
    assert resp.status_code == 400


def test_verify_document_too_large(client, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 100)
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    resp = _upload(client, _headers(lawyer), content=b"x" * 200)
    assert resp.status_code == 400


def test_verify_document_upload_and_admin_download(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    content = b"%PDF-1.4 fake document"
    resp = _upload(client, _headers(lawyer), content=content, name="carton.pdf")
    assert resp.status_code == 200
    assert resp.get_json()["document_name"] == "carton.pdf"

    citizen_h = _headers(_citizen())
    assert client.get(
        f"/api/admin/verification/{lawyer.id}/document", headers=citizen_h
    ).status_code == 403

    admin_h = _headers(_admin())
    dl = client.get(f"/api/admin/verification/{lawyer.id}/document", headers=admin_h)
    assert dl.status_code == 200
    assert dl.data == content
    assert dl.mimetype == "application/pdf"


def test_verify_document_forbidden_for_citizen(client):
    resp = _upload(client, _headers(_citizen()))
    assert resp.status_code == 403


def test_review_flow(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    _approve(client, _headers(_admin()), lawyer.id)
    profile_id = _profile_id(client)

    reviewer = _citizen()
    resp = client.post(
        f"/api/professionals/{profile_id}/reviews",
        json={"rating": 5, "comment": "خدمة ممتازة"},
        headers=_headers(reviewer),
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["rating"] == 5.0 and data["review_count"] == 1

    detail = client.get(f"/api/professionals/{profile_id}").get_json()
    assert detail["rating"] == 5.0
    assert detail["review_count"] == 1
    assert detail["reviews"][0]["comment"] == "خدمة ممتازة"


def test_review_upsert_by_same_reviewer(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    _approve(client, _headers(_admin()), lawyer.id)
    profile_id = _profile_id(client)
    reviewer = _citizen()
    h = _headers(reviewer)
    client.post(f"/api/professionals/{profile_id}/reviews", json={"rating": 5}, headers=h)
    resp = client.post(f"/api/professionals/{profile_id}/reviews", json={"rating": 3}, headers=h)
    assert resp.status_code == 201
    assert resp.get_json()["rating"] == 3.0
    assert resp.get_json()["review_count"] == 1
    detail = client.get(f"/api/professionals/{profile_id}").get_json()
    assert len(detail["reviews"]) == 1


def test_review_validates_rating(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    _approve(client, _headers(_admin()), lawyer.id)
    profile_id = _profile_id(client)
    h = _headers(_citizen())
    assert client.post(
        f"/api/professionals/{profile_id}/reviews", json={"rating": 6}, headers=h
    ).status_code == 400
    assert client.post(
        f"/api/professionals/{profile_id}/reviews", json={"rating": "abc"}, headers=h
    ).status_code == 400


def test_no_self_review(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    _approve(client, _headers(_admin()), lawyer.id)
    profile_id = _profile_id(client)
    resp = client.post(
        f"/api/professionals/{profile_id}/reviews",
        json={"rating": 5},
        headers=_headers(lawyer),
    )
    assert resp.status_code == 403


def test_review_only_on_verified_profile(client):
    pending = _lawyer("pending@nibras.test")
    _create_profile(client, _headers(pending))
    pending_id = pending.id
    # لا نعرف profile_id من القائمة (غير ظاهر) — نستخدم id الصف مباشرة
    from app.database import db_session

    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM professional_profiles WHERE user_id = ?", (pending_id,)
        ).fetchone()
    resp = client.post(
        f"/api/professionals/{row['id']}/reviews",
        json={"rating": 4},
        headers=_headers(_citizen()),
    )
    assert resp.status_code == 404


def test_profile_update_preserves_verification(client):
    lawyer = _lawyer()
    _create_profile(client, _headers(lawyer))
    _approve(client, _headers(_admin()), lawyer.id)
    resp = _create_profile(client, _headers(lawyer), city="مراكش", specialties=["تجاري"])
    assert resp.status_code == 201
    assert resp.get_json()["verification_status"] == "verified"
    assert resp.get_json()["city"] == "مراكش"
    item = client.get("/api/professionals").get_json()[0]
    assert item["city"] == "مراكش"
    assert item["specialties"] == ["تجاري"]
