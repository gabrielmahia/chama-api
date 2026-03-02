"""chama-api test suite."""
from __future__ import annotations

import pytest
from datetime import date
from fastapi.testclient import TestClient
from chama_api.app import create_app
from chama_api.store import Store
from chama_api import routers

# ── Fresh app + store per test session ────────────────────────────────────────
@pytest.fixture(autouse=True)
def reset_store():
    """Reset the global store between tests."""
    import chama_api.store as s
    s.store = Store()
    # Re-import store into each router module
    import importlib
    for mod in [routers.chamas, routers.members, routers.contributions, routers.loans]:
        importlib.reload(mod)
    yield

@pytest.fixture
def client():
    return TestClient(create_app())

def make_chama(client):
    r = client.post("/chamas/", json={
        "name": "Umoja Savings", "cycle_frequency": "monthly",
        "contribution_kes": 5000, "meeting_day": "Last Saturday",
    })
    assert r.status_code == 201
    return r.json()

def make_member(client, chama_id, name="Jane Wanjiku", phone="254712345678", role="member"):
    r = client.post(f"/chamas/{chama_id}/members", json={
        "full_name": name, "phone": phone, "role": role,
        "join_date": str(date.today()),
    })
    assert r.status_code == 201
    return r.json()


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestChamasCRUD:
    def test_create_chama(self, client):
        r = client.post("/chamas/", json={
            "name": "Test Chama", "cycle_frequency": "monthly",
            "contribution_kes": 3000, "meeting_day": "Saturday",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["name"] == "Test Chama"
        assert d["status"] == "active"
        assert "id" in d

    def test_create_chama_with_paybill(self, client):
        r = client.post("/chamas/", json={
            "name": "Chama X", "cycle_frequency": "weekly",
            "contribution_kes": 1000, "meeting_day": "Friday",
            "paybill": "522533",
        })
        assert r.json()["paybill"] == "522533"

    def test_invalid_frequency_rejected(self, client):
        r = client.post("/chamas/", json={
            "name": "Bad", "cycle_frequency": "daily",
            "contribution_kes": 1000, "meeting_day": "Mon",
        })
        assert r.status_code == 422

    def test_list_chamas(self, client):
        make_chama(client)
        make_chama(client)
        r = client.get("/chamas/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_chama(self, client):
        chama = make_chama(client)
        r = client.get(f"/chamas/{chama['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == chama["id"]

    def test_get_missing_chama_404(self, client):
        r = client.get("/chamas/nonexistent")
        assert r.status_code == 404

    def test_update_chama(self, client):
        chama = make_chama(client)
        r = client.patch(f"/chamas/{chama['id']}", json={"contribution_kes": 7500})
        assert r.status_code == 200
        assert r.json()["contribution_kes"] == 7500

    def test_member_count_increments(self, client):
        chama = make_chama(client)
        assert client.get(f"/chamas/{chama['id']}").json()["member_count"] == 0
        make_member(client, chama["id"])
        assert client.get(f"/chamas/{chama['id']}").json()["member_count"] == 1


class TestMembers:
    def test_add_member(self, client):
        chama = make_chama(client)
        r = client.post(f"/chamas/{chama['id']}/members", json={
            "full_name": "Jane Wanjiku", "phone": "254712345678",
            "role": "member", "join_date": str(date.today()),
        })
        assert r.status_code == 201
        assert r.json()["full_name"] == "Jane Wanjiku"

    def test_phone_normalised_07(self, client):
        chama = make_chama(client)
        r = client.post(f"/chamas/{chama['id']}/members", json={
            "full_name": "John", "phone": "0712345678",
            "role": "member", "join_date": str(date.today()),
        })
        assert r.status_code == 201
        assert r.json()["phone"] == "254712345678"

    def test_invalid_phone_rejected(self, client):
        chama = make_chama(client)
        r = client.post(f"/chamas/{chama['id']}/members", json={
            "full_name": "Bad", "phone": "12345",
            "role": "member", "join_date": str(date.today()),
        })
        assert r.status_code == 422

    def test_invalid_role_rejected(self, client):
        chama = make_chama(client)
        r = client.post(f"/chamas/{chama['id']}/members", json={
            "full_name": "Bad", "phone": "254712345678",
            "role": "president", "join_date": str(date.today()),
        })
        assert r.status_code == 422

    def test_list_members(self, client):
        chama = make_chama(client)
        make_member(client, chama["id"], phone="254712345678")
        make_member(client, chama["id"], name="John Kamau", phone="254723456789")
        r = client.get(f"/chamas/{chama['id']}/members")
        assert len(r.json()) == 2

    def test_get_member(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        r = client.get(f"/chamas/{chama['id']}/members/{member['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == member["id"]


class TestContributions:
    def test_record_contribution(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        r = client.post(f"/chamas/{chama['id']}/contributions", json={
            "member_id": member["id"], "amount": 5000,
            "cycle_date": str(date.today()), "status": "confirmed",
            "mpesa_receipt": "NLJ7RT61SV",
        })
        assert r.status_code == 201
        assert r.json()["mpesa_receipt"] == "NLJ7RT61SV"

    def test_duplicate_receipt_rejected(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        payload = {"member_id": member["id"], "amount": 5000,
                   "cycle_date": str(date.today()), "status": "confirmed",
                   "mpesa_receipt": "DUPRECEIPT1"}
        r1 = client.post(f"/chamas/{chama['id']}/contributions", json=payload)
        r2 = client.post(f"/chamas/{chama['id']}/contributions", json=payload)
        assert r1.status_code == 201
        assert r2.status_code == 409

    def test_list_contributions_paginated(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        for i in range(5):
            client.post(f"/chamas/{chama['id']}/contributions", json={
                "member_id": member["id"], "amount": 5000,
                "cycle_date": str(date.today()), "status": "confirmed",
                "mpesa_receipt": f"REC_{i:04d}",
            })
        r = client.get(f"/chamas/{chama['id']}/contributions?limit=3&offset=0")
        d = r.json()
        assert d["total"] == 5
        assert len(d["items"]) == 3
        assert d["limit"] == 3

    def test_filter_by_status(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        client.post(f"/chamas/{chama['id']}/contributions", json={
            "member_id": member["id"], "amount": 5000,
            "cycle_date": str(date.today()), "status": "confirmed", "mpesa_receipt": "REC001"})
        client.post(f"/chamas/{chama['id']}/contributions", json={
            "member_id": member["id"], "amount": 5000,
            "cycle_date": str(date.today()), "status": "pending"})
        r = client.get(f"/chamas/{chama['id']}/contributions?status=confirmed")
        assert r.json()["total"] == 1


class TestLoans:
    def test_issue_loan(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        r = client.post(f"/chamas/{chama['id']}/loans", json={
            "member_id": member["id"], "principal": 15000,
            "interest_rate": 0.10, "term_months": 3,
            "disbursed_date": str(date.today()),
        })
        assert r.status_code == 201
        d = r.json()
        assert d["total_repayable"] == 19500.0  # 15000 * (1 + 0.10 * 3)
        assert d["outstanding"] == 19500.0

    def test_duplicate_active_loan_rejected(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        payload = {"member_id": member["id"], "principal": 10000,
                   "interest_rate": 0.10, "term_months": 3,
                   "disbursed_date": str(date.today())}
        r1 = client.post(f"/chamas/{chama['id']}/loans", json=payload)
        r2 = client.post(f"/chamas/{chama['id']}/loans", json=payload)
        assert r1.status_code == 201
        assert r2.status_code == 409

    def test_list_loans(self, client):
        chama = make_chama(client)
        m1 = make_member(client, chama["id"], phone="254712345678")
        m2 = make_member(client, chama["id"], name="John K", phone="254723456789")
        for m in [m1, m2]:
            client.post(f"/chamas/{chama['id']}/loans", json={
                "member_id": m["id"], "principal": 5000,
                "interest_rate": 0.10, "term_months": 1,
                "disbursed_date": str(date.today()),
            })
        r = client.get(f"/chamas/{chama['id']}/loans")
        assert len(r.json()) == 2

    def test_get_loan(self, client):
        chama = make_chama(client)
        member = make_member(client, chama["id"])
        loan = client.post(f"/chamas/{chama['id']}/loans", json={
            "member_id": member["id"], "principal": 5000,
            "interest_rate": 0.10, "term_months": 1,
            "disbursed_date": str(date.today()),
        }).json()
        r = client.get(f"/chamas/{chama['id']}/loans/{loan['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == loan["id"]
