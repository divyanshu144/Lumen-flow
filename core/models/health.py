from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base

class HealthCheck(Base):
    __tablename__ = "healthcheck"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), default="ok")
