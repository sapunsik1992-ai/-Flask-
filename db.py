from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

engine = create_engine("sqlite:///ads.db", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    owner = Column(String, nullable=False)

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "owner": self.owner,
        }


Base.metadata.create_all(engine)
