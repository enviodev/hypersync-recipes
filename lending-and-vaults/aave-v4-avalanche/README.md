# Aave v4 on Avalanche

On 16 Nov 2026, **Aave v4 on Avalanche held $189.2M in stablecoins**, led by USDe at $90.7M and USDt at $90.1M, alongside 2.6M WAVAX and 741K sAVAX. **1,246 addresses** have supplied since the first deposit on 15 Jul 2026, and the biggest stablecoin day was 6 Nov 2026, with $70.2M added.

| Asset | Deposited |
| --- | --- |
| USDe | $90.7M |
| USDt | $90.1M |
| USDC | $8.5M |
| WAVAX | 2,648,902 WAVAX |
| sAVAX | 740,974 sAVAX |
| WETH.e | 420 WETH.e |
| BTC.b | 116 BTC.b |

## Why it's interesting

Aave v4 keeps liquidity in one Hub per chain and lets many spokes plug into it. So the Hub's `Add` and `Remove` events are the one place every deposit on the chain passes through, whichever spoke or vault a user came in from.

That means you get the whole market from one contract's events. Add the spokes' `Supply` events and the ERC-4626 vaults' `Deposit` events and you've also got every address that has supplied. HyperSync returns all of it since launch in one paged query.

## What it pulls

Addresses come from Aave's [address book for Avalanche](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Avalanche.sol). Event signatures match Aave's [v4 interfaces](https://github.com/aave/aave-v4/tree/main/src).

- `Add`, `Remove` and `AddAsset` logs from the Hub [`0xd07369fae4a5bb13c9ce446b052c7867b1abdf6e`](https://subnets.avax.network/c-chain/address/0xd07369fae4a5bb13c9ce446b052c7867b1abdf6e).
- `Supply` logs from the five spokes listed in `SPOKES`.
- ERC-4626 `Deposit` logs from the seven tokenization vaults listed in `VAULTS`.

Deposited is every `Add` minus every `Remove`, per asset. Addresses are the distinct suppliers on the spokes plus depositors into the vaults. Stablecoins count at $1, and other assets are shown in their own units. Every number here comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It reads from block 0 to the latest block and takes a minute or two. Sample output from a run on 16 Nov 2026.

```
Aave v4 on Avalanche, first deposit 15 Jul 2026
  USDe    $90.7M
  USDt    $90.1M
  USDC    $8.5M
  WAVAX   2,648,902.45 WAVAX
  sAVAX   740,974.34 sAVAX
  EURC    5,425.94 EURC
  WETH.e  419.95 WETH.e
  BTC.b   115.97 BTC.b
Stablecoins $189.2M
Addresses that have supplied: 1,246
Biggest stablecoin day: 06 Nov 2026, +$0.2M USDC, +$33.4M USDe, +$36.6M USDt
```

Deposits change every block, so your numbers will differ.

## Change the window or chain

- **Window.** The query starts at `"from_block": 0`. Add a `"to_block"` to the request body to stop at a past block, or raise `from_block` to look at a recent stretch.
- **Chain.** Aave v4 also runs on Ethereum, Base and Arc. Change `URL` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), then swap `HUB`, `SPOKES`, `VAULTS` and `TOKENS` for the matching file in the [address book](https://github.com/bgd-labs/aave-address-book/tree/main/src).

## Check the numbers

The Hub reports its own total per asset with `getAddedAssets(assetId)`. Find the asset ID with `getAssetId(underlying)`, then call both on a public Avalanche RPC as the comparison.

```bash
cast call 0xd07369fae4a5bb13c9ce446b052c7867b1abdf6e "getAssetId(address)(uint256)" \
  0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34 --rpc-url https://api.avax.network/ext/bc/C/rpc
cast call 0xd07369fae4a5bb13c9ce446b052c7867b1abdf6e "getAddedAssets(uint256)(uint256)" 7 \
  --rpc-url https://api.avax.network/ext/bc/C/rpc
```

On 16 Nov 2026 that gave 90.66M USDe and 90.23M USDt, against $90.7M and $90.1M from the events. `getAddedAssets` includes interest earned, which the events don't.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Add and Remove on the
Aave v4 Hub on Avalanche, plus Supply events on its spokes and Deposit events on its
ERC-4626 vaults. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a daily series of net deposits per asset since launch and write it to a CSV.
Keep the standard library only. Then check each asset's total against
getAddedAssets(assetId) on the Hub at the same block and explain any gap.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aave v4 docs](https://aave.com/docs/aave-v4)
- [Aave address book for Avalanche](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Avalanche.sol)
- [Avalanche C-Chain explorer](https://subnets.avax.network/c-chain)
- [Envio Discord](https://discord.gg/envio)
