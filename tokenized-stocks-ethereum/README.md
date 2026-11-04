# Tokenized stocks on Ethereum

Reads every transfer of every Ondo Global Markets and xStocks stock token on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It counts the transactions each token appears in over the last 30 days and prints the tokens that move the most.

These are the numbers behind Envio's post on SpaceX being the most active tokenized stock on Ethereum.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It covers the last 30 full UTC days. Pass a number of days and an end date (exclusive) to rerun a past window exactly:

```bash
python script.py 30 2026-11-04
```

## What it prints

```
1843 Ondo and xStocks stock tokens on Ethereum
Transactions with a stock token transfer, 05 Oct to 03 Nov UTC  173,408
Tokens that moved  1,680
  SPCXon    SpaceX                         51,705   29.8%
  NVDAon    NVIDIA                         16,983    9.8%
  TSLAon    Tesla                          16,159    9.3%
  SPYon     SPDR S&P 500 ETF               10,286    5.9%
  STRCx     Strategy PP Variable            7,569    4.4%
  ...
```

## How it counts

- Ondo's Ethereum token addresses come from the token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses). Only stocks and ETFs are included.
- xStocks' Ethereum token addresses come from the product list at [xstocks.fi](https://xstocks.fi/us/products).
- A transaction counts for a token if it has at least one Transfer of that token, including mints and burns. A transaction that moves two stock tokens counts once in the total.
- Transactions are grouped by UTC day from block timestamps.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Ethereum to read every
Transfer event of the Ondo Global Markets stock tokens (addresses from the token sheet at
https://docs.ondo.finance/addresses) and the xStocks tokens (addresses from https://xstocks.fi/us/products).
My API token is in the ENVIO_API_TOKEN environment variable.
Count transactions per token per day for the last 30 days and chart the top 10.
