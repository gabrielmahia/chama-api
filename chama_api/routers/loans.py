from __future__ import annotations
from datetime import timedelta
from fastapi import APIRouter, HTTPException
from chama_api.schemas import LoanCreate, LoanOut
from chama_api.store import store

router = APIRouter()


def _loan_out(r) -> LoanOut:
    total = r.principal * (1 + r.interest_rate * r.term_months)
    return LoanOut(
        **{k: v for k, v in r.__dict__.items() if k not in ("amount_repaid",)},
        amount_repaid=r.amount_repaid,
        total_repayable=round(total, 2),
        outstanding=round(total - r.amount_repaid, 2),
    )


@router.post("/{chama_id}/loans", response_model=LoanOut, status_code=201, summary="Issue a loan")
async def issue_loan(chama_id: str, body: LoanCreate):
    if not store.get_chama(chama_id):
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    if not store.get_member(body.member_id):
        raise HTTPException(404, f"Member {body.member_id!r} not found")
    active = [l for l in store.list_loans(chama_id, status="active")
              if l.member_id == body.member_id]
    if active:
        raise HTTPException(409, f"Member {body.member_id!r} already has an active loan.")
    due = body.disbursed_date + timedelta(days=30 * body.term_months)
    r = store.create_loan(
        chama_id=chama_id,
        member_id=body.member_id,
        principal=body.principal,
        interest_rate=body.interest_rate,
        term_months=body.term_months,
        disbursed_date=body.disbursed_date,
        due_date=due,
    )
    return _loan_out(r)


@router.get("/{chama_id}/loans", response_model=list[LoanOut], summary="List loans")
async def list_loans(chama_id: str, status: str | None = None):
    if not store.get_chama(chama_id):
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    return [_loan_out(r) for r in store.list_loans(chama_id, status=status)]


@router.get("/{chama_id}/loans/{loan_id}", response_model=LoanOut, summary="Get a loan")
async def get_loan(chama_id: str, loan_id: str):
    r = store.get_loan(loan_id)
    if not r or r.chama_id != chama_id:
        raise HTTPException(404, f"Loan {loan_id!r} not found")
    return _loan_out(r)
