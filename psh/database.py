import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Float, Date, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from dotenv import load_dotenv

load_dotenv()
URL=os.getenv('DATABASE_URL','sqlite:///./psh.db')
engine=create_engine(URL,connect_args={'check_same_thread':False} if URL.startswith('sqlite') else {},pool_pre_ping=True)
SessionLocal=sessionmaker(engine,expire_on_commit=False)

class Base(DeclarativeBase): pass

class Dataset(Base):
    __tablename__='datasets'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    name: Mapped[str]=mapped_column(String(200))
    sha256: Mapped[str]=mapped_column(String(64))
    source: Mapped[str]=mapped_column(String(200))
    assets: Mapped[list]=mapped_column(JSON)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class Observation(Base):
    __tablename__='daily_returns'
    dataset_id: Mapped[str]=mapped_column(ForeignKey('datasets.id'),primary_key=True)
    date: Mapped[datetime]=mapped_column(Date,primary_key=True)
    asset: Mapped[str]=mapped_column(String(100),primary_key=True)
    value: Mapped[float]=mapped_column(Float)

class Run(Base):
    __tablename__='experiment_runs'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    dataset_id: Mapped[str]=mapped_column(ForeignKey('datasets.id'),index=True)
    report: Mapped[dict]=mapped_column(JSON)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class Allocation(Base):
    __tablename__='allocations'
    run_id: Mapped[str]=mapped_column(ForeignKey('experiment_runs.id'),primary_key=True)
    method: Mapped[str]=mapped_column(String(80),primary_key=True)
    asset: Mapped[str]=mapped_column(String(100),primary_key=True)
    weight: Mapped[float]=mapped_column(Float)

def init_db(): Base.metadata.create_all(engine)
