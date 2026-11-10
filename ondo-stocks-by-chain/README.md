# Ondo Stocks by chain

Reads every transfer of every Ondo stock and ETF token on Ethereum, BNB Chain, HyperEVM and Robinhood for one week, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints how many transfers each chain carried, what they were worth, the most-moved tickers, and every LayerZero bridge hop an Ondo stock made between those chains.

These are the numbers behind Envio's post on where Ondo stocks moved in the week of 3 November 2026. That week $402M of Ondo stocks moved onchain, split almost evenly between BNB Chain ($204M) and Ethereum ($198M). BNB Chain needed about 13 times as many transfers to do it, with an average transfer of $217 against $2.8K on Ethereum.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It covers the 7 full UTC days before today. Pass a start date to choose another week:

```bash
python script.py 2026-11-03
```

A week takes two or three minutes. BNB Chain has close to a million transfers, so the script splits each chain's blocks into 8 parts and reads them in parallel. It also writes everything to `results.json`.

## What it prints

```
Ondo stocks by chain, 2026-11-03 to 2026-11-10 (UTC, end exclusive)

Transfers 1,006,976   value $402.1M at today's prices

Ethereum      69,897 transfers   $198.4M   49.4%  avg   $2.8K  3,341 wallets
           TSLAon $22.9M, SPCXon $13.6M, LMTon $12.9M, MUon $11.5M, METAon $10.6M
           left out 938 transfers from 1 wallet cycling volume
BNB Chain    936,890 transfers   $203.6M   50.6%  avg    $217  26,693 wallets
           FXIon $41.9M, NVDAon $27.6M, SOXLon $12.9M, MUon $8.8M, QQQon $7.2M
           left out 29,110 transfers from 248 wallets cycling volume
HyperEVM           9 transfers      $113    0.0%  avg     $13  3 wallets
           METAon $107, GOOGLon $6
Robinhood        180 transfers    $24.8K    0.0%  avg    $138  74 wallets
           QQQon $12.4K, NVDAon $6.6K, TSLAon $2.9K, GOOGLon $2.1K, CRCLon $446

Bridge hops (LayerZero) 74, $1.3M
  BNB Chain -> Ethereum  66
  BNB Chain -> HyperEVM  3
  HyperEVM -> BNB Chain  3
  Ethereum -> BNB Chain  1
  BNB Chain -> Robinhood  1
```

## How it counts

- Token addresses come from Ondo's token sheet, linked from the Ondo Stocks section of [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses). The script downloads it on every run. It keeps the 450 tokens marked Stock or ETF and leaves out USDon and the portfolio tokens.
- One HyperSync query per chain reads every `Transfer` log from those token contracts, with the transaction that contains it (HyperSync's default join). Only logs whose address is an Ondo token and whose first topic is `Transfer` are kept. The wallet is the address that sent the transaction.
- Value is each transfer's amount times the token's price on CoinGecko when you run the script, using the CoinGecko ids in Ondo's sheet. Every Ondo stock token has 18 decimals. Because it uses today's price, it is an estimate of the week's value, not the price at the time of each transfer. A swap that routes through several contracts counts once per hop.
- Wash check: when one wallet moves the same token through its own address 20 or more times in a New York day and ends the day within 10% of where it started, those transactions are one actor cycling volume and are left out of every number. Mints, burns and transfers with Ondo's own mint and redeem contracts (GMTokenManager, GMIssuerManager and GMTokenLimitOrder from the addresses page) don't count towards it, because that is issuance, not trading.
- A bridge hop is a LayerZero `OFTSent` event in the same transaction as an Ondo token burn. Its destination comes from the event's LayerZero endpoint id (Ethereum 30101, BNB Chain 30102, HyperEVM 30367, Robinhood 30416).
- Solana is not included. Ondo Stocks also live there, but this recipe reads EVM chains only.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of every
Ondo stock token on Ethereum (1), BNB Chain (56), HyperEVM (999) and Robinhood (4663) for the last 7 days.
Token addresses are in the token sheet linked from https://docs.ondo.finance/addresses.
My API token is in the ENVIO_API_TOKEN environment variable. Show transfers, value and wallets per chain,
the most-moved tickers, and LayerZero OFTSent bridge hops between the chains.
```

## Learn more

- [Ondo stocks on Robinhood](https://github.com/enviodev/hypersync-recipes/tree/main/ondo-stocks-robinhood): the first week of Ondo's tokenized stocks on Robinhood
- [Tokenized stocks on Ethereum](https://github.com/enviodev/hypersync-recipes/tree/main/tokenized-stocks-ethereum)
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
