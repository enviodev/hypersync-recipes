# Ondo stocks on Robinhood Chain, the first week

In their launch week, 27 Oct to 3 Nov 2026, Ondo's tokenized stocks on Robinhood Chain traded in **29 Uniswap v4 pools, with 226 swaps from 110 wallets**. 88% of those swaps paired an Ondo token with Robinhood's own token for the same company, like GOOGLon against GOOGL. GOOGLon was the most traded with 87 swaps from 50 wallets.

| Token | Swaps | Wallets |
| --- | --- | --- |
| GOOGLon | 87 | 50 |
| TSLAon | 40 | 20 |
| NVDAon | 22 | 17 |

## Why it's interesting

When a second issuer brings the same stocks to a chain, the first trades tell you how the two wrappers meet. Here most of the early flow was Ondo's version of a stock swapping straight into Robinhood's version of the same stock. The script is also a compact example of a launch-week tracker. Find every pool a set of tokens trades in, then count swaps and wallets per token for any week.

## What it pulls

- Ondo's 15 Robinhood Chain token addresses from the token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses).
- Every `Initialize` on the Uniswap v4 PoolManager [`0x8366a39cc670b4001a1121b8f6a443a643e40951`](https://developers.uniswap.org/docs/protocols/v4/deployments) where either side is an Ondo token, then every `Swap` in those pools during the week with the transaction that sent it, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Pool, swap and wallet counts all come from HyperSync.
- Token symbols for the other side of each pool, read with `eth_call` on Robinhood Chain's public RPC. They're only used as labels.

Wallets are the addresses that sent the swap transactions. A swap pairs with the same company's Robinhood Stock Token when the other token's symbol is the Ondo symbol without the "on" suffix.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py               # launch week, 27 Oct to 3 Nov 2026 UTC
python3 script.py 2026-11-03    # the 7 days from another start date
```

Sample output for the launch week:

```
Ondo stocks on Robinhood Chain, 2026-10-27 to 7 days later (UTC)
Uniswap v4 pools with an Ondo token  29
Swaps    226
Wallets  110
Swaps against the same company's Robinhood Stock Token  198 (88%)
  GOOGLon    87 swaps from  50 wallets
  TSLAon     40 swaps from  20 wallets
  NVDAon     22 swaps from  17 wallets
  ...
```

## Change the window or chain

- **Week.** Pass any start date as `YYYY-MM-DD` and the script counts the 7 days from there. Run it week after week to see how trading builds.
- **Chain.** Ondo's sheet lists its tokens on other chains too. Swap `URL` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), the PoolManager for that chain's address from the [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments), and the token list for that chain's column in the sheet.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Robinhood Chain to find every
Uniswap v4 pool with one of Ondo's tokenized stocks and count swaps and wallets per
token for a week. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Change it to loop over every week since 27 Oct 2026 and print one row per week with
swaps, wallets and new wallets that had never swapped an Ondo token before. Keep the
standard library only. Then check that the first week's row matches the 226 swaps and
110 wallets in the README.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Robinhood Chain on Envio](https://envio.dev/chains/robinhood)
- [Ondo token addresses](https://docs.ondo.finance/addresses)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Envio Discord](https://discord.gg/envio)
