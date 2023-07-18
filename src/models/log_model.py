from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from typing_extensions import TypeAlias
from pydantic import BaseModel

Hex: TypeAlias = str  # Explicitly note this is a hex value for ETL pipelines to handle
Address: TypeAlias = str


class LogModel(BaseModel):
    chain_id: int
    block_num: int
    block_hash: Hex
    address: Address
    topic: Optional[Hex]
    topics: List[Hex]
    data: Hex
    transaction_hash: Hex
    log_index: int
    deleted: bool
    block_time: Optional[datetime]
