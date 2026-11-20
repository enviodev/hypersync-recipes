# How to count new liquidity positions and the busiest NFT collections on Ethereum

This example counts new Uniswap and Aero liquidity positions with HyperSync. Every new liquidity position on a concentrated-liquidity DEX is an NFT, so counting new positions means counting mints on one contract. Over 24 hours (Ethereum blocks 26,448,557 to 26,455,757), **Uniswap v4 minted 2,739 positions, Aero Slipstream 2,274 and Uniswap v3 506**.

The same run ranks every NFT collection on the chain, with no contract list. 38,149 NFT transfers happened that day and five position and exit queue collections made up 19,354 of them, which is 50.7%.

| # | Collection | Transfers | Mints |
| --- | --- | --- | --- |
| 1 | Slipstream V3 Deposit (AERO-CL) | 10,637 | 2,274 |
| 2 | Kiln Exit Queue (vEQ) | 3,390 | 33 |
| 3 | Uniswap v4 Positions NFT | 3,332 | 2,739 |
| 4 | Clovers | 1,937 | 1,937 |
| 5 | Coinbase Cloud Exit Queue (vEQ) | 1,179 | 15 |
| 6 | Uniswap V3 Positions NFT-V1 | 816 | 506 |
| 7 | 111K | 720 | 360 |
| 8 | Ensuro v3 | 690 | 690 |
| 9 | Shapes | 682 | 337 |
| 10 | Argonauts | 679 | 0 |

## Why it's interesting

An NFT is just a token with its own id, so DeFi uses them for anything that is one of a kind. A liquidity position is one, and so is your place in a staking exit queue. They move far more often than art does, so a transfer count ranks them first.

## What it pulls

- Every ERC-20/ERC-721 `Transfer` log in the window from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). An ERC-721 transfer has the token id indexed, so it carries a fourth topic, which is how the script tells NFTs from tokens.
- Transfers and mints (transfers from the zero address) per collection, then the top 10.
- Each top collection's name and symbol from a standard RPC. HyperRPC does not serve `eth_call`, so set `RPC_URL` if you want your own node. The counts all come from HyperSync.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                       # the last 7,200 blocks, about 24 hours
python3 script.py 26448557 26455757     # the window above
```

It takes a few minutes. Sample output for the window above:

```
Ethereum NFT transfers, blocks 26,448,557 to 26,455,757 (7,200 blocks, about 24 hours)
38,149 transfers across 1,293 collections

 1   10,637 transfers   2,274 mints  Slipstream V3 Deposit (AERO-CL)  0x4857db576ee0e45f10525ec59527bfd10beec60b
 2    3,390 transfers      33 mints  Kiln Exit Queue (vEQ)  0x8d6fd650500f82c7d978a440348e5a9b886943bf
 3    3,332 transfers   2,739 mints  Uniswap v4 Positions NFT (UNI-V4-POSM)  0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e
 4    1,937 transfers   1,937 mints  Clovers (CLV)  0xb55c5cac5014c662fdbf21a2c59cd45403c482fd
 5    1,179 transfers      15 mints  Coinbase Cloud Exit Queue (vEQ)  0x86358f7b33b599c484e0335b8ee4f7f7f92d8b60
 ...
```
