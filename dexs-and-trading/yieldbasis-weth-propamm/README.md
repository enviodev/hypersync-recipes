# Yield Basis yb-WETH, the first week on oracle pricing

In its first 7 days on oracle pricing, from 29 Oct 2026 11:38 UTC (block 26,298,152), **the Yield Basis WETH pool on Ethereum traded $28.9M, 6.8x the $4.2M of the week before**. Those swaps paid $424K in fees, across 280 swaps from 86 wallets.

| First 7 days | |
| --- | --- |
| Volume | $28.9M |
| Week before | $4.2M |
| Fees | 210,073 crvUSD + 83.32 WETH ($424K) |
| Swaps | 280 |
| Wallets | 86 |
| Largest swap | $5.84M |

## Why it's interesting

A propAMM prices swaps off an external oracle instead of its own curve. This pool started pricing off signed Pyth ETH/USD reports after a governance vote, so you can line up volume before and after one onchain event and see what changed. The same pattern works for any pool upgrade. Find the event that switched it on, then compare the swaps either side.

## What it pulls

All of it comes from HyperSync.

- The pool's last `SetPolicyContract` log, which marks when the policy contract that prices swaps off Pyth reports went live. It was installed by Curve vote 1508 alongside [Yield Basis proposal #60](https://yieldbasis.com/proposal/60).
- Every `TokenExchange` log on the crvUSD/WETH pool behind Yield Basis market 10 (yb-WETH), [`0x656341Ef90b622c6634e0573772FfB7f3669b9f3`](https://etherscan.io/address/0x656341Ef90b622c6634e0573772FfB7f3669b9f3), from about a week before the switch onwards.
- The block timestamp and the transaction sender for each swap.

Volume is the crvUSD side of each swap at $1. Swaps under $1 are zero-size calls rather than trades, so they're left out. Fees are the `fee` field of each swap, paid in the coin bought, and WETH fees are valued at that swap's own price, so there's no outside price feed. Wallets are the addresses that sent the swap transactions, so a trade routed through a solver shows the signer. Days are 24 hour blocks from the switch, not calendar days.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
python3 script.py --hourly   # also prints volume for each of the 168 hours, for charting
```

Sample output.

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

The week is fixed to the 7 days after the switch, so these numbers won't change.

## Change the window or pool

- **Window.** `WEEK` sets the length of both windows, in seconds. Make it `30 * 86400` to compare 30 days either side. The swap scan starts 60,000 blocks (about 8 days) before the switch, so raise that number in the `logs(TOKEN_EXCHANGE, ...)` call too. The `--hourly` output and the by-day table are sized for 7 days.
- **Pool.** `POOL` is the pool address. Other Yield Basis markets have their own Curve pool, returned by the Yield Basis factory for `markets(i)`. A pool that never emitted `SetPolicyContract` needs a different start point, such as a block number.
- **Chain.** For a pool on another chain, change the HyperSync URL in `query()` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).

## Check the numbers

Paste the largest swap's transaction hash into [Etherscan](https://etherscan.io/tx/0x4fa182626c85ca0cdc18ba736930bdbdfbcf5d201d373913317df6ec58d23d61) and the decoded `TokenExchange` log should show the same amounts and fee. The [pool's events on Etherscan](https://etherscan.io/address/0x656341Ef90b622c6634e0573772FfB7f3669b9f3#events) also list the `SetPolicyContract` transaction at block 26,298,152.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find when the Yield Basis
yb-WETH pool on Ethereum (0x656341Ef90b622c6634e0573772FfB7f3669b9f3) switched
to oracle pricing, then reads every TokenExchange in the week before and after.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Extend it to cover every week since the switch, not only the first. Print one
row per week with volume, fees, swaps and wallets, and write the hourly volume
to a CSV. Keep the standard library only. Then check that the first week's row
still shows $28.9M volume and 280 swaps.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Yield Basis docs](https://docs.yieldbasis.com/dev/overview)
- [Yield Basis proposal #60](https://yieldbasis.com/proposal/60)
- [Envio Discord](https://discord.gg/envio)
