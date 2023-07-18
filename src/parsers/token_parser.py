import logging
from decimal import Decimal

from web3 import Web3

from src.utils import abi_utils
from src.models import LogModel, TransferModel

from src.constants import TRANSFER_TOPIC, TYPE_ERC20, DECIMALS_DEFAULT


logger = logging.getLogger()

web3 = Web3()


class TokenParser:
    """Token Transfer Parser Class"""

    def decode_log(self, log: LogModel) -> TransferModel:
        """Returns a Model of the log data given the contract standard"""
        contract_type = self.decode_token_standard(log.topic, len(log.topics))

        if contract_type == TYPE_ERC20:
            return self._parse_erc20_transfer_log(log)
        else:
            raise Exception("Wrong Contract Type")

    @staticmethod
    def _parse_erc20_transfer_log(log: LogModel) -> TransferModel:
        topics = log.topics + abi_utils.split_to_words(log.data)
        args = {
            "from": abi_utils.word_to_address(topics[1]),
            "to": abi_utils.word_to_address(topics[2]),
            "value": web3.to_int(hexstr=topics[3]),
        }

        result = TransferModel(
            chain_id=log.chain_id,
            block_num=log.block_num,
            block_time=log.block_time,
            tx_hash=log.transaction_hash,
            tx_from=args["from"],
            tx_to=args["to"],
            value=Decimal(args["value"]) / Decimal(10**DECIMALS_DEFAULT),
            type="Transfer",
            token_address=log.address.lower(),
        )
        return result

    @staticmethod
    def decode_token_standard(topic: str, topics_count: int):
        """Returns the token standard type"""
        if not topic:
            raise Exception("Anonymous Event")
        elif topic == TRANSFER_TOPIC and topics_count == 3:
            return TYPE_ERC20

        raise Exception("Topic is not part of the listed signatures")
