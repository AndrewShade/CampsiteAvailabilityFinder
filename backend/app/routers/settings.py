from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import NotificationWebhook
from ..schemas import AppSettings, WebhookCreate, WebhookOut, WebhookUpdate
from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/app", response_model=AppSettings)
def get_app_settings():
    return AppSettings(
        check_interval_minutes=settings.check_interval_minutes,
        ridb_api_key_configured=bool(settings.ridb_api_key),
    )


@router.get("/webhooks", response_model=list[WebhookOut])
def list_webhooks(db: Session = Depends(get_db)):
    return db.query(NotificationWebhook).order_by(NotificationWebhook.created_at).all()


@router.post("/webhooks", response_model=WebhookOut, status_code=201)
def create_webhook(body: WebhookCreate, db: Session = Depends(get_db)):
    webhook = NotificationWebhook(**body.model_dump())
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.patch("/webhooks/{webhook_id}", response_model=WebhookOut)
def update_webhook(webhook_id: int, body: WebhookUpdate, db: Session = Depends(get_db)):
    webhook = _get_or_404(webhook_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(webhook, field, value)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/webhooks/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    webhook = _get_or_404(webhook_id, db)
    db.delete(webhook)
    db.commit()


def _get_or_404(webhook_id: int, db: Session) -> NotificationWebhook:
    webhook = db.get(NotificationWebhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    return webhook
