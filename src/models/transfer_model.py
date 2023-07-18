from __future__ import annotations

from typing import Optional
from typing_extensions import TypeAlias
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

Hex: TypeAlias = str  # Explicitly note this is a hex value for ETL pipelines to handle
Address: TypeAlias = str


class TransferModel(BaseModel):
    chain_id: int
    block_num: int
    tx_hash: str
    tx_from: Address
    tx_to: Address
    value: Decimal
    type: str
    token_address: Address
    token_id: Optional[str]
    token_key: Optional[str]
    block_time: Optional[datetime]