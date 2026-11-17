# Where Ondo stocks moved, chain by chain

In the week of 3 to 9 Nov 2026, **$402M of Ondo stock and ETF tokens moved onchain across 1M transfers**, valued at CoinGecko prices on 10 Nov 2026, the day of the run. The value split almost evenly between BNB Chain ($204M) and Ethereum ($198M). BNB Chain did it in about 13 times as many transfers, with an average transfer of $217 against $2.8K on Ethereum. 74 LayerZero bridge hops moved $1.3M between the chains.

| Chain | Transfers | Value | Avg transfer | Wallets |
| --- | --- | --- | --- | --- |
| Ethereum | 69,897 | $198.4M | $2.8K | 3,341 |
| BNB Chain | 936,890 | $203.6M | $217 | 26,693 |
| Robinhood Chain | 180 | $24.8K | $138 | 74 |
| HyperEVM | 9 | $113 | $13 | 3 |

## Why it's interesting

Ondo issues the same 450 stock and ETF tokens on several chains, and each chain gets used differently. Ethereum carries fewer, larger transfers. BNB Chain carries a lot of small ones, and its top ticker that week was the FXI China ETF rather than a US tech name. If you're choosing where to list, build or market a stock token product, this is the per-chain picture in one run.

## What it pulls

- Token addresses from Ondo's token sheet, linked from the Ondo Stocks section of [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses). The script keeps the 450 tokens marked Stock or ETF and leaves out USDon and the portfolio tokens.
- Every ERC-20 `Transfer` log from those tokens on Ethereum (1), BNB Chain (56), HyperEVM (999) and Robinhood Chain (4663), with the transaction that sent it, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Transfer counts, wallets and bridge hops come from HyperSync.
- LayerZero `OFTSent` events in the same transaction as an Ondo token burn, from HyperSync. The destination comes from the LayerZero endpoint id (Ethereum 30101, BNB Chain 30102, HyperEVM 30367, Robinhood Chain 30416).
- Today's price for each token from CoinGecko's public price API, using the ids in Ondo's sheet. The dollar values come from these prices, not from HyperSync, and use the price on the day you run it rather than at the time of each transfer. These are prices of US stocks and ETFs, set off chain on the exchanges where the shares trade, and Ondo's sheet maps each token to a CoinGecko id. Chainlink publishes onchain feeds for only a handful of Ondo's tokens on Ethereum, and none for most of the 450 tokens on the four chains, so there is no onchain price HyperSync can read for the full set. That is why the script keeps the CoinGecko price. Transfer counts, wallets and token amounts are all from HyperSync, and only the dollar figure depends on this outside price.

Every Ondo stock token has 18 decimals. A swap that routes through several contracts counts once per hop. The wallet is the address that sent the transaction.

When one wallet moves the same token through its own address 20 or more times in a New York day and ends within 10% of where it started, those transfers are left out of every number. Mints, burns and transfers with Ondo's mint and redeem contracts (GMTokenManager, GMIssuerManager and GMTokenLimitOrder from the addresses page) don't count towards that, since they're issuance.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py               # the 7 full UTC days before today
python3 script.py 2026-11-03    # the week above
```

A week takes two or three minutes. BNB Chain has close to a million transfers, so the script splits each chain into 8 block ranges and reads them in parallel. It also writes everything to `results.json`. Sample output for the week above, run on 10 Nov 2026.

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

## Change the window or chain

- **Week.** Pass any start date as `YYYY-MM-DD` and the script reads the 7 days from there.
- **Chains.** Ondo also deploys on other chains. Add one by giving the script its HyperSync subdomain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), the matching column in Ondo's sheet, and its LayerZero endpoint id. Ondo's Solana tokens aren't covered here since this script reads EVM chains.
- **Value at the time.** To value each transfer at its own day's price instead of today's, swap the CoinGecko call for a daily price per token.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of every Ondo
stock and ETF token on Ethereum, BNB Chain, HyperEVM and Robinhood Chain for one week,
plus LayerZero OFTSent bridge hops. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add a per-day breakdown of transfers and wallets for each chain and write it to
daily.csv. Keep the standard library only. Then check that the daily transfer counts
for each chain add up to the weekly totals the script prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Ondo token addresses](https://docs.ondo.finance/addresses)
- [LayerZero endpoint ids](https://docs.layerzero.network/v2/deployments/deployed-contracts)
- [Envio Discord](https://discord.gg/envio)
