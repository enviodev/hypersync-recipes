# Grove Basin for JTRSY on Ethereum

A Python script that reads every event of Grove's JTRSY Basin on Ethereum with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Basin lets holders of JTRSY, the Janus Henderson Anemoy Treasury Fund token issued through Centrifuge, swap it for USDC in a single transaction, then redeems the JTRSY with the issuer in the background.

In a run on 16 Nov 2026, Basin had handled **20 swaps of JTRSY into USDC**, 534.7K JTRSY in for **$597.8K USDC out**, every one settled in the same transaction. The largest was 135K JTRSY for $150.5K USDC. Basin's own redemptions with the issuer took anywhere from 12 minutes to 6.9 days to settle. Read live from the contract over RPC, the Basin held $99.9M of liquidity with a largest single swap of $50M.

## Why it's interesting

Tokenized treasury funds usually redeem on the issuer's schedule, which can mean waiting days for cash. Basin moves that wait off the holder. The holder gets USDC in one transaction, and Basin carries the redemption itself. The script shows both sides of that from onchain events alone, the instant swaps and the slower redemptions behind them.

It's also a small, complete example of reading one contract's full history with HyperSync. One query with three event signatures returns every event since deployment, with block timestamps, in a few seconds.

## What it pulls

- Every `Swap`, `RedeemInitiated` and `RedeemCompleted` event from the JTRSY Basin, [`0xf08943f817e1F902dEbC884c7B19Ea5764594Ac9`](https://etherscan.io/address/0xf08943f817e1F902dEbC884c7B19Ea5764594Ac9) (`JTRSY_GROVE_BASIN` on Grove's [deployed contracts page](https://docs.grove.finance/deployed-contracts)).
- JTRSY is [`0x8c213ee79581Ff4984583C6a801e5263418C4b86`](https://etherscan.io/token/0x8c213ee79581Ff4984583C6a801e5263418C4b86) and USDC is [`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`](https://etherscan.io/token/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48). Both use 6 decimals.
- Two `eth_call`s on a public Ethereum RPC for the Basin's `totalAssets()` (liquidity) and `maxSwapSize()` (largest swap allowed). These two figures come from RPC, not from HyperSync.

The swap and redemption figures all come from HyperSync.

A swap is a `Swap` event with JTRSY in and USDC out. Each `RedeemInitiated` is paired with the `RedeemCompleted` that follows it, and the time between their blocks is the settlement time.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes a few seconds. Sample output from a run on 16 Nov 2026.

```
Grove Basin for JTRSY on Ethereum
  20 swaps of JTRSY into USDC, each in a single transaction (0 swaps in any other direction)
  534,688.600766 JTRSY in, $597,801.320668 USDC out
  Largest: 135,000.000000 JTRSY into $150,533.235000 USDC, 2026-09-11 18:07 UTC, tx 0x62b4e4ce14068d02f702138db15fd1e8dcd936a119d306dc37ca1b15f5fd8d5e
  Latest:  98,014.000000 JTRSY into $110,005.816872 USDC, 2026-11-13 10:35 UTC, tx 0xf5eb3c58f68b18fdb070e5e241c3b80478471a50c2a411dabf738feb5ef66956
Basin's own redemptions of the JTRSY it took in
      1.000000 JTRSY  requested 2026-07-23 12:49 UTC  settled for $1.110401 USDC after 2.7 hours (0.1 days)
  1,000.000000 JTRSY  requested 2026-07-28 11:37 UTC  settled for $1,110.846688 USDC after 0.4 hours (0.0 days)
  100,000.000000 JTRSY  requested 2026-07-28 13:58 UTC  settled for $111,084.668810 USDC after 19.4 hours (0.8 days)
  135,051.802383 JTRSY  requested 2026-09-15 10:54 UTC  settled for $150,714.405820 USDC after 165.5 hours (6.9 days)
  89,171.798383 JTRSY  requested 2026-11-04 20:11 UTC  settled for $100,015.320031 USDC after 23.5 hours (1.0 days)
  111,450.000000 JTRSY  requested 2026-11-06 17:07 UTC  settled for $125,031.321658 USDC after 4.2 hours (0.2 days)
  98,014.000000 JTRSY  requested 2026-11-13 12:19 UTC  settled for $110,005.904579 USDC after 0.2 hours (0.0 days)
Liquidity in the Basin now: $99,890,007.54
Largest single swap allowed: $50,000,000
```

New swaps and redemptions add lines, so your output will grow.

## Change the window or chain

- **Window.** The script reads from block 0 to the latest block. Set `body["to_block"]` before the loop to stop at a past block, and pass that block in hex instead of `"latest"` in `call()` so the liquidity figures match it.
- **Another Basin or chain.** Swap `BASIN`, `JTRSY` and `USDC` for another entry on Grove's [deployed contracts page](https://docs.grove.finance/deployed-contracts), and the `eth.hypersync.xyz` URL and `RPC` for that chain's endpoints. HyperSync URLs are on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).

## Check the numbers

Every swap prints its transaction hash, so you can open it on [Etherscan](https://etherscan.io/address/0xf08943f817e1F902dEbC884c7B19Ea5764594Ac9) and compare the amounts. The liquidity and swap limit are read live from the contract, and you can call `totalAssets()` and `maxSwapSize()` yourself on the Etherscan contract page.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Swap, RedeemInitiated
and RedeemCompleted event from Grove's JTRSY Basin on Ethereum
(0xf08943f817e1F902dEbC884c7B19Ea5764594Ac9), then pairs redemptions to time how long
each took to settle. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a daily series of the Basin's JTRSY and USDC balances by also reading ERC-20
Transfer logs of both tokens to and from the Basin address. Keep the standard library
only. Then check the latest balances against balanceOf on each token at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Grove deployed contracts](https://docs.grove.finance/deployed-contracts)
- [Grove docs](https://docs.grove.finance)
- [Envio Discord](https://discord.gg/envio)
