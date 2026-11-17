# Which tokenized stocks move the most on Ethereum

Over the 30 days from 5 Oct to 3 Nov 2026, **173K Ethereum transactions moved at least one Ondo Global Markets or xStocks stock token**. Of the 1,843 tokens tracked, 1,680 moved at least once. SpaceX (SPCXon) led with 51.7K transactions, 29.8% of the total, across 3.6K wallets. NVIDIA, Tesla and the S&P 500 ETF came next.

| Token | Stock | Transactions | Share | Wallets |
| --- | --- | --- | --- | --- |
| SPCXon | SpaceX | 51,705 | 29.8% | 3,567 |
| NVDAon | NVIDIA | 16,983 | 9.8% | 2,205 |
| TSLAon | Tesla | 16,159 | 9.3% | 1,650 |
| SPYon | SPDR S&P 500 ETF | 10,286 | 5.9% | 3,727 |
| STRCx | Strategy PP Variable | 7,569 | 4.4% | 2,155 |

## Why it's interesting

There are close to two thousand stock tokens on Ethereum from two issuers, and you can't watch them one by one. This script reads every transfer of every one of them in a single pass and tells you which stocks people actually trade. It's a good base for a stock token leaderboard, an alert when a new listing takes off, or a daily activity chart.

## What it pulls

- The token list. Ondo's Ethereum addresses come from the token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses), keeping only stocks and ETFs. xStocks' Ethereum addresses come from the product list at [xstocks.fi](https://xstocks.fi/us/products).
- Every ERC-20 `Transfer` log from those contracts on Ethereum over the window, with block timestamps, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Every number in the table comes from HyperSync.

A transaction counts for a token if it has at least one transfer of that token, mints and burns included. A transaction that moves two stock tokens counts once in the total. Wallets are the distinct non-zero senders and receivers. Days are UTC, from block timestamps.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                  # the last 30 full UTC days
python3 script.py 30 2026-11-04    # the window used above (end date is exclusive)
```

Sample output for the window above.

```
1843 Ondo and xStocks stock tokens on Ethereum
Transactions with a stock token transfer, 05 Oct to 03 Nov UTC  173,408
Tokens that moved  1,680
  SPCXon    SpaceX                         51,705   29.8%   3,567 wallets  first 7 days 23,164  last 7 days  4,068
  NVDAon    NVIDIA                         16,983    9.8%   2,205 wallets  first 7 days  8,222  last 7 days  1,689
  TSLAon    Tesla                          16,159    9.3%   1,650 wallets  first 7 days  2,529  last 7 days  2,155
  SPYon     SPDR S&P 500 ETF               10,286    5.9%   3,727 wallets  first 7 days  6,914  last 7 days    462
  STRCx     Strategy PP Variable            7,569    4.4%   2,155 wallets  first 7 days  1,194  last 7 days  2,794
  ...
```

## Change the window or chain

- **Window.** The first argument is the number of days and the second is the end date, exclusive. `python3 script.py 7 2026-11-04` gives the last week of the window above.
- **Top N.** The script prints the top 10. Change the `[:10]` slice at the bottom to print more.
- **Chain.** Ondo and xStocks issue on other chains too. Swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), point the address lookups at that chain's addresses, and change the `7200` blocks per day in `first_block` to match the chain's block time.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of every Ondo
Global Markets and xStocks stock token on Ethereum and counts transactions per token.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a daily series for the top 10 tokens, one row per UTC day with the transaction
count for each token, and write it to daily.csv. Keep the standard library only.
Then check that the daily counts for SPCXon add up to the 30-day total the script
already prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Ondo token addresses](https://docs.ondo.finance/addresses)
- [xStocks products](https://xstocks.fi/us/products)
- [Envio Discord](https://discord.gg/envio)
