"""SQLAlchemy models mirroring the Prisma schema."""
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deliver_web = Column(Boolean, default=True)
    deliver_telegram = Column(Boolean, default=False)
    deliver_kakao = Column(Boolean, default=False)

    telegram_chat_id = Column(String, nullable=True)
    kakao_access_token = Column(String, nullable=True)
    kakao_refresh_token = Column(String, nullable=True)
    push_subscription = Column(Text, nullable=True)

    resolutions = Column(Text, nullable=True)  # '나의 다짐' (매일 텔레그램 발송)

    template_id = Column(String, default="compact")
    schedule_hour = Column(Integer, default=8)
    schedule_minute = Column(Integer, default=0)
    timezone = Column(String, default="Asia/Seoul")
    plan_id = Column(String, nullable=True)

    sources = relationship("Source", back_populates="user")
    delivery_logs = relationship("DeliveryLog", back_populates="user")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    category = Column(String, default="기타")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_crawled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sources")
    articles = relationship("Article", back_populates="source")

    __table_args__ = (
        UniqueConstraint("user_id", "url"),
    )


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    content_hash = Column(String, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    date = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    pdf_urls = Column(JSON, default=[])
    crawled_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", back_populates="articles")
    delivery_logs = relationship("DeliveryLog", back_populates="article")

    __table_args__ = (
        UniqueConstraint("source_id", "content_hash"),
        Index("ix_articles_source_crawled", "source_id", "crawled_at"),
    )


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(String, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False)
    status = Column(String, default="pending")
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="delivery_logs")
    article = relationship("Article", back_populates="delivery_logs")

    __table_args__ = (
        Index("ix_delivery_logs_user_created", "user_id", "created_at"),
    )
