# Ripple USD (RLUSD) supply on Ethereum

In the 30 days to 13 Nov 2026, **RLUSD supply on Ethereum grew by $557.9M, from $1.35B to $1.91B (+41%)**. $803.4M was minted and $245.6M burned in that time, and 11.7K wallets now hold a balance.

| | 30 days to 13 Nov 2026 |
| --- | --- |
| Supply 30 days ago | 1,347.5M RLUSD |
| Supply now | 1,905.4M RLUSD |
| Minted | 803.4M RLUSD |
| Burned | 245.6M RLUSD |
| Holders | 11,678 |

## Why it's interesting

RLUSD is one of the newer dollar stablecoins, and its whole life on Ethereum is about 596K transfers. That's small enough to replay from the first block in a few minutes, which gives you supply, mints, burns and every holder's balance from one query. It's a good template for tracking any token from launch.

## What it pulls

- Every `Transfer` log on the RLUSD proxy [`0x8292Bb45bf1Ee4d140127049757C2E0fF06317eD`](https://etherscan.io/address/0x8292Bb45bf1Ee4d140127049757C2E0fF06317eD), from Ripple's [token addresses](https://docs.ripple.com/products/stablecoin/overview/token-addresses) page. RLUSD has 18 decimals.
- A transfer from the zero address is a mint and a transfer to it is a burn. Holders are addresses with a balance above zero.

Every number here comes from HyperSync. The supply the script rebuilds sits about 12.5M below `totalSupply()`, because some RLUSD was created before the first mint the script sees. Changes over a window are exact, so the 30-day figures line up with the contract.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py        # last 30 days
python3 script.py 90     # last 90 days
```

All of RLUSD's history takes a few minutes. Sample output from a run on 13 Nov 2026.

```
RLUSD on Ethereum, 596,345 transfers, up to 13 Nov 2026 12:08 UTC
Supply now 1,905.4M, 30 days ago 1,347.5M, change +557.9M (+41%)
Minted 803.4M and burned 245.6M in the last 30 days
Holders with a balance: 11,678
```

The window ends at the latest block, so your numbers will differ.

## Change the window or chain

- **Window.** The argument is the number of days to look back. The query starts at `START` (block 20,900,000, before RLUSD was deployed), so leave that alone unless you only need recent days.
- **Chain.** Ripple lists RLUSD's other deployments on its [token addresses](https://docs.ripple.com/products/stablecoin/overview/token-addresses) page. For an EVM chain, change `HS` to its endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `RLUSD` to the address there.

## Check the numbers

As the comparison, `totalSupply()` over RPC was 1,365.6M at block 26,189,943 (14 Oct, 09:48 UTC) and 1,917.9M at block 26,405,943 (13 Nov, 12:08 UTC), a rise of 552.35M. HyperSync mints minus burns between the same two blocks also give 552.35M.

```bash
cast call 0x8292Bb45bf1Ee4d140127049757C2E0fF06317eD "totalSupply()(uint256)" \
  --rpc-url https://ethereum-rpc.publicnode.com --block 26405943
```

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every RLUSD Transfer on
Ethereum and rebuild supply and holder balances from mints and burns. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Write the supply at the end of every UTC day since launch to a CSV, along with
the number of holders that day. Keep the standard library only. Then check the
change between two days against RLUSD totalSupply() at the first block of each.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Raw HTTP query examples](https://docs.envio.dev/docs/HyperSync/hypersync-curl-examples), the same plain requests this script makes
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [RLUSD token addresses](https://docs.ripple.com/products/stablecoin/overview/token-addresses)
- [Envio Discord](https://discord.gg/envio)
