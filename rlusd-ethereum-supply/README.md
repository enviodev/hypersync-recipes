# RLUSD supply on Ethereum, from every mint and burn

Reads every `Transfer` event of Ripple USD (RLUSD) on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Transfers from the zero address count as mints and transfers to it count as burns. The script prints the change in supply over the last 30 days, what was minted and burned, and how many wallets hold RLUSD.

These are the numbers behind Envio's post on RLUSD growing 40% on Ethereum in the month that total stablecoin supply shrank.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py        # last 30 days
python script.py 90     # last 90 days
```

All of RLUSD's history (about 596k transfers) takes a few minutes.

## What it prints

```
RLUSD on Ethereum, 596,345 transfers, up to 13 Nov 2026 12:08 UTC
Supply now 1,905.4M, 30 days ago 1,347.5M, change +557.9M (+41%)
Minted 803.4M and burned 245.6M in the last 30 days
Holders with a balance: 11,678
```

That run was on 13th Nov 2026. The 30-day window ends at the latest block, so the numbers shift with each run.

## How it counts

- The token is the RLUSD proxy `0x8292Bb45bf1Ee4d140127049757C2E0fF06317eD` from Ripple's [token addresses](https://docs.ripple.com/products/stablecoin/overview/token-addresses) page. RLUSD has 18 decimals.
- The query asks for `Transfer` logs on that address. It uses HyperSync's default join, and the script only keeps logs whose address and topic0 match.
- The absolute supply the script prints is about 12.5M below `totalSupply()`, because some supply was created before the first `Transfer` from the zero address that the script sees. Changes over a window are exact.
- Checked over RPC: `totalSupply()` was 1,365.6M at block 26,189,943 (14 Oct, 09:48 UTC) and 1,917.9M at block 26,405,943 (13 Nov, 12:08 UTC), a rise of 552.35M. HyperSync mints minus burns between those two blocks also give 552.35M.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Ethereum (endpoint
https://eth.hypersync.xyz) to read every Transfer event of RLUSD
0x8292Bb45bf1Ee4d140127049757C2E0fF06317eD. My API token is in the ENVIO_API_TOKEN environment
variable. Treat transfers from the zero address as mints and to the zero address as burns, and show
the daily supply and the change over the last 30 days.
```
