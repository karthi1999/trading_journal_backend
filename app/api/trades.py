import secrets
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import account as crud_account
from app.crud import attachment as crud_attachment
from app.crud import trade as crud_trade
from app.db import get_db
from app.models import MarketType, TradeSide, TradeStatus
from app.schemas.attachment import AttachmentResponse
from app.schemas.trade import TradeCreate, TradeResponse, TradeUpdate

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_MAX_BYTES = 8 * 1024 * 1024  # 8 MB
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    account_id: str | None = None,
    verified: bool | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[TradeResponse]:
    items = await crud_trade.list_for_user(
        db,
        user_id=user.id,
        account_id=account_id,
        verified=verified,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return [TradeResponse.from_model(t) for t in items]


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    payload: TradeCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeResponse:
    account = await crud_account.get(db, payload.account_id)
    if not account or account.user_id != user.id:
        raise HTTPException(status_code=400, detail="Invalid account")

    t = await crud_trade.create(
        db,
        user_id=user.id,
        account_id=payload.account_id,
        strategy_id=payload.strategy_id,
        journal_id=payload.journal_id,
        symbol=payload.symbol.upper(),
        side=TradeSide(payload.side),
        status=TradeStatus(payload.status),
        quantity=payload.quantity,
        entry_price=payload.entry_price,
        exit_price=payload.exit_price,
        pnl=payload.pnl,
        commission=payload.commission,
        currency=payload.currency,
        market=MarketType(payload.market),
        notes=payload.notes,
        tags=payload.tags,
        is_verified=payload.is_verified,
        opened_at=payload.opened_at,
        closed_at=payload.closed_at,
    )
    return TradeResponse.from_model(t)


@router.patch("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str,
    payload: TradeUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeResponse:
    existing = await crud_trade.get(db, trade_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    fields = payload.model_dump(exclude_unset=True)
    if "symbol" in fields and isinstance(fields["symbol"], str):
        fields["symbol"] = fields["symbol"].upper()
    if "side" in fields and fields["side"] is not None:
        fields["side"] = TradeSide(fields["side"])
    if "status" in fields and fields["status"] is not None:
        fields["status"] = TradeStatus(fields["status"])
    if "market" in fields and fields["market"] is not None:
        fields["market"] = MarketType(fields["market"])

    # Setting an exit time implies the trade is closed (unless caller overrode status).
    if "closed_at" in fields and fields["closed_at"] is not None and "status" not in fields:
        fields["status"] = TradeStatus.CLOSED

    t = await crud_trade.update(db, existing, fields)
    return TradeResponse.from_model(t)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(
    trade_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    existing = await crud_trade.get(db, trade_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    await crud_trade.delete(db, existing)


@router.get("/{trade_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    trade_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AttachmentResponse]:
    t = await crud_trade.get(db, trade_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    items = await crud_attachment.list_for_trade(db, trade_id)
    return [AttachmentResponse.from_model(a) for a in items]


@router.post(
    "/{trade_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    trade_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentResponse:
    t = await crud_trade.get(db, trade_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )

    contents = await file.read()
    if len(contents) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {_MAX_BYTES // (1024 * 1024)} MB limit",
        )

    suffix = Path(file.filename or "").suffix.lower() or ".bin"
    stored_name = f"{secrets.token_hex(16)}{suffix}"
    dest = _UPLOAD_DIR / stored_name
    dest.write_bytes(contents)

    attachment = await crud_attachment.create(
        db,
        trade_id=trade_id,
        user_id=user.id,
        url=f"/uploads/{stored_name}",
        filename=file.filename or stored_name,
        mime_type=file.content_type,
        size_bytes=len(contents),
    )
    return AttachmentResponse.from_model(attachment)


@router.delete(
    "/{trade_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    trade_id: str,
    attachment_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    a = await crud_attachment.get(db, attachment_id)
    if not a or a.user_id != user.id or a.trade_id != trade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
        )

    # Best-effort cleanup of the file on disk; DB row removal is the source of truth.
    if a.url.startswith("/uploads/"):
        file_path = _UPLOAD_DIR / a.url.rsplit("/", 1)[-1]
        if file_path.exists():
            file_path.unlink(missing_ok=True)

    await crud_attachment.delete(db, a)
