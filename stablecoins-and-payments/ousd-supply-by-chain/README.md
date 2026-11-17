# Open USD (OUSD) supply by chain

In the run below, **Open USD (OUSD) supply was $910.4M across four chains**. Tempo held $623.1M of it, then Ethereum at $113.2M, Base at $93.0M and Solana at $80.9M. Tempo also has the most holders, at 1.6K.

| Chain | Supply | Share | Holders |
| --- | --- | --- | --- |
| Tempo | $623,134,876 | 68.4% | 1,577 |
| Ethereum | $113,235,535 | 12.4% | 170 |
| Base | $93,037,502 | 10.2% | 995 |
| Solana | $80,943,228 | 8.9% | |
| Total | $910,351,142 | | |

## Why it's interesting

OUSD lives on four chains, and most of it sits on Tempo, the payments chain. If you're building on any of them, this shows where the supply and the holders actually are. It also shows how to rebuild every holder's balance on several chains in one pass, and check the result against the contract.

## What it pulls

- Every `Transfer` log on OUSD on three chains. The addresses are the official ones from Open Standard at [joinopenstandard.com/integrate](https://joinopenstandard.com/integrate), all with 6 decimals.
  - Ethereum [`0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436`](https://etherscan.io/address/0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436)
  - Base [`0xB2000000000000000000002fEb517dFeC7415344`](https://basescan.org/address/0xB2000000000000000000002fEb517dFeC7415344)
  - Tempo `0x20c0000000000000000000006a37DA5C996874BE`
- Supply on each chain is every mint minus every burn, and holders are addresses with a balance above zero. Some holders are contracts, such as liquidity pools. OUSD is redeemable 1:1 for US dollars, so supply is shown in dollars.

Ethereum, Base and Tempo come from HyperSync. Solana's $80.9M is read with `getTokenSupply` on Solana's public RPC, so the Solana line and the total include one number from outside HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Sample output, trimmed to the total and the checks.

```
Open USD (OUSD) supply: $910,351,142
  ...
Checks
  Ethereum: replayed supply matches totalSupply() at block 26,348,668, top 10 balances match balanceOf()
  Base: replayed supply matches totalSupply() at block 53,546,437, top 10 balances match balanceOf()
  Tempo: replayed supply matches totalSupply() at block 47,551,374, top 10 balances match balanceOf()
  Solana supply read from getTokenSupply on Solana's public RPC
```

The script prints each chain's supply, share and holders above the checks. OUSD is minted and redeemed all the time, so your numbers will differ.

## Change the window or chain

- **Chains.** Each EVM chain is one entry in `EVM`, with its HyperSync slug, a public RPC and the token address. Add a chain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) by adding an entry.
- **Token.** Swap the addresses in `EVM` for any other multichain token, and change `DECIMALS` if it isn't 6.
- **Solana.** For the Solana side from HyperSync instead, see [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana).

## Check the numbers

The script checks itself on every run, using each chain's public RPC as the comparison. The rebuilt supply matches `totalSupply()` at the last block HyperSync returned, and the ten largest balances match `balanceOf()` at the same block.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every OUSD Transfer on
Ethereum, Base and Tempo and rebuild supply and holder balances. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Replace the Solana RPC call with HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana), rebuilding OUSD supply on Solana
from mint and burn instructions for mint ousd2mJsPEckLHcSCDxyKD7NDGARZcfLbDZkKiatYHB.
Then print supply per chain at the end of every UTC day for the last 30 days.
Keep the standard library only, and check the Solana total against getTokenSupply.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [Open Standard integration docs](https://joinopenstandard.com/integrate)
- [Envio Discord](https://discord.gg/envio)
