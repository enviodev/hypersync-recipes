# Yield Basis yb-WETH propAMM, first week

Reads every swap on the Yield Basis WETH pool on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), for the 7 days after the pool switched to oracle pricing and the 7 days before. It prints volume, fees, wallets, a day by day split, the busiest hour, the largest swap and how much of the volume came from the most active wallets.

These are the numbers behind Envio's post on the yb-WETH propAMM.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Add `--hourly` to also print volume for each of the 168 hours, for charting.

## What it prints

```
Yield Basis yb-WETH propAMM, first 7 days
  Oracle pricing live from 2026-10-29 11:38 UTC (block 26298152)
  Volume  $28.9M   (6.8x the $4.2M of the 7 days before)
  Fees    210,073 crvUSD + 83.32 WETH, $424K with WETH at each swap's price
  Swaps   280   Wallets 86
  By day (24 hours from the switch)
    day 1  $ 23.06M volume  $ 388.7K fees  117 swaps  69 wallets
    day 2  $  0.98M volume  $   6.6K fees   40 swaps  27 wallets
    day 3  $  0.08M volume  $   0.4K fees    9 swaps   8 wallets
    day 4  $  0.46M volume  $   2.8K fees   13 swaps  11 wallets
    day 5  $  0.41M volume  $   3.5K fees   17 swaps  14 wallets
    day 6  $  1.59M volume  $   9.1K fees   37 swaps  24 wallets
    day 7  $  2.33M volume  $  13.0K fees   47 swaps  23 wallets
  Day 1 share: 80% of volume, 92% of fees
  Busiest clock hour  $11.9M  from 2026-10-29 20:00 UTC
  Largest swap  $5.84M with $104K fee  0x4fa182626c85ca0cdc18ba736930bdbdfbcf5d201d373913317df6ec58d23d61
  Top wallet 20%, top 5 47%, top 10 57% of volume
```

The week is fixed to the 7 days after the switch, so these numbers will not change.

## How it counts

- The pool is the crvUSD/WETH Curve pool behind Yield Basis market 10 (yb-WETH), `0x656341Ef90b622c6634e0573772FfB7f3669b9f3`. The Yield Basis factory returns it for `markets(10)`.
- The start of the week is the pool's last `SetPolicyContract` event. That is when Curve vote 1508, paired with [Yield Basis proposal #60](https://yieldbasis.com/proposal/60), installed the policy contract that prices swaps off signed Pyth ETH/USD reports.
- A swap is a `TokenExchange` event on the pool. Volume is the crvUSD side of each swap, valued at $1. Swaps under $1 are left out, since these are zero-size calls rather than trades.
- Fees are the `fee` field of each swap, paid in the coin bought. WETH fees are valued at that swap's own price. Valuing them at another ETH price moves the dollar total by a few percent, so the script also prints the raw crvUSD and WETH amounts.
- Wallets are the addresses that sent the swap transactions. A wallet that trades through a router or a solver shows up as the address that signed the transaction.
- Days are 24 hour blocks from the switch, not calendar days. The busiest hour is a UTC clock hour.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every TokenExchange event on the
Yield Basis WETH pool on Ethereum (0x656341Ef90b622c6634e0573772FfB7f3669b9f3) since it switched to oracle
pricing. My API token is in the ENVIO_API_TOKEN environment variable. Chart daily volume and fees, and show
how much of the volume each of the top 10 wallets traded.
```
