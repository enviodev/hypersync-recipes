# Uniswap stock tokens after hours on Robinhood

Reads every Uniswap v4 swap of a Robinhood Stock Token on Robinhood with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), values it in USD and splits it by whether the US stock market was open. It prints the share of volume, swaps and wallets that traded while the market was closed (nights, weekends and NYSE holidays), the busiest stock tokens after hours, and writes an hour-by-weekday grid in New York time to `heatmap.json`.

These are the numbers behind Envio's post on stock-token trading outside US market hours.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It covers the 30 days up to the start of today (UTC). Pass two UTC dates to choose the window, start inclusive and end exclusive:

```bash
python script.py 2026-10-11 2026-11-10
```

## What it prints

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

"Swaps read" includes the ETH/USDG swaps used to price ETH. "night" is any weekday time outside 9:30 to 16:00, so it includes the early morning before the open. There were no NYSE holidays in this window; Labor Day (7th Sep) falls in a window that starts in August. The market is open for 32.5 of the week's 168 hours, about 19%, so 39% of the volume in that time still makes the regular session the busiest stretch. The half hour from 9:30 to 10:00, summed over the weekdays in the window, is busier than any full hour of the day.

The pull takes about 30 minutes for 30 days of swaps.

## Check it against Uniswap's SPY numbers

Uniswap wrote that ten stock tokens started trading against SPY on Robinhood in August, and that more than 40 now have SPY pools "with over $900 million in volume across 130,000 wallets". Pass `--spy` to count only the pools that pair a stock token with SPY:

```bash
python script.py 2026-08-01 2026-11-11 --spy
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

That is $892M across 130,729 wallets with cycling left out, and $1.01B with it counted, against Uniswap's "over $900 million" and 130,000 wallets. Uniswap doesn't say how it values swaps or filters volume, so the two won't match exactly. The holiday row is Labor Day.

## How it counts

- The PoolManager comes from Uniswap's [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments): `0x8366a39cc670b4001a1121b8f6a443a643e40951` on Robinhood (chain 4663).
- The 203 Robinhood Stock Tokens come from Robinhood's asset API, `GET https://api.robinhood.com/rhj/assets`, documented on the [Stock Token APIs page](https://docs.robinhood.com/chain/stock-token-apis/). USDG and WETH come from the [contracts page](https://docs.robinhood.com/chain/contracts/).
- A pool counts when a stock token trades against USDG, ETH or another stock token. Pools are found from the `Initialize` event on the PoolManager, filtered by token in its topics. Pools that pair a stock token with any other token are left out, because those are trades in that other token.
- Every `Swap` on the PoolManager in those pools is read with the transaction that contains it (HyperSync's default join), so the wallet is the address that sent the transaction.
- A swap's size in USD is its USDG side. Otherwise it is the stock token (or ETH) side times that day's price, the volume-weighted median of the token's swap prices against USDG that day, then against ETH, then against SPY.
- The market is open 9:30 to 16:00 New York time on weekdays. Weekends and NYSE holidays from the [NYSE calendar](https://www.nyse.com/trade/hours-calendars) count as closed. Daylight saving is handled by Python's `zoneinfo`.
- Wash check: when one wallet swaps the same pool 20 or more times in a New York day and ends within 10% of where it started (bought and sold within 10% of each other), those swaps are one actor cycling volume and are left out of every number.
- A swap between two stock tokens, for example against SPY, counts once in the totals and once for each token in the per-token list.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Robinhood (chain 4663,
endpoint https://robinhood.hypersync.xyz) to read every Swap on the Uniswap v4 PoolManager
0x8366a39cc670b4001a1121b8f6a443a643e40951 in pools holding a Robinhood Stock Token
(addresses from https://api.robinhood.com/rhj/assets). My API token is in the ENVIO_API_TOKEN
environment variable. Value each swap in USD and show how much traded while the NYSE was closed,
as a 7 x 24 grid in New York time.
```

## Learn more

- [Robinhood on Envio](https://envio.dev/chains/robinhood): HyperSync and HyperIndex support for Robinhood
- [Uniswap v4 hooks on Robinhood](https://github.com/enviodev/hypersync-recipes/tree/main/uniswap-v4-hooks-robinhood): every v4 pool and hook on Robinhood
- [Ondo stocks on Robinhood](https://github.com/enviodev/hypersync-recipes/tree/main/ondo-stocks-robinhood): the first week of Ondo's tokenized stocks on Robinhood
- [Uniswap v4 multichain indexer example](https://docs.envio.dev/docs/HyperIndex/example-uniswap-v4-multi-chain-indexer): index v4 pools and swaps across chains
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
