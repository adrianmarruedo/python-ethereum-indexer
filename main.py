import click
import asyncio
import logging

from config import settings
from src.db import Base, get_token_top_holders
from src.db.db_utils import create_tables
from src.providers import AlchemyProvider
from src.services import IndexerService, BackfillService
from src.constants import INIT_BLOCK, DEFAULT_CHAIN_ID

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


@click.group()
def cli():
    pass


@click.command()
@click.argument("contract_address", type=str)
@click.argument("backfill", type=bool, default=True)
def run_indexing(contract_address: str, backfill: bool) -> None:
    """Strats the indexing for the contract 'contract_address'.

    :param contract_address: contract_address
    :param backfill: if True, backfill past
    :return : None
    """
    logging.info(f"Starting Indexer for contract '{contract_address}' for chain ID {DEFAULT_CHAIN_ID}")
    provider = AlchemyProvider(DEFAULT_CHAIN_ID, settings.PROVIDER_URL, settings.PROVIDER_WEBSOCKET, settings.PROVIDER_KEY)
    backfill_service = BackfillService(DEFAULT_CHAIN_ID, provider)
    indexer_service = IndexerService(DEFAULT_CHAIN_ID, provider)

    checksum_address = provider.checksum_address(contract_address)
    current_block = provider.get_latest_block_num()
    if backfill:
        logging.info(f"Backfilling Transfers for ERC20 contract '{checksum_address}' up to block {current_block}")
        # TODO IMPROVEMENT: replace INIT_BLOCK by finding contract creation using Etherscan API
        backfill_service.backfill(checksum_address, INIT_BLOCK, current_block)
    else:
        logging.info(f"Skipped Backfill")

    logging.info(f"Real-Time Indexing starting...")
    asyncio.run(indexer_service.start(checksum_address))


@click.command()
@click.argument("token_address", type=str)
@click.argument("limit", type=int, default=10)
def get_top_holders(token_address: str, limit: int) -> None:
    """Prints the n top holders for the token_address.

    :param token_address: Token Address
    :param limit: number of holders to display
    :return : None
    """
    holders = get_token_top_holders(DEFAULT_CHAIN_ID, token_address, limit)
    i = 1
    for holder in holders:
        print(f"#{i}. wallet_address: {holder.wallet_address}. balance: {holder.balance}")
        i += 1

cli.add_command(run_indexing)
cli.add_command(get_top_holders)

if __name__ == "__main__":
    create_tables(metadata=Base.metadata)
    cli()
