# Stock token trading on Uniswap after the bell, on Robinhood Chain

From 11 Oct to 9 Nov 2026, **60.6% of Robinhood Stock Token volume on Uniswap v4 traded while the US stock market was closed**. That's $888M from 2.7M swaps and 77K wallets in all, and 83% of those wallets traded at least once outside market hours. SPY was the busiest token after hours at $271M.

| Session | Volume | Share | Swaps | Wallets |
| --- | --- | --- | --- | --- |
| Market open | $350.2M | 39.4% | 1,152,408 | 38,171 |
| Weekday nights | $444.7M | 50.1% | 1,219,805 | 52,102 |
| Weekends | $93.1M | 10.5% | 370,643 | 27,450 |

## Why it's interesting

Stock tokens trade around the clock, so the obvious question is whether anyone actually trades them when Wall Street is shut. They do. The market is open for 32.5 of the week's 168 hours, about 19%, and still takes 39% of the volume, so the regular session is the busiest stretch per hour. The half hour from 9:30 to 10:00 New York time, summed over the window, is busier than any full hour of the day.

The script also shows a full Uniswap v4 pattern you can reuse. Find pools from `Initialize`, read every `Swap` with the sender's wallet, and price each swap from onchain trades alone.

## What it pulls

- The 203 Robinhood Stock Tokens from Robinhood's asset API, `GET https://api.robinhood.com/rhj/assets`, documented on the [Stock Token APIs page](https://docs.robinhood.com/chain/stock-token-apis/). USDG and WETH come from the [Robinhood Chain contracts page](https://docs.robinhood.com/chain/contracts/).
- Every `Initialize` and `Swap` on the Uniswap v4 PoolManager [`0x8366a39cc670b4001a1121b8f6a443a643e40951`](https://developers.uniswap.org/docs/protocols/v4/deployments) on Robinhood Chain (chain 4663), with each swap's transaction, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Every number here comes from HyperSync.

A pool counts when a stock token trades against USDG, ETH or another stock token. A swap's dollar size is its USDG side, with USDG taken as $1. Otherwise it's the token side times that day's volume-weighted median price from the token's own swaps against USDG, then ETH, then SPY. The wallet is the address that sent the transaction.

The market is open 9:30 to 16:00 New York time on weekdays. Weekday time outside that counts as night, so it includes the early morning before the open. Weekends and NYSE holidays from the [NYSE calendar](https://www.nyse.com/trade/hours-calendars) count as closed. There were no NYSE holidays in this window.

When one wallet swaps the same pool 20 or more times in a New York day and ends within 10% of where it started, those swaps are left out of every number. In this window that set aside 790K swaps and $151M.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                          # the 30 days up to the start of today (UTC)
python3 script.py 2026-10-11 2026-11-10    # the window above, end date exclusive
```

It takes about 30 minutes for 30 days of swaps and writes an hour-by-weekday grid in New York time to `heatmap.json` (`heatmap-spy.json` with `--spy`). Sample output for the window above.

```
Robinhood Stock Tokens: 203
Uniswap v4 pools trading a stock token against USDG, ETH or another stock token: 13,235 (120 against SPY)
Swaps read: 6,578,742 (blocks 85,401,778 to 110,459,116)

Robinhood Stock Tokens on Uniswap v4, 2026-10-11 to 2026-11-10 (UTC, end exclusive)
Volume   $888,054,737 from 2,742,856 swaps and 77,295 wallets
Excluded as single-wallet cycling: 790,256 swaps, $151,040,216. Unpriced swaps: 0
US market closed: 60.6% of volume, 58.0% of swaps, 83.0% of wallets traded at least once while it was closed
  open     $   350,226,826   39.4%    1,152,408 swaps   42.0%     38,171 wallets
  night    $   444,705,867   50.1%    1,219,805 swaps   44.5%     52,102 wallets
  weekend  $    93,122,044   10.5%      370,643 swaps   13.5%     27,450 wallets
  holiday  $             0    0.0%            0 swaps    0.0%          0 wallets
Busiest stock tokens while the market is closed (volume in pools holding the token):
  SPY    $  271,061,578   58.0% of its volume
  TTWO   $   69,015,092   98.7% of its volume
  NVDA   $   52,949,773   58.8% of its volume
  ...
```

"Swaps read" includes the ETH/USDG swaps used to price ETH. A swap between two stock tokens counts once in the totals and once for each token in the per-token list.

## Change the window or chain

- **Window.** Pass two UTC dates, start inclusive and end exclusive. A shorter window runs faster.
- **SPY pools.** Add `--spy` to count only the pools that pair a stock token with SPY.
- **Market hours.** The holiday and early-close lists are constants near the top, and the 9:30 open and 16:00 close are in `market_open()`. Change them to test a different session, like the hour before the open.
- **Chain.** Uniswap v4 runs on many chains. Swap `URL` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), the PoolManager for that chain's address from the [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments), and the token list for the stock tokens on that chain.

## Check the numbers

Uniswap has published a figure for the SPY pools on Robinhood Chain, "over $900 million in volume across 130,000 wallets", which works as an outside comparison. Run the SPY-only count from August.

```bash
python3 script.py 2026-08-01 2026-11-11 --spy
```

```
Robinhood Stock Tokens on Uniswap v4 in pools against SPY, 2026-08-01 to 2026-11-11 (UTC, end exclusive)
Volume   $892,089,124 from 2,707,016 swaps and 130,729 wallets
Excluded as single-wallet cycling: 588,203 swaps, $122,705,903. Unpriced swaps: 0
US market closed: 59.7% of volume, 63.0% of swaps, 85.5% of wallets traded at least once while it was closed
  open     $   359,355,931   40.3%    1,000,716 swaps   37.0%     56,474 wallets
  night    $   388,208,185   43.5%    1,177,132 swaps   43.5%     83,284 wallets
  weekend  $   135,730,709   15.2%      499,574 swaps   18.5%     54,669 wallets
  holiday  $     8,794,299    1.0%       29,594 swaps    1.1%      7,844 wallets
```

That's $892M across 131K wallets with repeated same-wallet swaps left out, and $1.01B with them counted. Uniswap doesn't say how it values or filters volume, so the two won't match exactly. The holiday row is Labor Day.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Robinhood Chain to read every
Uniswap v4 swap in pools holding a Robinhood Stock Token, values each swap in USD and
splits volume by US market hours. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add a per-day table of after-hours share for the five busiest tokens and write it to
after_hours_daily.csv. Keep the standard library only. Run it on a 7-day window first.
Then check that the daily volumes for each token add up to the per-token total the
script prints for the same window.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Robinhood Chain on Envio](https://envio.dev/chains/robinhood)
- [Uniswap v4 multichain indexer example](https://docs.envio.dev/docs/HyperIndex/example-uniswap-v4-multi-chain-indexer)
- [Robinhood Stock Token APIs](https://docs.robinhood.com/chain/stock-token-apis/)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Envio Discord](https://discord.gg/envio)
