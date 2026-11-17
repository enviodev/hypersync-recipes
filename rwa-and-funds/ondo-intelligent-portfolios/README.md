# Ondo Intelligent Portfolios on Ethereum and BNB Chain

**Ondo's Intelligent Portfolio tokens held $54.7M on Ethereum and BNB Chain, across 1.8K holding addresses**, valued at the prices on Ondo's app on 4 Nov 2026. $47M of it, 86%, arrived after 12 Oct 2026. BLKGRWon and MAG7Xon were the two largest, at $15.7M and $15.4M.

## Why it's interesting

Intelligent Portfolios wrap a basket of tokenized stocks and funds into one token, and they grew fast once they launched. Supply rebuilt from mints and burns shows how fast, portfolio by portfolio, and the holder count shows how widely they're held. It's a small, clear script to start from if you track any fund token that lives on two chains.

## What it pulls

- Every ERC-20 `Transfer` of the seven portfolio tokens on Ethereum and BNB Chain, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Supply, holders and the arrived-since figure all come from HyperSync.
- Token addresses from each portfolio's page on Ondo's app, app.ondo.finance. The seven are BLKHIon, BLKDIGon, BLKGRWon, YLD8on, YLD5on, MAG7Xon and BRAINon. BLKGRWon, for example, is [`0xc90341Cb9cb8D65AF044FaB23b659b7b4279399B`](https://etherscan.io/token/0xc90341Cb9cb8D65AF044FaB23b659b7b4279399B) on Ethereum.
- Dollar values use the token prices shown on Ondo's app on 4 Nov 2026, kept in `PRICES` in the script. They don't come from HyperSync, so edit them for today's value.

Supply is mints minus burns, and it matches each token's `totalSupply()` onchain. Holders are addresses with a positive balance. The portfolios on Solana aren't read here.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py               # arrived since 12 Oct 2026
python3 script.py 2026-10-01    # arrived since another UTC date
```

Sample output:

```
Ondo Intelligent Portfolios on Ethereum and BNB Chain: $54.7M
  BLKGRWon   $ 15.72M  28.8%
  MAG7Xon    $ 15.37M  28.1%
  ...
Addresses holding a portfolio token: 1,840
Arrived since 12 Oct 2026: $47.0M (86%)
```

## Change the window or chain

- **Cut-off date.** Pass any UTC date to see how much arrived after it.
- **Prices.** Update `PRICES` with the latest values from each portfolio's page for today's dollar figures.
- **Chain.** `CHAINS` maps each chain to its HyperSync endpoint. If Ondo adds the portfolios on another EVM chain, add its endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and the token addresses for that chain.

## Check the numbers

The rebuilt supply for each token matches `totalSupply()` onchain. You can check any one on [Etherscan](https://etherscan.io) or BscScan with the addresses in the script.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of Ondo's
Intelligent Portfolio tokens on Ethereum and BNB Chain and rebuild supply and holders.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a weekly series of supply and holders per portfolio since launch and write it to
weekly.csv. Keep the standard library only. Then check that the last week's supply for
each token matches totalSupply() read onchain.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Ondo docs](https://docs.ondo.finance)
- [Envio Discord](https://discord.gg/envio)
