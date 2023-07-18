DEFAULT_CHAIN_ID = 1

NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

# Transfer Names
TRANSFER = "Transfer"

# Transfer Topics
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # Transfer

TRANSFER_SELECTOR_MAP = {
    "0xa9059cbb": {
        "function_name": "transfer",
        "function_signature": "transfer(address,uint256)",
        "inputs": ["to", "value"],
        "types": ["address", "uint256"],
    },
    "0x23b872dd": {
        "function_name": "transferFrom",
        "function_signature": "transferFrom(address,address,uint256)",
        "inputs": ["from", "to", "value"],
        "types": ["address", "address", "uint256"],
    }
}

# Types
TYPE_ERC20 = "ERC20"

DECIMALS_DEFAULT = 18

INIT_BLOCK = 10000000
