"""In-memory store — replaces a real database for demo and testing."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class ChamaRecord:
    id: str
    name: str
    cycle_frequency: str
    contribution_kes: float
    meeting_day: str
    paybill: Optional[str]
    status: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MemberRecord:
    id: str
    chama_id: str
    full_name: str
    phone: str
    role: str
    join_date: date
    is_active: bool = True


@dataclass
class ContributionRecord:
    id: str
    chama_id: str
    member_id: str
    amount: float
    cycle_date: date
    status: str
    mpesa_receipt: Optional[str]
    recorded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LoanRecord:
    id: str
    chama_id: str
    member_id: str
    principal: float
    interest_rate: float
    term_months: int
    disbursed_date: date
    due_date: date
    status: str = "active"
    amount_repaid: float = 0.0


class Store:
    """Thread-safe in-memory data store.

    For production: replace each method body with DB queries.
    The interface is intentionally thin — CRUD + filters.
    """

    def __init__(self):
        self._chamas:        dict[str, ChamaRecord]        = {}
        self._members:       dict[str, MemberRecord]       = {}
        self._contributions: dict[str, ContributionRecord] = {}
        self._loans:         dict[str, LoanRecord]         = {}

    # ── Chamas ───────────────────────────────────────────────
    def create_chama(self, **kwargs) -> ChamaRecord:
        r = ChamaRecord(id=str(uuid.uuid4()), **kwargs)
        self._chamas[r.id] = r
        return r

    def get_chama(self, chama_id: str) -> Optional[ChamaRecord]:
        return self._chamas.get(chama_id)

    def list_chamas(self) -> list[ChamaRecord]:
        return list(self._chamas.values())

    def update_chama(self, chama_id: str, **kwargs) -> Optional[ChamaRecord]:
        r = self._chamas.get(chama_id)
        if not r:
            return None
        for k, v in kwargs.items():
            if hasattr(r, k):
                setattr(r, k, v)
        return r

    # ── Members ──────────────────────────────────────────────
    def create_member(self, **kwargs) -> MemberRecord:
        r = MemberRecord(id=str(uuid.uuid4()), **kwargs)
        self._members[r.id] = r
        return r

    def get_member(self, member_id: str) -> Optional[MemberRecord]:
        return self._members.get(member_id)

    def list_members(self, chama_id: str, active_only: bool = True) -> list[MemberRecord]:
        ms = [m for m in self._members.values() if m.chama_id == chama_id]
        if active_only:
            ms = [m for m in ms if m.is_active]
        return ms

    # ── Contributions ─────────────────────────────────────────
    def create_contribution(self, **kwargs) -> ContributionRecord:
        r = ContributionRecord(id=str(uuid.uuid4()), **kwargs)
        self._contributions[r.id] = r
        return r

    def get_contribution(self, contribution_id: str) -> Optional[ContributionRecord]:
        return self._contributions.get(contribution_id)

    def list_contributions(
        self,
        chama_id: str,
        member_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContributionRecord], int]:
        cs = [c for c in self._contributions.values() if c.chama_id == chama_id]
        if member_id:
            cs = [c for c in cs if c.member_id == member_id]
        if status:
            cs = [c for c in cs if c.status == status]
        cs.sort(key=lambda x: x.recorded_at, reverse=True)
        return cs[offset : offset + limit], len(cs)

    def receipt_exists(self, receipt: str) -> bool:
        return any(c.mpesa_receipt == receipt for c in self._contributions.values())

    # ── Loans ─────────────────────────────────────────────────
    def create_loan(self, **kwargs) -> LoanRecord:
        r = LoanRecord(id=str(uuid.uuid4()), **kwargs)
        self._loans[r.id] = r
        return r

    def get_loan(self, loan_id: str) -> Optional[LoanRecord]:
        return self._loans.get(loan_id)

    def list_loans(self, chama_id: str, status: Optional[str] = None) -> list[LoanRecord]:
        ls = [l for l in self._loans.values() if l.chama_id == chama_id]
        if status:
            ls = [l for l in ls if l.status == status]
        return ls


# Module-level store — replace with dependency injection in production
store = Store()
