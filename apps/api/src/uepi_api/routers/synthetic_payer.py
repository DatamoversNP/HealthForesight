"""Local synthetic-payer identity and population what-if. Reads only the connected database."""

from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.database import get_db
from uepi_api.services.synthetic_whatif import (
    WhatIfRejected,
    dataset_identity,
    execute_synthetic_whatif,
)

router = APIRouter()


class SyntheticWhatIfRequest(BaseModel):
    policy_id: UUID
    policy_ids: Optional[List[UUID]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


@router.get("/synthetic-payer/identity")
async def get_synthetic_payer_identity(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    return dataset_identity(db, current_user.tenant_id)


@router.post("/synthetic-payer/what-if")
async def post_synthetic_whatif(
    body: SyntheticWhatIfRequest,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    try:
        return execute_synthetic_whatif(
            db,
            current_user.tenant_id,
            body.policy_id,
            body.parameters,
            body.policy_ids,
        )
    except WhatIfRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
