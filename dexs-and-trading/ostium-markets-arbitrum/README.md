# Ostium's biggest markets on Arbitrum

Reads every position opened on [Ostium](https://www.ostium.com) on Arbitrum over the last 30 days with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then groups the size of those positions by pair and by asset group: indices, forex, commodities, stocks, ETFs and crypto. It also reads open interest for every pair straight from Ostium's contracts.

These are the numbers behind Envio's post on Ostium's biggest markets.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py              # 30 days ending at the last 00:00 UTC
python script.py 2026-11-05   # 30 days ending at 00:00 UTC on that date
```

## What it prints

```
Ostium on Arbitrum, positions opened 2026-10-06 to 2026-11-05 (UTC, 30 days)
  $57.1M opened across 6,663 trades by 335 traders

By asset group         size   share of size   share of trades
  Indices      $    34.9M       61.1%          18.8%
  Crypto       $    11.3M       19.8%          47.7%
  Forex        $     7.2M       12.6%           9.1%
  Commodities  $     2.8M        5.0%          10.6%
  Stocks       $     0.9M        1.5%          12.2%
  ETFs         $     0.0M        0.0%           1.7%
  Not crypto   $    45.8M       80.2%          52.3%

Top 10 pairs
  US500/USD  Indices      $    18.3M   32.1%      299 trades
  US100/USD  Indices      $    15.6M   27.3%      648 trades
  EUR/USD    Forex        $     4.3M    7.6%      308 trades
  BTC/USD    Crypto       $     3.2M    5.7%    1,129 trades
  USD/JPY    Forex        $     2.2M    3.9%      101 trades
  SOL/USD    Crypto       $     2.2M    3.9%      494 trades
  ETH/USD    Crypto       $     2.0M    3.5%      392 trades
  XAU/USD    Commodities  $     1.7M    3.0%      397 trades
  XRP/USD    Crypto       $     1.3M    2.3%      192 trades
  HYPE/USD   Crypto       $     1.1M    2.0%      508 trades
  Top 2 together: 59.4%

Open interest now $7.6M
  Forex        $     2.7M   35.5%
  Commodities  $     2.4M   31.2%
  Indices      $     1.1M   14.2%
  Stocks       $     0.8M   11.0%
  ETFs         $     0.3M    4.6%
  Crypto       $     0.3M    3.5%
  Not crypto   $     7.3M   96.5%
Top 5 pairs by open interest
  EUR/USD    $     2.2M   29.6%
  XAU/USD    $     1.2M   15.7%
  US500/USD  $     1.0M   13.3%
  XCU/USD    $     0.5M    7.2%
  BRENT/USD  $     0.5M    6.1%
```

Open interest is read live, so that part changes every time you run it.

## How it counts

- Contract addresses come from the mainnet table in [Ostium's docs](https://docs.ostium.com/protocol/security/audits). Event layouts come from `IOstiumTradingCallbacks.sol` in [Ostium's contracts repo](https://github.com/0xOstium/smart-contracts-public).
- A new position is a `MarketOpenExecuted` or `LimitOpenExecuted` event from the TradingCallbacks contract (`0x7720fC8c8680bF4a1Af99d44c6c265a74e9742a9`). Its size is collateral times leverage, in USDC.
- Pair names and asset groups are read from Ostium's PairsStorage contract with `pairs(i)` and `groups(g)`, so nothing is guessed. Ostium's app shows two of the contract names differently: `SPX/USD` is US500 and `NDX/USD` is US100. The script prints the app names from Ostium's price API.
- The window is 30 full UTC days, found by block timestamp.
- Open interest is long plus short notional from `openInterest(pair, 0)` and `openInterest(pair, 1)` on TradingStorage, valued at Ostium's live mid prices from its [Builder API](https://docs.ostium.com/developer/builder-api/get-prices). Pairs quoted in yen, euros, pounds or Hong Kong dollars are converted with Ostium's own FX pairs.
- Closes, take profits, stop losses and liquidations are not counted, only new positions.

## Check it another way

The opened totals match Ostium's own subgraph (`https://builder.prod.bedrock.ostium.io/v1/subgraph/gn`, `orders` with `orderAction: "Open"`) for the same window, trade for trade. Open interest matches the `longOI` and `shortOI` fields on the subgraph's `pairs`.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every MarketOpenExecuted
and LimitOpenExecuted event from Ostium's TradingCallbacks contract on Arbitrum
(0x7720fC8c8680bF4a1Af99d44c6c265a74e9742a9). My API token is in the ENVIO_API_TOKEN environment
variable. Size each position as collateral x leverage, name pairs with pairs(i) on PairsStorage
(0x260E349F643f12797fDc6f8c9d3df211D5577823), and chart weekly new position size by asset group.
```
