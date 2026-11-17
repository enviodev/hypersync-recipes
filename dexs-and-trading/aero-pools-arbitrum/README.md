# The biggest Aero pools on Arbitrum

Finds every pool created by Aero's factories on Arbitrum, reads every swap in them since launch with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and reads what each pool holds onchain. It ranks the pools by swap volume and by liquidity.

These are the numbers behind Envio's post on Aero's biggest pools on Arbitrum.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

That reads up to the latest block. Pass a block number to stop there instead. The post used block 521465669:

```bash
python script.py 521465669
```

## What it prints

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

Run it without a block number and the numbers will be higher, since the pools keep trading.

## How it counts

- Factories come from Aero's [deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses) (`cl-arbitrum.json` and `pools-arbitrum.json`): the CL pool factory, the volatile pool factory and the stable pool factory. Their `allPoolsLength()` onchain matches the pools found here (63 CL, 2 volatile, 0 stable).
- Volume is each swap valued on one side. A dollar stablecoin side (USDC, USDC.e, USDT0, USDG, DAI, GHO, USDe, USDai) counts at $1. Otherwise WETH or WBTC are used, priced from Aero's own stablecoin pools at the time of the swap, and then any other token priced from its Aero pool. A handful of gold token swaps with no dollar route are left unpriced.
- Liquidity is each pool's token balances (`balanceOf`) at the end block, valued at the latest prices from the same swaps. For CL pools this includes fees not yet collected.
- Wallets are the distinct senders of transactions that contain a swap, so routers and bots count too.
- Daily volume from this script matches DefiLlama's Aero Slipstream volume on Arbitrum to within 0.3% each day.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every swap in
Aero's pools on Arbitrum. The pool factories are listed in
https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses
(cl-arbitrum.json and pools-arbitrum.json). My API token is in the ENVIO_API_TOKEN
environment variable. Chart daily swap volume per pool since launch as a stacked area chart.
```
