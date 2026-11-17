# Grove Basin for JTRSY on Ethereum

Reads every event of Grove's JTRSY Basin on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Basin lets holders of JTRSY, the Janus Henderson Anemoy Treasury Fund token issued through Centrifuge, swap it for USDC in a single transaction. Basin then redeems the JTRSY with the issuer in the background. The script lists every swap, the largest one, and how long each of Basin's own redemptions took to settle. It also reads the liquidity standing in the Basin and the largest swap it allows.

These are the numbers behind Envio's post on Grove Basin.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
Grove Basin for JTRSY on Ethereum
  18 swaps of JTRSY into USDC, each in a single transaction (0 swaps in any other direction)
  325,224.600766 JTRSY in, $362,792.960896 USDC out
  Largest: 135,000.000000 JTRSY into $150,533.235000 USDC, 2026-09-11 18:07 UTC, tx 0x62b4e4ce14068d02f702138db15fd1e8dcd936a119d306dc37ca1b15f5fd8d5e
  Latest:  89,170.000000 JTRSY into $100,013.250340 USDC, 2026-11-04 14:35 UTC, tx 0x9e95519924bb12447fd3b5d76ad86b8f8f72a913ed21880bcd8cac6e447b7523
Basin's own redemptions of the JTRSY it took in
      1.000000 JTRSY  requested 2026-07-23 12:49 UTC  settled for $1.110401 USDC after 2.7 hours (0.1 days)
  1,000.000000 JTRSY  requested 2026-07-28 11:37 UTC  settled for $1,110.846688 USDC after 0.4 hours (0.0 days)
  100,000.000000 JTRSY  requested 2026-07-28 13:58 UTC  settled for $111,084.668810 USDC after 19.4 hours (0.8 days)
  135,051.802383 JTRSY  requested 2026-09-15 10:54 UTC  settled for $150,714.405820 USDC after 165.5 hours (6.9 days)
  89,171.798383 JTRSY  requested 2026-11-04 20:11 UTC  still settling
Liquidity in the Basin now: $100,000,042.81
Largest single swap allowed: $50,000,000
```

New swaps and redemptions change these numbers, so yours may differ.

## How it counts

- The Basin address comes from Grove's [deployed contracts page](https://docs.grove.finance/deployed-contracts) (`JTRSY_GROVE_BASIN`). Event signatures come from the contract's verified source (`GroveBasin`).
- A swap is a `Swap` event with JTRSY in and USDC out. JTRSY and USDC both use 6 decimals.
- Basin groups the JTRSY it takes in and redeems it with the issuer. Each `RedeemInitiated` is paired with the `RedeemCompleted` that follows it, and the time between their blocks is the settlement time.
- Liquidity is the Basin's `totalAssets()` and the swap limit is `maxSwapSize()`, both read with `eth_call` on a public Ethereum RPC.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Swap,
RedeemInitiated and RedeemCompleted event of Grove's JTRSY Basin on Ethereum
(0xf08943f817e1F902dEbC884c7B19Ea5764594Ac9). My API token is in the ENVIO_API_TOKEN
environment variable. Chart each swap's USDC payout and how long each redemption took to settle.
```
