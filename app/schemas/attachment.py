from datetime import datetime

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    url: str
    filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    @classmethod
    def from_model(cls, a) -> "AttachmentResponse":
        return cls(
            id=a.id,
            url=a.url,
            filename=a.filename,
            mime_type=a.mime_type,
            size_bytes=a.size_bytes,
            created_at=a.created_at,
        )
