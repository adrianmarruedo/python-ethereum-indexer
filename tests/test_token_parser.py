import unittest
from decimal import Decimal

from src.parsers import TokenParser
from src.models import LogModel, TransferModel


class TestTokenParserClass(unittest.TestCase):
    """Test TokenParser Class"""

    # TEST CASES
    # TRANSFER_TOPIC
    log_1 = LogModel(
        chain_id=1,
        block_num=15941856,
        block_hash="0x5ce752bc54c89c97098bb1222d6fe499f6819820d06fccec057008a975ad8614",
        address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        topic="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        topics=[
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "0x00000000000000000000000020dc3024213990d0cae48313da541459648a9483",
            "0x000000000000000000000000861ff4c1aa2591dac7b24a0e80631f77f59a06dc",
        ],
        data="0x0000000000000000000000000000000000000000000000000000000077359400",
        transaction_hash="0x3b2d2ed6638e0c0c9e53d84f463a4a3fc9de228d6e52356cf4e05537786313c0",
        log_index=168,
        deleted=False,
    )
    log_2 = LogModel(
        chain_id=1,
        block_num=15941856,
        block_hash="0x5ce752bc54c89c97098bb1222d6fe499f6819820d06fccec057008a975ad8614",
        address="0xD46bA6D942050d489DBd938a2C909A5d5039A161",
        topic="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        topics=[
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "0x000000000000000000000000c5be99a02c6857f9eac67bbce58df5572498f40c",
            "0x000000000000000000000000e6c4293235d11c9d241d6d204eb366f0afdbe3fa",
        ],
        data="0x000000000000000000000000000000000000000000000000000000229d4309a6",
        transaction_hash="0xcf3ed8a344c06d1b2eefc5d26e3c59c4ca512d28bc84a07bf3eccde78e7bec7a",
        log_index=165,
        deleted=False,
    )
    # ERROR CASES
    # Transfer ERC721
    log_3 = LogModel(
        chain_id=1,
        block_num=15941856,
        block_hash="0x5ce752bc54c89c97098bb1222d6fe499f6819820d06fccec057008a975ad8614",
        address="0xB54420149dBE2D5B2186A3e6dc6fC9d1A58316d4",
        topic="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        topics=[
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0x000000000000000000000000a1d02d5d5d76bb3b75cbcfe05187eccbaf292a75",
            "0x0000000000000000000000000000000000000000000000000000000000001c24",
        ],
        data="0x",
        transaction_hash="0x629934f933d27b8532d64ae5ede2057b7084b842aaddff5e4c8971d3a5adae65",
        log_index=154,
        deleted=False,
    )
    log_4 = LogModel(
        chain_id=1,
        block_num=15941856,
        block_hash="0x5ce752bc54c89c97098bb1222d6fe499f6819820d06fccec057008a975ad8614",
        address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        topic=None,
        topics=[],
        data="0x0000000000000000000000000000000000000000000000000000000077359400",
        transaction_hash="0x3b2d2ed6638e0c0c9e53d84f463a4a3fc9de228d6e52356cf4e05537786313c0",
        log_index=168,
        deleted=False,
    )

    # RESULTS
    # TRANSFER_TOPIC
    event_1 = TransferModel(
        chain_id=log_1.chain_id,
        block_num=log_1.block_num,
        block_time=log_1.block_time,
        tx_hash=log_1.transaction_hash,
        tx_from="0x20dc3024213990d0cae48313da541459648a9483",
        tx_to="0x861ff4c1aa2591dac7b24a0e80631f77f59a06dc",
        value=Decimal(2000000000) / Decimal(10**18),
        type="Transfer",
        token_address=log_1.address,
    )
    event_2 = TransferModel(
        chain_id=log_2.chain_id,
        block_num=log_2.block_num,
        block_time=log_2.block_time,
        tx_hash=log_2.transaction_hash,
        tx_from="0xc5be99a02c6857f9eac67bbce58df5572498f40c",
        tx_to="0xe6c4293235d11c9d241d6d204eb366f0afdbe3fa",
        value=Decimal(148667304358) / Decimal(10**18),
        type="Transfer",
        token_address=log_2.address,
    )

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        self.parser = TokenParser()

    def test_parse_log_1(self):
        event = self.parser.decode_log(self.log_1)
        self.assertEqual(event, self.event_1)

    def test_parse_log_2(self):
        event = self.parser.decode_log(self.log_2)
        self.assertEqual(event, self.event_2)

    def test_parse_log_3(self):
        with self.assertRaises(Exception):
            event = self.parser.decode_log(self.log_3)

    def test_parse_log_4(self):
        with self.assertRaises(Exception):
            event = self.parser.decode_log(self.log_4)

    def test_parse_log_5(self):
        with self.assertRaises(Exception):
            event = self.parser.decode_log(self.log_5)

