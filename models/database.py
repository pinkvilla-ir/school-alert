# models/database.py
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User account for school alert system."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    family_contexts = relationship("FamilyContext", back_populates="user", cascade="all, delete-orphan")
    gmail_tokens = relationship("GmailToken", back_populates="user", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="user", cascade="all, delete-orphan")
    notification_logs = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class FamilyContext(Base):
    """Family configuration per user (children, schools, important senders, keywords)."""
    __tablename__ = "family_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # JSONB fields for flexible schema
    children_json = Column(JSONB, nullable=False, default=[])
    # Example: [{"name": "Rishi", "grade": "KG", "school": "Rosa Lee Carter"}]
    
    important_senders_json = Column(JSONB, nullable=False, default=[])
    # Example: ["coach@soccer.com", "teacher@school.edu"]
    
    keywords_json = Column(JSONB, nullable=False, default=[])
    # Example: ["cancelled", "emergency", "permission slip", "early dismissal"]
    
    timezone = Column(String(50), default="America/New_York", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="family_contexts")

    __table_args__ = (
        Index("ix_family_contexts_children", "children_json", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<FamilyContext user_id={self.user_id}>"


class GmailToken(Base):
    """Encrypted Gmail OAuth tokens per user."""
    __tablename__ = "gmail_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Fernet-encrypted token and refresh_token
    encrypted_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=False)
    
    gmail_address = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="gmail_tokens")

    __table_args__ = (
        Index("ix_gmail_tokens_user_email", "user_id", "gmail_address"),
    )

    def __repr__(self):
        return f"<GmailToken user_id={self.user_id} email={self.gmail_address}>"


class EmailLog(Base):
    """Log of all processed emails for analytics and debugging."""
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    gmail_message_id = Column(String(255), nullable=False, unique=True)
    subject = Column(Text, nullable=False)
    sender = Column(String(255), nullable=False)
    
    # Claude scoring
    urgency_score = Column(Integer, nullable=False)  # 1-5
    action_today = Column(Boolean, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    
    notification_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_logs")
    notification_logs = relationship("NotificationLog", back_populates="email_log", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_email_logs_user_created", "user_id", "created_at"),
        Index("ix_email_logs_urgency", "urgency_score"),
    )

    def __repr__(self):
        return f"<EmailLog user_id={self.user_id} urgency={self.urgency_score}>"


class NotificationLog(Base):
    """Log of all sent notifications (success/failure/retry)."""
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email_log_id = Column(UUID(as_uuid=True), ForeignKey("email_logs.id", ondelete="CASCADE"), nullable=False)
    
    notification_type = Column(String(50), nullable=False)  # "pushover" or "ntfy"
    status = Column(String(50), nullable=False)  # "sent", "failed", "retry"
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_logs")
    email_log = relationship("EmailLog", back_populates="notification_logs")

    __table_args__ = (
        Index("ix_notification_logs_user_created", "user_id", "created_at"),
        Index("ix_notification_logs_status", "status"),
    )

    def __repr__(self):
        return f"<NotificationLog user_id={self.user_id} status={self.status}>"