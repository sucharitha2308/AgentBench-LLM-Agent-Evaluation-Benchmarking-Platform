from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class ProviderCredential(Base, TimestampMixin):
    __tablename__ = "provider_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "openai", "gemini"
    key_alias: Mapped[str] = mapped_column(String(100), default="Default Key", nullable=False)
    encrypted_api_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="credentials")
