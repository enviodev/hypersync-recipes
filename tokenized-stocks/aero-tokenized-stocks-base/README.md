# Coinbase tokenized stocks on Aero, in and out of market hours

In the 7 days from 28 Oct to 4 Nov 2026 (09:40 UTC), **Coinbase's tokenized stocks did $780.8M of USDC-paired volume on Aero on Base, across 775K swaps, and 77.5% of it traded while US markets were closed**. $192.3M of that came on Saturday and Sunday. MSTRc and SNDKc led with $135.8M and $131.9M.

| Stock | USDC volume | Closed-market share | Weekend |
| --- | --- | --- | --- |
| MSTRc | $135.8M | 70.5% | $36.6M |
| SNDKc | $131.9M | 79.5% | $31.4M |
| METAc | $76.6M | 79.7% | $14.7M |

## Why it's interesting

Coinbase's stock tokens trade around the clock on Base, and Aero is where a lot of that liquidity sits. Most of the volume lands when Wall Street is shut, including a big weekend share. The script also shows how to cover a DEX with several pool factories in one pass, which is the awkward part of tracking Aero.

## What it pulls

- The stock token list from Coinbase's [Tokenized Stocks API](https://docs.base.org/sdks/tokenized-stocks/overview), `https://api.coinbase.com/v1/tokenized-stocks`.
- `PoolCreated` events from five pool factories on Base, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). That's the Aerodrome classic factory `0x420dd381b31aef6683db6b902084cb0ffece40da` ([contracts](https://github.com/aerodrome-finance/contracts)), three Slipstream deployments ([Slipstream](https://github.com/aerodrome-finance/slipstream)) and the Aero CL factory ([deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/blob/main/deployment-addresses/cl-base.json)).
- Every `Swap` in the pools that hold a stock token over the window, with block timestamps, from HyperSync. Every number here comes from HyperSync.

Volume is the USDC side of each swap in a stock/USDC pool, using [USDC on Base](https://basescan.org/token/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913). Swaps against other tokens aren't priced, so they're not in the totals. US markets count as open 9:30 to 16:00 New York time on weekdays. The script switches from EDT to EST on 1 Nov 2026 and doesn't know any other clock change, so windows after the March 2027 switch need that offset updated.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 7                         # the last 7 days
python3 script.py 7 2026-11-04T09:40:09     # the window above
```

Sample output for the window above.

```
Coinbase tokenized stocks on Aero (Base), 28 Oct 09:40 UTC to 04 Nov 09:40 UTC
Pools holding a stock: 1,999
USDC-paired volume: $780.8M across 774,920 swaps, 77.5% while US markets were closed
Saturday and Sunday (ET): $192.3M
  MSTRc    $  135.8M   70.5% closed  $  36.6M at the weekend
  SNDKc    $  131.9M   79.5% closed  $  31.4M at the weekend
  METAc    $   76.6M   79.7% closed  $  14.7M at the weekend
  ...
```

## Change the window or chain

- **Window.** The first argument is the number of days. Add an end time in UTC, like `2026-11-04T09:40:09`, to rerun a past window exactly. The block search only reaches back about seven times the window length from the latest block (50 days for a 7-day window), so an older end time needs a lower starting point in `first_block_after`.
- **Quote token.** Volume is priced from the USDC side. To include stock/ETH pools, add a WETH price from the same swaps and value the ETH side with it.
- **Token list.** Swap the Coinbase API call for any list of Base tokens to get the same in-hours and after-hours split for them.
- **Chain.** Aero's factories in this script are on Base. For another chain, swap `URL` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `FACTORIES` and `USDC` for that chain's addresses.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Base to find every Aero pool that
holds a Coinbase tokenized stock and sum USDC-paired swap volume in and out of US market
hours. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add an hour-by-weekday grid of USDC volume in New York time and write it to
heatmap.csv. Keep the standard library only. Then check that the grid adds up to the
total USDC-paired volume the script prints for the same window.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Coinbase tokenized stocks](https://docs.base.org/sdks/tokenized-stocks/overview)
- [Aerodrome contracts](https://github.com/aerodrome-finance/contracts)
- [Envio Discord](https://discord.gg/envio)
