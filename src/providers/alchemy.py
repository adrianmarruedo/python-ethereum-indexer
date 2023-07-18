import logging
import time
from typing import Dict, List
from web3 import Web3

from src.models import LogModel

logger = logging.getLogger()


class AlchemyProvider:
    """Alchemy provider Class"""

    def __init__(self, chain_id: int, host: str, websocket: str, api_key: str) -> None:
        self.chain_id = chain_id
        self._url = host
        self._websocket_url = websocket
        self._key = api_key
        self._web3 = Web3(Web3.HTTPProvider(self._url + self._key))

    def parse_log(self, log) -> LogModel:
        """Returns the LogModel of the given log AttrDict"""
        try:
            log_model = LogModel(
                chain_id=self.chain_id,
                block_num=log["blockNumber"],
                block_hash=self._web3.to_hex(log["blockHash"]),
                transaction_hash=self._web3.to_hex(log["transactionHash"]),
                address=str(log["address"]),
                topic=self._web3.to_hex(log["topics"][0]) if len(log["topics"]) else None,
                topics=[self._web3.to_hex(topic) for topic in log["topics"]],
                data=self._web3.to_hex(log["data"]),
                log_index=log["logIndex"],
                deleted=log["removed"],
            )
            return log_model
        except Exception as e:
            logger.error(f"Error Log: {log}")
            raise e

    def parse_log_dict(self, log) -> LogModel:
        """Returns the LogModel of the given log Dict from response json"""
        try:
            log_model = LogModel(
                chain_id=self.chain_id,
                block_num=self._web3.to_int(hexstr=log["blockNumber"]),
                block_hash=log["blockHash"],
                transaction_hash=log["transactionHash"],
                address=log["address"],
                topic=log["topics"][0] if len(log["topics"]) else None,
                topics=log["topics"],
                data=log["data"],
                log_index=self._web3.to_int(hexstr=log["logIndex"]),
                deleted=bool(log["removed"]),
            )
            return log_model
        except Exception as e:
            logger.error(f"Error Log: {log}")
            raise e

    def get_latest_block_num(self) -> int:
        """Returns last block number"""
        return self._web3.eth.block_number

    def get_logs(self, start_block: int, end_block: int) -> List[LogModel]:
        """Returns List of logs between the range conformed to LogModel"""
        assert end_block >= start_block

        logs = []
        st = time.time()

        event_filter = {"fromBlock": start_block, "toBlock": end_block}
        logs_provider = self._web3.eth.get_logs(event_filter)
        for log in logs_provider:
            logs.append(self.parse_log(log))
        et = time.time()
        logger.debug(f"get_logs time: {et-st} seconds")

        return logs

    def get_logs_filtered(self, filter_dict: Dict) -> List[LogModel]:
        """Returns List of logs conformed to LogModel applying the EthFilter in filter_dict"""
        logs = []
        st = time.time()

        logs_provider = self._web3.eth.get_logs(filter_dict)
        for log in logs_provider:
            logs.append(self.parse_log(log))
        et = time.time()
        logger.debug(f"get_logs time: {et-st} seconds")

        return logs

    def checksum_address(self, contract_address: str) -> str:
        return self._web3.to_checksum_address(contract_address)
