import time
import signal
import sys
from web3 import Web3

RPC_URL = "https://eth.llamarpc.com"  # change if you want a different RPC
PAIR_ADDRESS = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"  # example: Uniswap V2 USDC/WETH pair (mainnet)
POLL_INTERVAL = 10  # seconds

# Minimal ABIs for the calls we need
UNISWAP_V2_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "type": "function",
    },
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "type": "function"},
]

ERC20_MIN_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
]


w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("RPC connection failed:", RPC_URL)
    sys.exit(1)

pair = w3.eth.contract(Web3.to_checksum_address(PAIR_ADDRESS), abi=UNISWAP_V2_PAIR_ABI)


def sigint_handler(sig, frame):
    print("\nStopping tracker.")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)


def fetch_token_info(token_address):
    tok = w3.eth.contract(Web3.to_checksum_address(token_address), abi=ERC20_MIN_ABI)
    try:
        symbol = tok.functions.symbol().call()
    except Exception:
        symbol = token_address
    try:
        decimals = tok.functions.decimals().call()
    except Exception:
        decimals = 18
    return symbol, decimals


def format_amount(raw, decimals):
    return raw / (10 ** decimals)


def main():
    token0_addr = pair.functions.token0().call()
    token1_addr = pair.functions.token1().call()
    sym0, dec0 = fetch_token_info(token0_addr)
    sym1, dec1 = fetch_token_info(token1_addr)

    print(f"Tracking pair {PAIR_ADDRESS}")
    print(f"token0: {sym0} ({token0_addr}) dec={dec0}")
    print(f"token1: {sym1} ({token1_addr}) dec={dec1}")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            block = w3.eth.block_number
            reserves = pair.functions.getReserves().call()
            r0, r1, ts = reserves
            amt0 = format_amount(r0, dec0)
            amt1 = format_amount(r1, dec1)

            # price: token0 in token1 = (reserve1/dec1) / (reserve0/dec0)
            price0_in_1 = (r1 * (10 ** dec0)) / (r0 * (10 ** dec1)) if r0 != 0 else float("inf")
            price1_in_0 = (r0 * (10 ** dec1)) / (r1 * (10 ** dec0)) if r1 != 0 else float("inf")

            print(f"[block {block}] reserves: {amt0:.6f} {sym0} / {amt1:.6f} {sym1} | 1 {sym0} = {price0_in_1:.12f} {sym1} | 1 {sym1} = {price1_in_0:.12f} {sym0}")
        except Exception as e:
            print("Error fetching data:", e)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()