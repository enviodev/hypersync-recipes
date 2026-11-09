# BlackRock BUIDL by chain

Reads every mint and burn of BlackRock's USD Institutional Digital Liquidity Fund (BUIDL) on the EVM chains BlackRock lists, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It rebuilds BUIDL supply on each chain and checks it against `totalSupply()` onchain.

These are the numbers behind Envio's post on where BUIDL sits.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
BlackRock BUIDL on EVM chains: $1,077,950,497
  Avalanche  $   416,822,490   38.7%
  Ethereum   $   316,772,397   29.4%
  BNB Chain  $   277,503,739   25.7%
  OP Mainnet $    26,572,637    2.5%
  Tempo      $    17,172,594    1.6%
  Arbitrum   $    12,629,108    1.2%
  Polygon    $    10,477,531    1.0%
Avalanche vs Ethereum, OP Mainnet, Arbitrum and Polygon combined: $416,822,490 vs $366,451,674
BUIDL minted on Avalanche since launch: $2,043,131,789
Checks
  Avalanche: replayed supply matches totalSupply() at block 99,867,223
  Ethereum: replayed supply matches totalSupply() at block 26,378,668
  BNB Chain: replayed supply matches totalSupply() at block 132,620,165
  OP Mainnet: replayed supply matches totalSupply() at block 159,322,313
  Tempo: replayed supply matches totalSupply() at block 48,215,732
  Arbitrum: replayed supply matches totalSupply() at block 522,735,768
  Polygon: replayed supply matches totalSupply() at block 97,025,310
```

The numbers move as BUIDL is minted and redeemed, so yours will differ.

## How it counts

- Token addresses are the official ones on BlackRock's [token addresses page](https://www.blackrock.com/corporate/compliance/scams-and-fraud/blackrock-token-addresses). Ethereum has two share classes, BUIDL and BUIDL-I, and both count towards Ethereum.
- BUIDL has 6 decimals on every chain and a stable $1 value, so supply is shown in dollars.
- Supply on each chain is every mint (a Transfer from the zero address) minus every burn (a Transfer to it). The script checks it against `totalSupply()` at the last block HyperSync returned.
- BUIDL is also on Solana and Aptos. HyperSync covers EVM chains, so those two are not included here.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every mint and burn of
BlackRock's BUIDL on Avalanche (0x53FC82f14F009009b440a706e31c9021E1196A2F) and Ethereum
(0x7712c34205737192402172409a8F7ccef8aA2AEc and 0x6a9DA2D710BB9B700acde7Cb81F10F1fF8C89041).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart BUIDL supply on each chain, day by day.
```

## Learn more

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Index Avalanche with Envio](https://envio.dev/chains/avalanche)
- [HyperIndex, for a full indexer with a GraphQL API](https://docs.envio.dev/docs/HyperIndex/overview)
