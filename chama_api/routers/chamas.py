from __future__ import annotations
from fastapi import APIRouter, HTTPException
from chama_api.schemas import ChamaCreate, ChamaUpdate, ChamaOut
from chama_api.store import store

router = APIRouter()


@router.post("/", response_model=ChamaOut, status_code=201, summary="Create a chama")
async def create_chama(body: ChamaCreate):
    record = store.create_chama(
        name=body.name,
        cycle_frequency=body.cycle_frequency,
        contribution_kes=body.contribution_kes,
        meeting_day=body.meeting_day,
        paybill=body.paybill,
        status="active",
    )
    members = store.list_members(record.id)
    return ChamaOut(**record.__dict__, member_count=len(members))


@router.get("/", response_model=list[ChamaOut], summary="List all chamas")
async def list_chamas():
    return [
        ChamaOut(**r.__dict__, member_count=len(store.list_members(r.id)))
        for r in store.list_chamas()
    ]


@router.get("/{chama_id}", response_model=ChamaOut, summary="Get a chama")
async def get_chama(chama_id: str):
    r = store.get_chama(chama_id)
    if not r:
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    return ChamaOut(**r.__dict__, member_count=len(store.list_members(r.id)))


@router.patch("/{chama_id}", response_model=ChamaOut, summary="Update a chama")
async def update_chama(chama_id: str, body: ChamaUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    r = store.update_chama(chama_id, **updates)
    if not r:
        raise HTTPException(404, f"Chama {chama_id!r} not found")
    return ChamaOut(**r.__dict__, member_count=len(store.list_members(r.id)))
