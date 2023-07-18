from __future__ import annotations

import logging
from typing import List, Dict

from sqlalchemy import delete

from ...db_utils import DBSession
from . import Transfer

from src.models import TransferModel


def _transfer_model_to_dict(transfer: TransferModel) -> Dict:
    """Low overhead pydantic TransferModel to dict"""
    return {
        "chain_id": transfer.chain_id,
        "block_num": transfer.block_num,
        "tx_hash": transfer.tx_hash,
        "tx_from": transfer.tx_from.lower(),
        "tx_to": transfer.tx_to.lower(),
        "value": transfer.value,
        "type": transfer.type,
        "token_address": transfer.token_address.lower(),
        "block_time": transfer.block_time,
    }


def insert_transfers(transfers: List[TransferModel]) -> None:
    """SQLTransaction containing List[TransferModel] INSERT

    :param transfers: List of transfers to insert
    :return : None
    """
    if len(transfers) == 0:
        logging.warning("No transfers provided")
        return
    # SQLAlchemy Core
    transfers_dict = [_transfer_model_to_dict(tx) for tx in transfers]
    engine = DBSession.get_engine()
    with engine.connect() as conn:
        try:
            insert_obj = Transfer.__table__.insert()
            conn.execute(insert_obj, transfers_dict)
            conn.commit()
        except Exception as e:
            logging.warning(f"did not add transfers")
            raise e


def delete_token_transfers(chain_id: int, token_address: str) -> None:
    """SQLTransaction containing DELETE transfers for a token_address

    :param chain_id: chain ID
    :param token_address: token_address to filter
    :return : None
    """
    # SQLAlchemy Core
    engine = DBSession.get_engine()
    with engine.connect() as conn:
        try:
            del_stmt = (
                delete(Transfer)
                .where(Transfer.chain_id == chain_id)
                .where(Transfer.token_address == token_address.lower())
            )

            conn.execute(del_stmt)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
