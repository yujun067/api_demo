from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.config import Base


class HackerNewsItem(Base):
    """SQLAlchemy model for Hacker News items."""

    __tablename__ = "hacker_news_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=True)
    score = Column(Integer, nullable=True, index=True)
    author = Column(String(100), nullable=True, index=True)
    timestamp = Column(Integer, nullable=True, index=True)
    descendants = Column(Integer, nullable=True)
    type = Column(String(50), nullable=True, index=True)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<HackerNewsItem(id={self.id}, title='{self.title[:50]}...')>"
