from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from chama_api.schemas import ContributionCreate, ContributionOut, PagedContributions
from chama_api.store import store
from datetime import datetime

router = APIRouter()


@router.post(
    "/{chama_id}/contributions",
    response_model=ContributionOut,
    status_code=201,
    summary="Record a contribution",
)
async def record_contribution(chama_id: str, body: ContributionCreate):
    if not store.get_chama(chama_id):
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    if not store.get_member(body.member_id):
        raise HTTPException(404, f"Member {body.member_id!r} not found")
    # Idempotency: reject duplicate M-Pesa receipts
    if body.mpesa_receipt and store.receipt_exists(body.mpesa_receipt):
        raise HTTPException(
            409,
            f"Receipt {body.mpesa_receipt!r} already recorded. Duplicate rejected.",
        )
    r = store.create_contribution(
        chama_id=chama_id,
        member_id=body.member_id,
        amount=body.amount,
        cycle_date=body.cycle_date,
        status=body.status,
        mpesa_receipt=body.mpesa_receipt,
        recorded_at=datetime.utcnow(),
    )
    return ContributionOut(**r.__dict__)


@router.get(
    "/{chama_id}/contributions",
    response_model=PagedContributions,
    summary="List contributions with pagination",
)
async def list_contributions(
    chama_id: str,
    member_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not store.get_chama(chama_id):
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    items, total = store.list_contributions(chama_id, member_id=member_id,
                                            status=status, limit=limit, offset=offset)
    return PagedContributions(
        items=[ContributionOut(**c.__dict__) for c in items],
        total=total, limit=limit, offset=offset,
    )


@router.get(
    "/{chama_id}/contributions/{contribution_id}",
    response_model=ContributionOut,
    summary="Get a contribution",
)
async def get_contribution(chama_id: str, contribution_id: str):
    r = store.get_contribution(contribution_id)
    if not r or r.chama_id != chama_id:
        raise HTTPException(404, f"Contribution {contribution_id!r} not found")
    return ContributionOut(**r.__dict__)
