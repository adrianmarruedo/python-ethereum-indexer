from __future__ import annotations

import logging
from typing import List, Dict
from decimal import Decimal

from sqlalchemy import delete, insert

from ...db_utils import DBSession
from . import Balance

from src.models import BalanceModel


def _balance_model_to_dict(balance: BalanceModel) -> Dict:
    """Low overhead pydantic BalanceModel to dict"""
    return {
        "chain_id": balance.chain_id,
        "wallet_address": balance.wallet_address.lower(),
        "token_address": balance.token_address.lower(),
        "balance": balance.balance,
    }


def insert_balances(chain_id: int, balances: List[BalanceModel]) -> None:
    """SQLTransaction containing List[BalanceModel] INSERT

    :param chain_id: chain ID
    :param balances: List of balances to Upsert
    :return : None
    """
    if len(balances) == 0:
        logging.warning("No balances provided")
        return
    balances_dict = [_balance_model_to_dict(tx) for tx in balances]

    engine = DBSession.get_engine()
    with engine.connect() as conn:
        try:
            # Insert
            insert_stmt = insert(Balance)
            conn.execute(insert_stmt, balances_dict)
            conn.commit()

        except Exception as e:
            conn.rollback()
            logging.warning(f"did not add balances")
            raise e


def increment_balance(chain_id: int, token_address: str, wallet_address: str, value: Decimal) -> None:
    """SQLTransaction containing UPDATE of balance

    :param chain_id: chain ID
    :param token_address: Token Address
    :param wallet_address: Wallet Address
    :param value: increment value, can be negative
    :return : None
    """
    session_maker = DBSession.get_db()
    with session_maker.begin() as session:
        try:
            object = (
                session
                .query(Balance)
                .filter_by(
                    chain_id=chain_id,
                    token_address=token_address.lower(),
                    wallet_address=wallet_address.lower()
                )
                .first()
            )
            if object:
                object.balance += value
            else:
                object = Balance(
                    chain_id=chain_id,
                    token_address=token_address.lower(),
                    wallet_address=wallet_address.lower(),
                    balance=value
                )
                session.add(object)
            session.commit()
        except Exception as e:
            logging.warning(f"did not increment balance")
            raise e




def delete_token_balances(chain_id: int, token_address: str) -> None:
    """SQLTransaction containing DELETE the balances for the token_address

    :param chain_id: chain ID
    :param token_address: Token Address to delete the balances from
    :return : None
    """
    # SQLAlchemy Core
    engine = DBSession.get_engine()
    with engine.connect() as conn:
        try:
            del_stmt = (
                delete(Balance)
                .where(Balance.chain_id == chain_id)
                .where(Balance.token_address == token_address.lower())
            )
            conn.execute(del_stmt)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
