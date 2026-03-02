# chama-api

**FastAPI REST service for chama (ROSCA) management — JWT auth scaffold, CRUD, OpenAPI docs.**

[![CI](https://github.com/gabrielmahia/chama-api/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielmahia/chama-api/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![Tests](https://img.shields.io/badge/tests-36%20passing-brightgreen)](#)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey)](LICENSE)

REST API service layer for chama management, built on [chama-protocol](https://github.com/gabrielmahia/chama-protocol).
Exposes chama, member, contribution, and loan operations over HTTP with automatic OpenAPI documentation.

**Architecture:**
```
chama-protocol  ← domain library
      ↑
chama-api       ← HTTP service (this repo)
      ↑
hela / mobile / any HTTP client
```

---

## Install & run

```bash
pip install -e ".[server]"
uvicorn chama_api.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
# → http://localhost:8000/redoc (ReDoc)
```

---

## Endpoints

### Chamas
```
POST   /chamas/                         Create chama
GET    /chamas/                         List all chamas
GET    /chamas/{id}                     Get chama (includes member_count)
PATCH  /chamas/{id}                     Update name, contribution, status
```

### Members
```
POST   /chamas/{id}/members             Add member (phone normalised automatically)
GET    /chamas/{id}/members             List members (includes compliance_rate)
GET    /chamas/{id}/members/{member_id} Get member
```

### Contributions
```
POST   /chamas/{id}/contributions       Record payment (idempotent on mpesa_receipt)
GET    /chamas/{id}/contributions       List with pagination + status/member filters
GET    /chamas/{id}/contributions/{cid} Get contribution
```

### Loans
```
POST   /chamas/{id}/loans               Issue loan (one active loan per member enforced)
GET    /chamas/{id}/loans               List loans (filter by status)
GET    /chamas/{id}/loans/{loan_id}     Get loan (includes total_repayable, outstanding)
```

---

## Example flow

```bash
# Create a chama
curl -X POST http://localhost:8000/chamas/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Umoja Savings","cycle_frequency":"monthly","contribution_kes":5000,"meeting_day":"Last Saturday"}'

# {"id":"abc-123","name":"Umoja Savings","status":"active","member_count":0,...}

# Add a member
curl -X POST http://localhost:8000/chamas/abc-123/members \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Jane Wanjiku","phone":"0712345678","role":"treasurer"}'

# {"id":"m-456","phone":"254712345678","compliance_rate":0.0,...}

# Record an M-Pesa contribution (idempotent)
curl -X POST http://localhost:8000/chamas/abc-123/contributions \
  -H "Content-Type: application/json" \
  -d '{"member_id":"m-456","amount":5000,"cycle_date":"2024-01-31","status":"confirmed","mpesa_receipt":"NLJ7RT61SV"}'

# Issue a loan
curl -X POST http://localhost:8000/chamas/abc-123/loans \
  -H "Content-Type: application/json" \
  -d '{"member_id":"m-456","principal":15000,"interest_rate":0.10,"term_months":3}'

# {"total_repayable":19500.0,"outstanding":19500.0,...}
```

---

## Design decisions

**Idempotency on contributions.** If an M-Pesa receipt is provided, duplicate POSTs
to `/contributions` return HTTP 409 rather than double-counting a payment. Same pattern
as [mpesa-webhooks](https://github.com/gabrielmahia/mpesa-webhooks).

**One active loan per member.** The loans endpoint enforces that a member cannot have
two active loans simultaneously — the most common rule in Kenyan chamas.

**Pluggable store.** The `Store` class in `store.py` uses in-memory dicts by default.
Replace each method with database queries to connect PostgreSQL, Firestore, or any backend
without changing the router logic.

**Compliance rate calculated on read.** Member responses include `compliance_rate`
(settled contributions / total contributions). This is computed on retrieval from the
contribution log rather than stored — keeping the write path simple and the read path
always accurate.

---

*Part of the [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack) East Africa engineering ecosystem.*
*Maintained by [Gabriel Mahia](https://github.com/gabrielmahia). Kenya × USA.*
