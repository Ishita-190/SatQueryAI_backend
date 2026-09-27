from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_list_session(client: TestClient) -> None:
    res = client.post("/sessions", json={"title": "Flood AOI"})
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Flood AOI"
    assert body["job_type"] == "ask_scene"
    session_id = body["id"]

    listed = client.get("/sessions")
    assert listed.status_code == 200
    rows = listed.json()
    assert any(r["id"] == session_id for r in rows)


def test_rename_and_delete_session(client: TestClient) -> None:
    created = client.post("/sessions", json={}).json()
    sid = created["id"]

    renamed = client.patch(f"/sessions/{sid}", json={"title": "Renamed"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Renamed"

    deleted = client.delete(f"/sessions/{sid}")
    assert deleted.status_code == 204

    missing = client.get(f"/sessions/{sid}")
    assert missing.status_code == 404


def test_ownership_forbidden(client: TestClient) -> None:
    from app.auth.clerk import get_current_user
    from app.main import app

    created = client.post("/sessions", json={"title": "Mine"}).json()
    sid = created["id"]

    async def other_user():
        from app.auth.clerk import AuthUser

        return AuthUser(clerk_user_id="user_b")

    app.dependency_overrides[get_current_user] = other_user

    forbidden = client.get(f"/sessions/{sid}")
    assert forbidden.status_code == 403

    forbidden_msgs = client.get(f"/sessions/{sid}/messages")
    assert forbidden_msgs.status_code == 403


def test_upload_asset_and_restore_messages(
    client: TestClient, sample_png_bytes: bytes
) -> None:
    sid = client.post("/sessions", json={}).json()["id"]

    files = {"file": ("scene.png", sample_png_bytes, "image/png")}
    up = client.post(f"/sessions/{sid}/assets", files=files)
    assert up.status_code == 200
    payload = up.json()
    assert payload["asset"]["filename"] == "scene.png"
    assert payload["asset"]["preview_png_base64"]
    assert payload["asset"]["gcs_uri"].startswith("mem://")
    assert payload["user_message"]["attachment"]["id"] == payload["asset"]["id"]

    msgs = client.get(f"/sessions/{sid}/messages")
    assert msgs.status_code == 200
    thread = msgs.json()
    assert len(thread) >= 2
    assert thread[0]["role"] == "user"
    assert thread[0]["attachment"] is not None
    assert thread[0]["attachment"]["preview_png_base64"]


def test_send_message_uses_llm_and_persists(
    client: TestClient, sample_png_bytes: bytes
) -> None:
    sid = client.post("/sessions", json={}).json()["id"]
    files = {"file": ("scene.png", sample_png_bytes, "image/png")}
    client.post(f"/sessions/{sid}/assets", files=files)

    res = client.post(
        f"/sessions/{sid}/messages",
        json={"content": "Is there water?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["user_message"]["content"] == "Is there water?"
    assert "Echo: Is there water?" in body["assistant_message"]["content"]
    assert "image=yes" in body["assistant_message"]["content"]

    detail = client.get(f"/sessions/{sid}")
    assert detail.json()["title"] == "Is there water?"

    msgs = client.get(f"/sessions/{sid}/messages").json()
    assert any(m["content"] == "Is there water?" for m in msgs)
    assert any("Echo:" in m["content"] for m in msgs)


def test_upload_with_message_asks_llm(
    client: TestClient, sample_png_bytes: bytes
) -> None:
    sid = client.post("/sessions", json={}).json()["id"]
    files = {"file": ("scene.png", sample_png_bytes, "image/png")}
    data = {"message": "Is there a river?"}
    up = client.post(f"/sessions/{sid}/assets", files=files, data=data)
    assert up.status_code == 200
    payload = up.json()
    assert payload["user_message"]["content"] == "Is there a river?"
    assert "Use this scene" not in payload["user_message"]["content"]
    assert "Echo: Is there a river?" in payload["assistant_message"]["content"]
    assert "image=yes" in payload["assistant_message"]["content"]
    assert client.get(f"/sessions/{sid}").json()["title"] == "Is there a river?"


def test_before_after_session_renames_on_first_question(
    client: TestClient, sample_png_bytes: bytes
) -> None:
    created = client.post(
        "/sessions",
        json={"title": "Before vs after", "job_type": "before_after"},
    ).json()
    sid = created["id"]
    assert created["title"] == "Before vs after"

    files = {"file": ("before.png", sample_png_bytes, "image/png")}
    client.post(f"/sessions/{sid}/assets", files=files)

    res = client.post(
        f"/sessions/{sid}/messages",
        json={"content": "Has built-up increased?"},
    )
    assert res.status_code == 200
    detail = client.get(f"/sessions/{sid}").json()
    assert detail["title"] == "Has built-up increased?"
    assert detail["job_type"] == "before_after"


def test_unauthenticated_session_create() -> None:
    app.dependency_overrides.clear()
    with TestClient(app) as ac:
        res = ac.post("/sessions", json={})
    assert res.status_code == 401
