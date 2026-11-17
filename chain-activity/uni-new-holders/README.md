# New UNI holders per day

Since UNI launched in September 2020, **1.69M addresses have sent or received it on Ethereum, and 27 Oct 2026 brought 13.1K new ones, the busiest day since launch week**. Only three days have beaten it, all in UNI's first week.

| Day (UTC) | New addresses |
| --- | --- |
| 2020-09-17 | 178,331 |
| 2020-09-18 | 53,692 |
| 2020-09-19 | 18,600 |
| 2026-10-27 | 13,137 |
| 2020-09-20 | 9,872 |

## Why it's interesting

New addresses per day is one of the clearest signs of a token reaching new people, and it needs the token's whole history to get right, since you only know an address is new if you've seen everything before it. HyperSync returns every UNI transfer since 2020 in one paged query, and the same script works for any ERC-20.

## What it pulls

All of it comes from HyperSync.

- Every `Transfer` log from the UNI token contract, [`0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984`](https://etherscan.io/token/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984), from its deployment block 10,861,674.
- Block timestamps, to put each transfer in a UTC day.

An address counts on the UTC day it first appears as the sender or receiver of a UNI transfer. The zero address is skipped, so it never counts as a holder.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                              # UNI on Ethereum
python3 script.py 0xTokenAddress 12345678      # any ERC-20 on Ethereum, with an optional start block
```

It writes `new_addresses.csv` with one row per day (`day`, `new_addresses`, `transfers`) and prints the busiest days. Sample output.

```
1,693,450 addresses in total. Busiest days for new addresses:
  2020-09-17  178,331
  2020-09-18  53,692
  2020-09-19  18,600
  2026-10-27  13,137
  2020-09-20  9,872
```

It always reads up to the latest block, so your totals will be a little higher.

## Change the window or chain

- **Token.** Pass any ERC-20 address as the first argument.
- **Start block.** The second argument sets where to start. Use the token's deployment block, or "new" only means new since that block.
- **Chain.** Swap `HYPERSYNC` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and pass a token address on that chain.

## Check the numbers

The `new_addresses` column in `new_addresses.csv` adds up to the total on the first printed line. For a single day, you can open the token's transfers on [Etherscan](https://etherscan.io/token/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984) and spot check that a new address had no earlier UNI transfer.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of UNI
on Ethereum since 2020 and counts addresses that send or receive it for the
first time each day. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Add a second count per day of new receivers only, ignoring addresses whose
first appearance was as a sender, and add it as a column in new_addresses.csv.
Keep the standard library only. Then check that the original new_addresses
column still adds up to the total the script prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Uniswap docs](https://docs.uniswap.org)
- [Envio Discord](https://discord.gg/envio)
