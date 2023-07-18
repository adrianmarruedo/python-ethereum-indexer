from __future__ import annotations

import logging
import json
from typing import List, Tuple, Dict, Any
from websockets import connect

import src.db as db
from src.providers import AlchemyProvider
from src.parsers import TokenParser
from src.constants import TRANSFER_TOPIC, NULL_ADDRESS

logger = logging.getLogger()


class IndexerService:
    """Indexer Service Class for real-time indexing"""

    def __init__(self, chain_id: int, provider: AlchemyProvider) -> None:
        self.chain_id = chain_id
        self._provider = provider
        self._parser = TokenParser()

    async def start(self, contract_address: str) -> None:
        subscription = {
            "jsonrpc": "2.0",
            "id": self.chain_id,
            "method": "eth_subscribe",
            "params": [
                "logs",
                {
                    "address": contract_address,
                    "topics": [TRANSFER_TOPIC]
                }
            ]
        }
        async with self._get_connection() as ws:
            await ws.send(json.dumps(subscription))
            subs_resp = await ws.recv()
            while True:
                response_str = await ws.recv()
                response = json.loads(response_str)
                log_dict = response["params"]["result"]
                log = self._provider.parse_log_dict(log_dict)
                if not log.deleted:
                    transfer = self._parser.decode_log(log)
                    logger.info(f"New transfer: block_num={transfer.block_num}, tx_hash={transfer.tx_hash}, tx_from={transfer.tx_from}, tx_to={transfer.tx_to}, value={transfer.value}")
                    db.insert_transfers(transfers=[transfer])
                    db.increment_balance(self.chain_id, transfer.token_address, transfer.tx_to, transfer.value)
                    db.increment_balance(self.chain_id, transfer.token_address, transfer.tx_from, -transfer.value)


    def _get_connection(self):
        return connect(self._provider._websocket_url+self._provider._key)
