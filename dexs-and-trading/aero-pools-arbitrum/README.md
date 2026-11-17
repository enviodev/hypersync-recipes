# The biggest Aero pools on Arbitrum

In its first 14.9 days on Arbitrum, up to block 521,465,669, **Aero's 65 pools did $252.1M in swap volume across 255K swaps from 5.8K wallets**. USDG/USDC was the biggest pool at $74.2M, then USDG/USD₮0 at $43.7M and WETH/USDC at $31.4M. USDG pools made up 55.5% of the volume.

| Pool | Volume | Swaps |
| --- | --- | --- |
| USDG/USDC | $74.2M | 29,007 |
| USDG/USD₮0 | $43.7M | 7,141 |
| WETH/USDC | $31.4M | 48,405 |
| WBTC/WETH | $20.6M | 29,489 |
| USDC/USD₮0 | $18.4M | 5,111 |
| All 65 pools | $252.1M | 255,074 |

## Why it's interesting

A new DEX on a chain is a good test of how quickly liquidity and flow show up. This script finds every pool from the factories, reads every swap since launch and prices each one in dollars from the DEX's own trades, with no price feed. It works for any Uniswap v2 or v3 style DEX if you swap in its factories.

## What it pulls

- `PoolCreated` logs from Aero's three factories on Arbitrum, from Aero's [deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses) (`cl-arbitrum.json` and `pools-arbitrum.json`). They are the CL pool factory `0x88a60ee77392577c355c0acb2a8d476d5a4ec03a`, the volatile pool factory `0x8e6a9fcd1d638cc760ffba397605fe3355de76d2` and the stable pool factory `0x78589e876edcebdce72ee3436ab3c9ad3a7cef2d`.
- Every `Swap` log from those pools, with the block timestamp and the transaction's sender.
- Every `Transfer` of each pool's two tokens into and out of the pool since the factories were deployed, which gives each pool's token balances at the end block.
- Each token's `decimals()` and `symbol()` through Arbitrum's public RPC, and as a cross-check only, each pool's token balances with `balanceOf` at the end block.

Volume is each swap valued on one side. A dollar stablecoin side (USDC, USDC.e, USDT0, USDG, DAI, GHO, USDe, USDai) counts at $1. Otherwise WETH or WBTC is used, priced from Aero's own stablecoin pools at the time of the swap, and then any other token priced from its Aero pool. A handful of gold token swaps have no dollar route and are left unpriced. Wallets are the distinct senders of transactions that contain a swap, so routers and bots count too.

The swap volume, swap counts, wallets and liquidity all come from HyperSync. Liquidity is each pool's balances rebuilt from transfers in minus transfers out, valued at the latest prices from the same swaps. For CL pools that balance includes fees not yet collected.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py             # up to the latest block
python3 script.py 521465669   # up to the block used above
```

Sample output from a run on 17 Nov 2026 with block 521465669.

```
Aero on Arbitrum: 65 pools, 43 with swaps, over 14.9 days
Swap volume $252.1M across 255,074 swaps from 5,814 wallets (21 swaps unpriced)
Liquidity $5.03M at block 521465669

Top pools by swap volume
  USDG/USDC              $    74.2M   29.5%   29,007 swaps  0x09328be718d89228a985471bb470988a34d0b162
  USDG/USD₮0             $    43.7M   17.3%    7,141 swaps  0x81659867a8ce20bb57be82fd9184f2ff1f887605
  WETH/USDC              $    31.4M   12.5%   48,405 swaps  0x30c83aaecc7ceabea96b881a62729a1df366efd5
  WBTC/WETH              $    20.6M    8.2%   29,489 swaps  0x6938f149a2b1ca7f4737109ab7d0df0c50b69087
  USDC/USD₮0             $    18.4M    7.3%    5,111 swaps  0x412cf90dc0e435e9f68d2d810b24fe7d2904085b
  WETH/ARB               $    16.5M    6.5%   54,215 swaps  0xbdf6749254c8760b42f38b9985baaf1cecf17617
  USDG/WETH              $    14.7M    5.8%   25,339 swaps  0x14cecb8a37013853ad071fc877705a8ecc9e77b7
  WBTC/USDC              $    12.2M    4.9%   20,509 swaps  0x8e7dfd89de71e4a206295ca68760b2fc58ce053c
  sUSDai/USDC            $    12.2M    4.8%    1,048 swaps  0x319d28ce8f1aea7b284a8fe2002f4330109b5dc8
  USDG/WBTC              $     6.2M    2.5%   14,004 swaps  0x346b3e6bc9c654c5c2437e6b005e2ccd3a43ddd5

Top pools by liquidity
  USDG/USDC              $    1.41M   28.0%  0x09328be718d89228a985471bb470988a34d0b162
  USDC/USD₮0             $    1.10M   21.8%  0x412cf90dc0e435e9f68d2d810b24fe7d2904085b
  USDG/USD₮0             $    0.83M   16.6%  0x81659867a8ce20bb57be82fd9184f2ff1f887605
  WBTC/WETH              $    0.41M    8.1%  0x6938f149a2b1ca7f4737109ab7d0df0c50b69087
  USDG/WETH              $    0.37M    7.4%  0x14cecb8a37013853ad071fc877705a8ecc9e77b7
  WETH/USDC              $    0.35M    7.0%  0x30c83aaecc7ceabea96b881a62729a1df366efd5
  WBTC/USDC              $    0.20M    4.0%  0x8e7dfd89de71e4a206295ca68760b2fc58ce053c
  WETH/ARB               $    0.18M    3.6%  0xbdf6749254c8760b42f38b9985baaf1cecf17617
  USDG/WBTC              $    0.11M    2.2%  0x346b3e6bc9c654c5c2437e6b005e2ccd3a43ddd5
  USDG/ARB               $    0.02M    0.5%  0xe41723a9fca1eac0f18728d4583510aa7377901b

The other 58 pools: $32.6M volume, $0.38M liquidity
Volume is 50x liquidity
Top 5 pools: 74.7% of volume
USDG pools: 24 of 65, 55.5% of volume, 54.6% of liquidity

Prices used for liquidity: WETH $2,420.16, WBTC $80,204.09
```

"The other 58 pools" means every pool outside the top seven by volume. The script ends with an RPC check line, left out above. Arbitrum's public RPC only keeps recent state, so the check needs a run without a block number or an archive RPC. Run it without a block number and the numbers will be higher, since the pools keep trading.

## Change the window or chain

- **Window.** Pass an end block as the first argument. The start is `FIRST_BLOCK`, just before the factories were deployed.
- **Chain.** Aero's deployment addresses folder has a file per chain. Swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` for a public RPC on that chain, the three factory addresses and `FIRST_BLOCK`, and update `STABLES`, `WETH` and `WBTC` to that chain's token addresses.

## Check the numbers

The script compares each rebuilt pool balance with `balanceOf` over Arbitrum's public RPC at the same block. In a run on 17 Nov 2026 at block 525,000,956, all 158 token balances of the 79 pools matched. As a further comparison, call `allPoolsLength()` on each factory through any Arbitrum RPC. When we checked, it returned 63 CL pools, 2 volatile pools and 0 stable pools, the same 65 pools the script found.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every pool from Aero's
factories on Arbitrum, read every swap since launch and price it in dollars from
Aero's own pools. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Add a daily volume table per pool for the top 5 pools by volume, using each
swap's block timestamp, and write it to daily_volume.csv. Keep the standard
library only. Run it with end block 521465669 and check that the daily totals
for each pool add up to the volume the script already prints for it.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aero deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses)
- [Envio Discord](https://discord.gg/envio)
