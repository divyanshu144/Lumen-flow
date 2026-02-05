from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Column, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.db import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="contact")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # session key for web chat; later can be user_id/contact_id
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="web")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contact: Mapped["Contact | None"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)

    role: Mapped[str] = mapped_column(String(20))  # user/assistant/system
    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)

    status: Mapped[str] = mapped_column(String(30), default="new")  # new/contacted/won/lost
    score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events = relationship(
        "LeadEvent",
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="LeadEvent.created_at",
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)

    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high
    status: Mapped[str] = mapped_column(String(30), default="open")  # open/in_progress/closed
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LeadEvent(Base):
    __tablename__ = "lead_events"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    # event types: status_changed, score_changed, note_added, system_draft, etc.
    event_type = Column(String(50), nullable=False)

    # optional structured info
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)

    # free text note (human or system)
    note = Column(Text, nullable=True)

    # who wrote it: "user", "agent", "system", "admin"
    actor = Column(String(50), nullable=False, default="system")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="events")


class AutomationDraft(Base):
    __tablename__ = "automation_drafts"

    id = Column(Integer, primary_key=True, index=True)

    # what kind of draft is this?
    kind = Column(String(50), nullable=False)  # "lead_followup" | "ticket_reply"

    # link to entity
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)

    # optional linking
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)

    status = Column(String(30), nullable=False, default="pending")  # pending|approved|rejected|sent
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # relationships (optional)
    lead = relationship("Lead", backref="drafts", lazy="joined")
    ticket = relationship("Ticket", backref="drafts", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    conversation = relationship("Conversation", lazy="joined")


class LeadScoreRule(Base):
    __tablename__ = "lead_score_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    field: Mapped[str] = mapped_column(String(50))  # summary | status
    operator: Mapped[str] = mapped_column(String(20))  # contains | equals
    value: Mapped[str] = mapped_column(String(255))
    points: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
