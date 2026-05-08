from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.db import prisma
from app.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyResponse])
async def list_strategies(user=Depends(get_current_user)) -> list[StrategyResponse]:
    items = await prisma.strategy.find_many(
        where={"userId": user.id}, order={"createdAt": "desc"}
    )
    return [StrategyResponse.from_model(s) for s in items]


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    payload: StrategyCreate, user=Depends(get_current_user)
) -> StrategyResponse:
    s = await prisma.strategy.create(
        data={
            "userId": user.id,
            "name": payload.name,
            "description": payload.description,
            "entryCriteria": payload.entry_criteria,
            "exitCriteria": payload.exit_criteria,
        }
    )
    return StrategyResponse.from_model(s)


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str, payload: StrategyUpdate, user=Depends(get_current_user)
) -> StrategyResponse:
    existing = await prisma.strategy.find_unique(where={"id": strategy_id})
    if not existing or existing.userId != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    field_map = {
        "name": "name",
        "description": "description",
        "entry_criteria": "entryCriteria",
        "exit_criteria": "exitCriteria",
    }
    data = {
        field_map[k]: v for k, v in payload.model_dump(exclude_unset=True).items() if k in field_map
    }
    s = await prisma.strategy.update(where={"id": strategy_id}, data=data)
    return StrategyResponse.from_model(s)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(strategy_id: str, user=Depends(get_current_user)) -> None:
    existing = await prisma.strategy.find_unique(where={"id": strategy_id})
    if not existing or existing.userId != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    await prisma.strategy.delete(where={"id": strategy_id})
