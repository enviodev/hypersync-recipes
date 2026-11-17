# Ostium's biggest markets on Arbitrum

In the 30 days to 00:00 UTC on 5 Nov 2026, **traders opened $57.1M of positions on [Ostium](https://www.ostium.com), and 80.2% of that size was outside crypto**. Indices led with $34.9M, mostly the S&P 500 (US500, $18.3M) and the Nasdaq 100 (US100, $15.6M). That came from 6.7K trades by 335 traders.

| Asset group | Size opened | Share of size | Share of trades |
| --- | --- | --- | --- |
| Indices | $34.9M | 61.1% | 18.8% |
| Crypto | $11.3M | 19.8% | 47.7% |
| Forex | $7.2M | 12.6% | 9.1% |
| Commodities | $2.8M | 5.0% | 10.6% |
| Stocks | $0.9M | 1.5% | 12.2% |
| ETFs | $0.0M | 0.0% | 1.7% |

## Why it's interesting

Ostium lists perps on stock indices, forex, commodities and stocks next to crypto, all settled onchain in USDC. Crypto pairs get almost half the trades but indices get most of the size, so trade counts and dollar size tell very different stories here. Every position is an event, so you can rebuild the whole picture from the chain.

## What it pulls

- Every `MarketOpenExecuted` and `LimitOpenExecuted` log from Ostium's TradingCallbacks contract, `0x7720fC8c8680bF4a1Af99d44c6c265a74e9742a9`. Each position's size is collateral times leverage, in USDC. Event layouts come from `IOstiumTradingCallbacks.sol` in [Ostium's contracts repo](https://github.com/0xOstium/smart-contracts-public).
- Pair names and asset groups from Ostium's PairsStorage contract (`0x260E349F643f12797fDc6f8c9d3df211D5577823`) with `pairs(i)` and `groups(g)`, through Arbitrum's public RPC.
- Open interest for every pair from `openInterest(pair, 0)` and `openInterest(pair, 1)` on TradingStorage (`0xccd5891083a8acd2074690f65d3024e7d13d66e7`), also through Arbitrum's public RPC.
- Live mid prices and display names from Ostium's [Builder API](https://docs.ostium.com/developer/builder-api/get-prices).

All three contract addresses are in the mainnet table in [Ostium's docs](https://docs.ostium.com/protocol/security/audits).

The positions opened, their size, trades and traders come from HyperSync. Open interest comes from public RPC calls, valued at Ostium's live API prices, with pairs quoted in yen, euros, pounds or Hong Kong dollars converted with Ostium's own FX pairs. The contract calls two of the indices `SPX/USD` and `NDX/USD`, and the script prints the app's names, US500 and US100. Only new positions count, not closes, take profits, stop losses or liquidations.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # 30 days ending at 00:00 UTC today
python3 script.py 2026-11-05   # 30 days ending at 00:00 UTC on 5 Nov 2026, as above
```

Sample output for `2026-11-05`.

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

The 30-day window is fixed by the date, so the positions part stays the same. Open interest is read live, so that part changes every time you run it.

## Change the window or chain

- **Window.** Pass the end date. The window is the 30 full UTC days before 00:00 on that date, found by binary search on block timestamps. For a different length, change the `30 * 86400` in the script.
- **Chain.** Ostium runs on Arbitrum. To reuse the pattern for another protocol, swap `HS` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and the event signatures and contracts for that protocol's.

## Check the numbers

As a comparison, Ostium runs its own subgraph at `https://builder.prod.bedrock.ostium.io/v1/subgraph/gn`. Its `orders` with `orderAction: "Open"` matched the opened totals trade for trade for the same window, and the `longOI` and `shortOI` fields on its `pairs` matched the open interest.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every
MarketOpenExecuted and LimitOpenExecuted event from Ostium's TradingCallbacks
contract on Arbitrum and groups position size by pair and asset group. My
HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a weekly breakdown, with size opened per asset group for each 7-day block of
the window, and split each group into longs and shorts using the buy flag in the
Trade struct. Keep the standard library only. Run it for 2026-11-05 and check
that the weekly sizes add up to the $57.1M total.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Ostium docs](https://docs.ostium.com)
- [Ostium contracts](https://github.com/0xOstium/smart-contracts-public)
- [Envio Discord](https://discord.gg/envio)
