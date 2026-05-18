from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import strategy as crud_strategy
from app.db import get_db
from app.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyResponse])
async def list_strategies(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[StrategyResponse]:
    items = await crud_strategy.list_for_user(db, user.id)
    return [StrategyResponse.from_model(s) for s in items]


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    payload: StrategyCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StrategyResponse:
    s = await crud_strategy.create(
        db,
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        entry_criteria=payload.entry_criteria,
        exit_criteria=payload.exit_criteria,
    )
    return StrategyResponse.from_model(s)


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    payload: StrategyUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StrategyResponse:
    existing = await crud_strategy.get(db, strategy_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    fields = payload.model_dump(exclude_unset=True)
    s = await crud_strategy.update(db, existing, fields)
    return StrategyResponse.from_model(s)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    existing = await crud_strategy.get(db, strategy_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    await crud_strategy.delete(db, existing)
