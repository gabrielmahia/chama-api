from __future__ import annotations
from fastapi import APIRouter, HTTPException
from chama_api.schemas import MemberCreate, MemberOut
from chama_api.store import store

router = APIRouter()


@router.post("/{chama_id}/members", response_model=MemberOut, status_code=201, summary="Add a member")
async def add_member(chama_id: str, body: MemberCreate):
    if not store.get_chama(chama_id):
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    r = store.create_member(
        chama_id=chama_id,
        full_name=body.full_name,
        phone=body.phone,
        role=body.role,
        join_date=body.join_date,
    )
    contribs, _ = store.list_contributions(chama_id, member_id=r.id)
    settled = sum(1 for c in contribs if c.status in ("confirmed", "waived"))
    rate = round(settled / len(contribs) * 100, 1) if contribs else 0.0
    return MemberOut(**r.__dict__, contribution_count=len(contribs), compliance_rate=rate)


@router.get("/{chama_id}/members", response_model=list[MemberOut], summary="List members")
async def list_members(chama_id: str, active_only: bool = True):
    if not store.get_chama(chama_id):
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    members = store.list_members(chama_id, active_only=active_only)
    result = []
    for m in members:
        contribs, _ = store.list_contributions(chama_id, member_id=m.id)
        settled = sum(1 for c in contribs if c.status in ("confirmed", "waived"))
        rate = round(settled / len(contribs) * 100, 1) if contribs else 0.0
        result.append(MemberOut(**m.__dict__, contribution_count=len(contribs), compliance_rate=rate))
    return result


@router.get("/{chama_id}/members/{member_id}", response_model=MemberOut, summary="Get a member")
async def get_member(chama_id: str, member_id: str):
    m = store.get_member(member_id)
    if not m or m.chama_id != chama_id:
        raise HTTPException(404, f"Member {member_id!r} not found in chama {chama_id!r}")
    contribs, _ = store.list_contributions(chama_id, member_id=m.id)
    settled = sum(1 for c in contribs if c.status in ("confirmed", "waived"))
    rate = round(settled / len(contribs) * 100, 1) if contribs else 0.0
    return MemberOut(**m.__dict__, contribution_count=len(contribs), compliance_rate=rate)
