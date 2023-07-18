from sqlalchemy import Column
from sqlalchemy.types import Integer, String, DateTime, DECIMAL, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint

from ... import Base


class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, nullable=False)
    wallet_address = Column(String(255), nullable=False)
    balance = Column(DECIMAL(54, 18), nullable=False)
    token_address = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    UniqueConstraint('token_address', 'wallet_address', name='token_wallet_1')
