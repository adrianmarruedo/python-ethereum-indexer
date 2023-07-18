# Ethereum Python Indexer
The repo contains a simple Ethereum mainnet indexer to index ERC20 transfers and balances for a 
requested contract_address. The indexer will first backfill the past data using Web3 and alchemy then 
start the real-time indexing using Alchemy websocket. Some characteristics:
* Python 3.10
* Sqlalchemy to manage database interaction. sqlalchemy core is used for efficient 
bulk insert. sqlalchemy orm for the rest.
* Pydantic to enforce and verify on execution the data models for logs, transfers 
and balances. 
* Secrets and configs managed by a combination of load_env and pydantic.BaseSettings.
* For simplicity, ERC20 Decimals are hardcoded to 18 (common use). See improvements section.
* The backfill automatically throattles eth.get_logs requests in order to respect the 10k max 
logs returned by Alchemy.
* For simplicity, Init block of backfill is hardcoded to 13M. Using 'earliest' start_block would not be compatible with 
the throattling. See improvements section.
* Transfers and balances are stored in a table. 
* Backfill compute balance is done using pandas package, which is fast but relies on RAM.
* For simplicity, Real-time update of balances is done by incrementing affected balances. Therefore, not reorg protected. 
See improvements section.
* It is assumed low overhead in the backfill for recently deployed tokens or tokens with not many transactions. 

## Setup
* Use Python 3.10
* Install requirements
    ```
    pip install -r requirements.txt
    ```
* Update .env file with Alchemy API key and DB connection. There is a template at .env_template

## How to run
  1. Run CLI command
      ```
      python main.py run-indexing <contract_address> <backfill>
      ```
      Where:
      - contract_address: token address
      - backfill: True if backfill past

      Example:

      ```
      python main.py run-indexing 0xBAac2B4491727D78D2b78815144570b9f2Fe8899 True
      ```
      The command will create the tables in the localhost Postgres if they don't exist already. 
2. Check the balances table. The first execution will automatically create the tables if they 
didn't exist. Note that addresses and token_address have been lowercased. There are some helpful queries in 
the sql folder. Alternatively, run the following CLI command:
    ```
    python main.py get-top-holders <contract_address> <limit>
    ```
   Where:
      - contract_address: token address
      - limit: Number of top holders to display
   Example:
    ```
    python main.py get-top-holders 0x600000000a36F3cD48407e35eB7C5c910dc1f7a8 10
    ```

