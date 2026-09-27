from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = "New chat"
    job_type: str = "ask_scene"


class SessionUpdate(BaseModel):
    title: str


class AssetOut(BaseModel):
    id: UUID
    filename: str
    content_type: str
    gcs_uri: str
    preview_gcs_uri: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    preview_png_base64: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: UUID
    title: str
    job_type: str
    created_at: datetime
    updated_at: datetime
    assets: list[AssetOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    id: UUID
    title: str
    job_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageAttachmentOut(BaseModel):
    id: UUID
    filename: str
    preview_png_base64: str | None = None


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    asset_id: UUID | None = None
    attachment: MessageAttachmentOut | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class SendMessageResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


class UploadAssetResponse(BaseModel):
    asset: AssetOut
    user_message: MessageOut
    assistant_message: MessageOut
