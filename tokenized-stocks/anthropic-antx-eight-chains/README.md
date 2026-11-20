# How to track a token launch across multiple chains with HyperSync

This example follows a real multichain launch. On 18 Nov 2026, **1.5M ANTx, the tokenized Anthropic token from xStocks, were minted on each of eight EVM chains in 83 seconds**, between 19:14:09 and 19:15:32 UTC. Every chain uses the same contract address, `0x909369940f22dc1c143ac78753a33f41597138b1`.

| Chain | Minted | Time after the first (UTC 19:14:09) | Block |
| --- | --- | --- | --- |
| Ink | 1,500,000 | +0s | 61,530,838 |
| HyperEVM | 1,500,000 | +11s | 51,618,509 |
| Ethereum | 1,500,000 | +26s | 26,443,975 |
| Monad | 1,500,000 | +42s | 123,379,201 |
| Mantle | 1,500,000 | +63s | 103,449,500 |
| Optimism | 1,500,000 | +68s | 159,715,270 |
| Arbitrum | 1,500,000 | +74s | 525,407,726 |
| BNB Chain | 1,500,000 | +83s | 134,365,661 |

Ethereum and Ink also have a first mint of 100 ANTx from 12 Nov, so their supply reads 1,500,100.

## Why it's interesting

One address on eight chains means one HyperIndex config with eight chain entries follows the whole rollout. The same query shape works on every chain, so you can watch a token launch everywhere at once.

## What it pulls

- The ANTx address from the xStocks products page at [xstocks.fi/products](https://xstocks.fi/products), which lists the same address for every chain. Each chain's contract reports the name "Anthropic xStock" and the symbol ANTx.
- Every ERC-20 `Transfer` log of that token on Ethereum, BNB Chain, Arbitrum, Optimism, Mantle, Ink, HyperEVM and Monad, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview), with the block time.
- A mint is a transfer from the zero address and a burn is a transfer to it. Supply is mints minus burns. The script also prints the largest mint on each chain and how many seconds apart they landed.

Every amount is a count of ANTx, not a dollar value. ANTx has 18 decimals.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes about a minute. Sample output:

```
Ethereum: supply 1,500,100 ANTx from 2 mints and burns
  largest mint 1,500,000 ANTx at 18 Nov 19:14:35 UTC (block 26,443,975)
...
The largest mint on each of 8 chains landed between 18 Nov 19:14:09 and 18 Nov 19:15:32 UTC,
83 seconds apart, all at the same contract address.
  +  0s  Ink        1,500,000 ANTx
  + 11s  HyperEVM   1,500,000 ANTx
  + 26s  Ethereum   1,500,000 ANTx
  + 42s  Monad      1,500,000 ANTx
  + 63s  Mantle     1,500,000 ANTx
  + 68s  Optimism   1,500,000 ANTx
  + 74s  Arbitrum   1,500,000 ANTx
  + 83s  BNB Chain  1,500,000 ANTx
```
