import degenbot
from web3 import Web3
from degenbot.erc20_tok

RPC_URL = "https://eth.llamarpc.com"  # free public RPC

w3 = Web3(Web3.HTTPProvider(RPC_URL))

print("Connected:", w3.is_connected())
print("Chain ID:", w3.eth.chain_id)
print("Latest block:", w3.eth.block_number)

address = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48") #USDC

eth_balance = w3.eth.get_balance(address)
code = w3.eth.get_code(address)

print(code)

Erc2