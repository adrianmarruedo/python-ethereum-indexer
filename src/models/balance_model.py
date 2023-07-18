from __future__ import annotations

from typing import Optional
from typing_extensions import TypeAlias
from decimal import Decimal
from pydantic import BaseModel

Hex: TypeAlias = str  # Explicitly note this is a hex value for ETL pipelines to handle
Address: TypeAlias = str


class BalanceModel(BaseModel):
    chain_id: int
    wallet_address: Address
    token_address: Address
    token_id: Optional[str]
    token_key: Optional[str]
    balance: Decimal
