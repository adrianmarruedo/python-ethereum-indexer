from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.sql import and_, or_
from ...db_utils import DBSession

from . import Balance
from src.models import BalanceModel


def _balance_orm_to_model(balance: Dict) -> BalanceModel:
    """Low overhead ORM Balance to pydantic BalanceModel"""
    model = BalanceModel(
        chain_id=balance.chain_id,
        token_address=balance.token_address,
        wallet_address=balance.wallet_address,
        balance=balance.balance
    )
    return model


def get_token_top_holders(
    chain_id: int,
    token_address: str,
    limit: int = 100,
) -> List[BalanceModel]:
    """Returns the list of top Balances for the specified chain_id-token_address

    :param chain_id: chain ID
    :param token_address: Token Address
    :param limit: Optional. limit of holders to retrieve
    :return : List of Transfers"""
    try:
        session_maker = DBSession.get_db()
        with session_maker.begin() as session:
            statement = (
                select(Balance)
                .filter_by(chain_id=chain_id)
                .filter_by(token_address=token_address.lower())
                .order_by(Balance.balance.desc())
                .limit(limit)
            )
            balances_orm = session.execute(statement).scalars().all()

            balances = [
                _balance_orm_to_model(balance_orm) for balance_orm in balances_orm
            ]

        return balances
    except Exception as e:
        raise e

