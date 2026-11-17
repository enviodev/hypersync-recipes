# Stablecoins on Arc, 30 days of supply

In the 30 days to 9 Nov 2026, **USDC supply on Arc grew by $790.6M, from $496.9M to $1.29B**. $5.45B was minted and $4.66B burned in that time, and the biggest single day was 22 Oct, when supply rose by $114.9M. EURC on Arc grew by €1.3M to €8.9M.

| | Now | 7 days ago | 30 days ago | Minted (30d) | Burned (30d) |
| --- | --- | --- | --- | --- | --- |
| USDC | 1.287B | 1.083B | 496.9M | 5.451B | 4.660B |
| EURC | 8.9M | 7.1M | 7.6M | 90.5M | 89.2M |

## Why it's interesting

Arc is Circle's own chain, so USDC and EURC both live there natively. Rebuilding supply from mints and burns gives you a day-by-day series from launch, which is what you'd want behind a stablecoin dashboard for a new chain. And because USDC is Arc's native gas token, it's also a neat example of a native asset that still emits ERC-20 events.

## What it pulls

- Every `Transfer` log to or from the zero address on two tokens from the [Arc contract addresses page](https://docs.arc.io/arc/references/contract-addresses), both with 6 decimals.
  - USDC `0x3600000000000000000000000000000000000000`
  - EURC `0xbEf5f6d51CB62b58e6A8f77868681825C6fe21c1`
- A mint is a transfer from the zero address and a burn is a transfer to it. Supply is mints minus burns since the first block.

USDC's `totalSupply()` sits 10,000 USDC above mints minus burns at every block from 1,000 on, a genesis balance with no `Transfer` log, so the script adds it. Every number here comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                        # up to the latest block
python3 script.py 2026-11-09T10:41:53    # the window above
```

Sample output from the window above. The full run is in `out.txt`.

```
Stablecoins on Arc, up to 09 Nov 10:41 UTC (last mint or burn in block 30,336,014)
USDC: 1.287B now, 1.083B 7 days ago, 496.9M 30 days ago
      30 days: +790.6M net, 5.451B minted, 4.660B burned
EURC: 8.9M now, 7.1M 7 days ago, 7.6M 30 days ago
      30 days: +1.3M net, 90.5M minted, 89.2M burned

USDC supply at the end of each UTC day, last 31 days
  2026-10-10  499.9M
  ...
  2026-11-09  1.287B
Biggest one-day rise: 2026-10-22, +114.9M
```

Without an end time the window ends at the latest block, so your numbers will differ.

## Change the window or chain

- **Window.** Pass an end time in UTC to rerun a past window. The 7 and 30 day lookbacks are the `(0, 7, 30)` tuple near the end of the script, so change them there for a longer view.
- **Tokens.** Add any Arc token to `TOKENS` with its decimals. The [Arc contract addresses page](https://docs.arc.io/arc/references/contract-addresses) lists the rest.
- **Chain.** Change `URL` to another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), swap the token addresses, and drop `GENESIS`, which only applies to Arc.

## Check the numbers

As the comparison, `totalSupply()` from `https://rpc.mainnet.arc.io` at block 30,336,095 returns 1,287,478,957.572406 USDC and 8,918,370.632218 EURC. Both match the script to the last unit. USDC also matches at blocks 25,000,000 and 30,000,000.

```bash
cast call 0x3600000000000000000000000000000000000000 "totalSupply()(uint256)" \
  --rpc-url https://rpc.mainnet.arc.io --block 30336095
```

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to rebuild USDC and EURC supply
on Arc from every mint and burn. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Write each token's supply at the end of every UTC day since launch to a CSV, and
add a column for the number of addresses that minted that day. Keep the standard
library only. Then check the last row for each token against totalSupply() on
https://rpc.mainnet.arc.io at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Arc contract addresses](https://docs.arc.io/arc/references/contract-addresses)
- [Envio Discord](https://discord.gg/envio)
