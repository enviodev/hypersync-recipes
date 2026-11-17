# Coinbase borrowing on Morpho, Base

Coinbase's bitcoin-backed loans run through the cbBTC/USDC market on Morpho on Base, and its newer gold-backed loans run through a PAXG/USDC market. Up to Base block 55,212,962 on 9 Nov 2026, **75.5K wallets had borrowed $3.76B of USDC against cbBTC since Sep 2024, and 40.6K cbBTC sat in the market as collateral**. At the market oracle's price that collateral was worth about $3.03B, against $1.62B of USDC owed.

| | cbBTC/USDC | PAXG/USDC |
| --- | --- | --- |
| Collateral at that block | 40,602.5463 cbBTC | 11.8555 PAXG |
| USDC borrowed in total | $3,757,272,323 | $22,275 |
| Borrowers | 75,465 | 35 |
| Events | 1,550,996 | 304 |
| First borrow | 13 Sep 2024 | 27 Oct 2026 |

## Why it's interesting

When a big app runs loans through an open lending market, you can follow the whole book onchain. Every collateral deposit, borrow, repay and liquidation is an event on Morpho, so the market's history is a replay away. The cbBTC market has over 1.5M events, which makes it a good test of pulling a busy market from the first block.

## What it pulls

- `SupplyCollateral`, `WithdrawCollateral`, `Borrow`, `Repay` and `Liquidate` logs on Morpho on Base [`0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`](https://basescan.org/address/0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb), from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses), for two market IDs.
  - cbBTC/USDC `0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836`
  - PAXG/USDC `0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392`
- The market IDs come from the Morpho API, and the script reads each market's oracle back from Morpho's `idToMarketParams` onchain. cbBTC is [`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`](https://basescan.org/address/0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf) (8 decimals) and PAXG is [`0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef`](https://basescan.org/address/0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef) (18 decimals), from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/paxg/mainnet).

Collateral is `SupplyCollateral` minus `WithdrawCollateral` minus collateral seized in `Liquidate`. A borrower is any `onBehalf` address in a `Borrow` event. The cbBTC market is open to anyone on Morpho, so its totals cover every borrower in it, not only those who came through Coinbase.

Collateral, borrowers, total borrowed and the monthly series come from HyperSync. "USDC owed now" is the market's `totalBorrowAssets` read over Base's public RPC, so it includes interest. Dollar values for collateral use each market's oracle `price()`, also read over RPC.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # up to the latest block
python3 script.py 55212962     # up to the block used above
```

The cbBTC market has more than 1.5M events, so a full run takes a while. Sample output from the block above.

```
cbBTC/USDC market 0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836 (oracle 0x663becd10dae6c4a3dcd89f1d76c1174199639b9), up to Base block 55,212,962
  collateral now: 40,602.5463 cbBTC ~ $3,029,058,806 at $74,602.68 per cbBTC
  USDC owed now: $1,623,913,618 (RPC, with interest); $3,757,272,323 borrowed in total since 2024-09-13
  75,465 unique borrowers, 1,550,996 collateral, borrow, repay and liquidation events
  end of each month: collateral, USDC principal outstanding (borrows minus repays)
    2024-09         16.8918 cbBTC  $         561,934
    ...
    2026-11     40,602.5463 cbBTC  $   1,539,700,362

PAXG/USDC market 0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392 (oracle 0x6a47f48780eaeb07ee18ca47a9c33c925961bfad), up to Base block 55,212,962
  collateral now: 11.8555 PAXG ~ $48,785 at $4,114.98 per PAXG
  USDC owed now: $21,074 (RPC, with interest); $22,275 borrowed in total since 2026-10-27
  35 unique borrowers, 304 collateral, borrow, repay and liquidation events
```

Without a block number your numbers will differ a little.

## Change the window or chain

- **Block.** Pass a Base block number to rebuild the markets as they stood then.
- **Markets.** Add any Morpho market that lends USDC to `MARKETS`, with its ID and the collateral token's decimals. The script reads the oracle onchain. Find IDs in the [Morpho app](https://app.morpho.org) or the Morpho API.
- **Chain.** Morpho runs on many chains. Change `HYPERSYNC` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` to a public RPC there and `MORPHO` to the address in the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses).

## Check the numbers

As an outside comparison, at block 55,212,962 the rebuilt cbBTC collateral matches the Morpho API's `collateralAssets` to within 0.05 cbBTC, the gap being blocks between the two reads. The month-end principal from events ($1.54B) sits below `totalBorrowAssets` over RPC ($1.62B) because the RPC figure includes interest.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every collateral,
borrow, repay and liquidation event in two Morpho markets on Base and rebuild
collateral and borrowers. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add a weekly count of new borrowers (the first Borrow for each onBehalf address)
for the cbBTC/USDC market since it opened, and write it to a CSV. Keep the
standard library only. Then check three borrowers against position(marketId,
borrower) on Morpho at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Morpho addresses](https://docs.morpho.org/get-started/resources/addresses)
- [PAXG on Morpho, Base](../../rwa-and-funds/paxg-on-morpho-base), a deeper look at the gold market
- [Envio Discord](https://discord.gg/envio)
