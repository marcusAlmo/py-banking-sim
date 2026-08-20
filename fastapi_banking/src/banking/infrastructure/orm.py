"""
SQLAlchemy ORM models.

These are *persistence* representations, not domain objects. They live
in the infrastructure layer and are translated to/from the pure domain
`Account` / `Transaction` classes inside `account_repository.py`.

Keeping ORM models separate from domain entities (rather than annotating
the domain classes with `Mapped[...]`) is a deliberate DDD choice: it
lets the domain stay framework-agnostic and means a switch to a
different ORM or storage engine would touch only this layer.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models in this project."""


class AccountModel(Base):
    __tablename__ = "accounts"

    # The 10-digit account number is the natural primary key.
    number: Mapped[str] = mapped_column(String(10), primary_key=True)
    holder: Mapped[str] = mapped_column(String(120), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pin: Mapped[str] = mapped_column(String(4), nullable=False)


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
