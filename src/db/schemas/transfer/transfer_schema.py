from sqlalchemy import Column
from sqlalchemy.types import Integer, String, DateTime, DECIMAL, BIGINT
from sqlalchemy.sql import func

from ... import Base


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, nullable=False)
    block_num = Column(Integer, nullable=False)
    tx_hash = Column(String(255), nullable=False)
    tx_from = Column(String(255), nullable=False)
    tx_to = Column(String(255), nullable=False)
    value = Column(DECIMAL(54, 18), nullable=False)
    type = Column(String(255), nullable=False)
    token_address = Column(String(255), nullable=False)
    block_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
