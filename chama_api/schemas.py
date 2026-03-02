"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Chama ──────────────────────────────────────────────────────
class ChamaCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, example="Umoja Investment Group")
    cycle_frequency: str = Field(..., example="monthly",
                                  description="weekly | biweekly | monthly | quarterly")
    contribution_kes: float = Field(..., gt=0, example=5000)
    meeting_day: str = Field(..., example="Last Saturday")
    paybill: Optional[str] = Field(None, example="522533")

    @field_validator("cycle_frequency")
    @classmethod
    def valid_frequency(cls, v: str) -> str:
        allowed = {"weekly", "biweekly", "monthly", "quarterly"}
        if v.lower() not in allowed:
            raise ValueError(f"cycle_frequency must be one of {allowed}")
        return v.lower()


class ChamaUpdate(BaseModel):
    name: Optional[str] = None
    contribution_kes: Optional[float] = Field(None, gt=0)
    meeting_day: Optional[str] = None
    paybill: Optional[str] = None
    status: Optional[str] = Field(None, description="active | suspended | dissolved")


class ChamaOut(BaseModel):
    id: str
    name: str
    cycle_frequency: str
    contribution_kes: float
    meeting_day: str
    paybill: Optional[str]
    status: str
    created_at: datetime
    member_count: int = 0


# ── Member ─────────────────────────────────────────────────────
class MemberCreate(BaseModel):
    full_name: str = Field(..., min_length=2, example="Jane Wanjiku")
    phone: str = Field(..., example="254712345678",
                       description="E.164 without +, e.g. 254712345678")
    role: str = Field("member", example="member",
                      description="chairperson | treasurer | secretary | auditor | member")
    join_date: date = Field(default_factory=date.today)

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        p = v.strip().lstrip("+")
        if p.startswith("07") or p.startswith("01"):
            p = "254" + p[1:]
        elif len(p) == 9 and p[0] == "7":
            p = "254" + p
        if not (p.startswith("254") and p.isdigit() and len(p) == 12):
            raise ValueError("Phone must be E.164 format without +, e.g. 254712345678")
        return p

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        allowed = {"chairperson", "treasurer", "secretary", "auditor", "member"}
        if v.lower() not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v.lower()


class MemberOut(BaseModel):
    id: str
    chama_id: str
    full_name: str
    phone: str
    role: str
    join_date: date
    is_active: bool
    contribution_count: int = 0
    compliance_rate: float = 0.0


# ── Contribution ───────────────────────────────────────────────
class ContributionCreate(BaseModel):
    member_id: str
    amount: float = Field(..., gt=0, example=5000)
    cycle_date: date
    status: str = Field("confirmed", description="confirmed | pending | failed | waived")
    mpesa_receipt: Optional[str] = Field(None, example="NLJ7RT61SV",
                                         description="M-Pesa receipt — used for idempotency")

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"confirmed", "pending", "failed", "waived"}
        if v.lower() not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v.lower()


class ContributionOut(BaseModel):
    id: str
    chama_id: str
    member_id: str
    amount: float
    cycle_date: date
    status: str
    mpesa_receipt: Optional[str]
    recorded_at: datetime


class PagedContributions(BaseModel):
    items: list[ContributionOut]
    total: int
    limit: int
    offset: int


# ── Loan ───────────────────────────────────────────────────────
class LoanCreate(BaseModel):
    member_id: str
    principal: float = Field(..., gt=0, example=15000)
    interest_rate: float = Field(..., gt=0, le=1.0, example=0.10,
                                  description="Monthly rate as decimal, e.g. 0.10 = 10%")
    term_months: int = Field(..., gt=0, le=60, example=3)
    disbursed_date: date = Field(default_factory=date.today)


class LoanOut(BaseModel):
    id: str
    chama_id: str
    member_id: str
    principal: float
    interest_rate: float
    term_months: int
    disbursed_date: date
    due_date: date
    status: str
    amount_repaid: float
    total_repayable: float
    outstanding: float


class ErrorOut(BaseModel):
    detail: str
