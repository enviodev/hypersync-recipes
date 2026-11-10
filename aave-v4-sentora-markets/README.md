# Sentora's curated markets on Aave v4

Reads every Supply, Withdraw and Borrow on Sentora's three curated Aave v4 spokes on Ethereum, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It rebuilds what has been supplied and borrowed, day by day, and checks each reserve against the spoke's own state onchain.

These are the numbers behind Envio's post on Sentora's Aave v4 markets passing $100M.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
Supplied to Sentora's Aave v4 markets: $101,416,307
  RLUSD  $    51,342,132
  USDe   $    49,961,885
  kBTC   $       112,261
  PYUSD  $            20
  OUSD   $             9
RLUSD borrowed in the RLUSD Yield market: $41,824,152 of $51,341,946 supplied (81.5% utilization)
Supplied, day by day (USD at today's prices)
  2026-10-22               100
  ...
  2026-11-04        83,200,848
  ...
  2026-11-10       101,395,229
Checks at block 26,383,355
  RLUSD Yield RLUSD  replayed    51,324,975.88  onchain    51,346,056.06  interest  21,080.18
  RLUSD Yield USDe   replayed    49,999,999.34  onchain    49,999,999.34  interest       0.00
  ...
```

The numbers move as people supply, withdraw and borrow, so yours will differ.

## How it counts

- Spoke and oracle addresses come from Aave's official [address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4EthereumSentoraCurated.sol). Event signatures come from Aave's [ISpoke interface](https://github.com/aave/aave-v4/blob/main/src/spoke/interfaces/ISpoke.sol).
- The query uses HyperSync's default join, so only the matching logs come back. The script also keeps only logs whose address and topic0 match what it asked for.
- Each reserve's underlying token and decimals come from `getReserve()`, and its price comes from the spoke's own oracle (`getReservePrice()`, 8 decimals).
- Supplied value is every Supply minus every Withdraw. The script checks it against `getReserveSuppliedAssets()` at the last block HyperSync returned. Onchain supply also includes interest earned since each deposit, so it sits slightly above the replayed principal.
- Borrowed is read with `getReserveTotalDebt()`. Utilization is debt divided by supplied assets.
- The day-by-day curve values every asset at today's oracle price. Almost all of it is dollar stablecoins, so the curve is close to what it was on each day.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Supply, Withdraw
and Borrow event on Sentora's Aave v4 spokes on Ethereum (0x9EbF0C19BF7dFE859820Cc09E846114b53814e52,
0xbb97b61Ad6747D337E5805F2d159d275BB1f0828 and 0xA37e7cdC557f3C7f745FB3F337b6439979662c46).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart supplied and borrowed value per reserve, day by day.
```

## Learn more

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Index Ethereum with Envio](https://envio.dev/chains/ethereum)
- [HyperIndex, for a full indexer with a GraphQL API](https://docs.envio.dev/docs/HyperIndex/overview)
