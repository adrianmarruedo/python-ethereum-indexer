from __future__ import annotations
import logging
import time
from typing import List, Tuple, Dict, Any
import pandas as pd

import src.db as db
from src.providers import AlchemyProvider
from src.parsers import TokenParser
from src.models import TransferModel, LogModel, BalanceModel
from src.constants import TRANSFER_TOPIC, NULL_ADDRESS

DEFAULT_CHUNK_SIZE = 2000
CHUNK_INCREASE = 1.5
CHUNK_DECREASE = 0.5
MIN_CHUNK = 2000
MAX_CHUNK = 50000
RETRIES_NUM = 7
RETRY_DELAY = 1
LOGS_DECREASE_THRESHHOLD = 5000  # Number of logs to trigger chunk decrease

logger = logging.getLogger()


class BackfillService:
    """Backfill Service Class for past indexing"""

    def __init__(self, chain_id: int, provider: AlchemyProvider) -> None:
        self.chain_id = chain_id
        self._provider = provider
        self._parser = TokenParser()

    def backfill(self, contract_address: str, start_block: int, end_block: int) -> None:
        """Backfills the contract_address"""
        self._truncate_contract(contract_address)
        transfers = self._progressive_backfill(contract_address, start_block, end_block)
        balances = self._compute_balances(transfers)
        db.insert_balances(self.chain_id, balances)

    def _truncate_contract(self, contract_address: str) -> None:
        db.delete_token_balances(self.chain_id, token_address=contract_address)
        db.delete_token_transfers(self.chain_id, token_address=contract_address)

    def _progressive_backfill(
            self, contract_address: str, start_block: int, end_block: int, start_chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> List[TransferModel]:
        """Backfills progressively in order to throatle get_logs calls. for eth_logs method to be called safely,
        block_range must be under 2k or number of return logs must be under 10k"""
        current_block = start_block

        chunk_size = start_chunk_size
        accum_transfers = []
        all_processed = 0

        while current_block <= end_block:
            estimated_end_block = min(current_block + chunk_size - 1, end_block)
            logger.info(f"Scanning blocks: {current_block} - {estimated_end_block}. chunk size: {chunk_size}")
            actual_end_block, transfers = self._get_transfers(contract_address, current_block, estimated_end_block)
            db.insert_transfers(transfers)

            accum_transfers.extend(transfers)
            current_end = actual_end_block
            all_processed += len(transfers)

            logger.info(f"Stats. Events found: {len(transfers)}. Accum. events: {all_processed}")
            chunk_size = self._estimate_next_chunk_size(chunk_size, len(transfers))

            # Set where the next chunk starts
            current_block = current_end + 1

        return accum_transfers

    def _get_transfers(self, contract_address: str, start_block: int, end_block: int) -> Tuple[int,List[TransferModel]]:
        filter_dict = {
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": contract_address,
            "topics": [TRANSFER_TOPIC],
        }
        end_block, logs = self._retry_web3_call(
            func=self._provider.get_logs_filtered,
            filter_params=filter_dict,
            retries=RETRIES_NUM,
            delay=RETRY_DELAY
        )
        transfers = [self._parser.decode_log(log) for log in logs if not log.deleted]

        return end_block, transfers

    def _compute_balances(self, transfers: List[TransferModel]) -> List[BalanceModel]:
        """Returns a list of Balances given a list of Transfers

        :param transfers: List of Transfers to compute the balance from
        :return: List of resulting Balances
        """
        if not len(transfers):
            return []

        balance_list = []

        transfer_df = pd.DataFrame([dict(transfer) for transfer in transfers])
        increment_df = transfer_df[
            ["token_address", "token_id", "tx_to", "value"]
        ].copy()
        increment_df.columns = ["token_address", "token_id", "wallet_address", "value"]
        decrement_df = transfer_df[
            ["token_address", "token_id", "tx_from", "value"]
        ].copy()
        decrement_df.value = decrement_df.value.apply(lambda x: -x)
        decrement_df.columns = ["token_address", "token_id", "wallet_address", "value"]
        delta_df = pd.concat([increment_df, decrement_df])
        balance_df = delta_df.groupby(
            ["token_address", "wallet_address"]
        ).agg(balance=pd.NamedAgg(column="value", aggfunc="sum"))
        balance_df.reset_index().apply(
            lambda row: balance_list.append(self._pandas_balance_row_to_model(row))
            if self._pandas_balance_row_to_model(row)
            else None,
            axis=1,
        )

        return balance_list

    def _pandas_balance_row_to_model(self, row: List[Any]) -> BalanceModel | None:
        """Returns the TransferModel given a pd row
        :param row: Pandas numpy array
        :return: Returns BalanceModel or None in case of the row being the NULL_ADDRESS
        """
        if row[1] == NULL_ADDRESS:
            return None
        model = BalanceModel(
            chain_id=self.chain_id,
            token_address=row[0],
            wallet_address=row[1],
            balance=row[2],
        )
        return model

    @staticmethod
    def _retry_web3_call(
            func, filter_params: Dict, retries: int, delay: int
    ) -> Tuple[int, List[LogModel]]:
        """A custom retry loop to throttle down block range.

        If our JSON-RPC server cannot serve all incoming `eth_getLogs` in a single request,
        we retry and throttle down block range for every retry.

        :param func: A callable that triggers Ethereum JSON-RPC, as func(start_block, end_block)
        :param filter_params: filter_dict for `eth_getLogs` method
        :param retries: How many times we retry
        :param delay: Time to sleep between retries
        """
        start_block = filter_params["fromBlock"]
        end_block = filter_params["toBlock"]

        for i in range(retries):
            try:
                filter_params["toBlock"] = end_block
                return end_block, func(filter_params)
            except Exception as e:
                if i < retries - 1:
                    logger.warning(
                        "Retrying events for block range %d - %d (%d) failed with %s, retrying in %s seconds",
                        start_block,
                        end_block,
                        end_block-start_block,
                        e,
                        delay
                    )
                    # Decrease the range
                    end_block = start_block + ((end_block - start_block) // 2)
                    # Let the JSON-RPC to recover e.g. from restart
                    time.sleep(delay)
                    continue
                else:
                    logger.warning("Out of retries")
                    raise

    @staticmethod
    def _estimate_next_chunk_size(current_chuck_size: int, data_count: int) -> int:
        """Figures out optimal chunk size"""
        if data_count > LOGS_DECREASE_THRESHHOLD:
            current_chuck_size *= CHUNK_DECREASE
        else:
            current_chuck_size *= CHUNK_INCREASE

        current_chuck_size = max(MIN_CHUNK, current_chuck_size)
        current_chuck_size = min(MAX_CHUNK, current_chuck_size)

        return int(current_chuck_size)
