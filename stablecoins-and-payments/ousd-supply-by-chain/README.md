# Open USD (OUSD) supply by chain

In a run on 17 Nov 2026 (Ethereum block 26,435,319), **Open USD (OUSD) supply was $964.9M across four chains**. Tempo held $631.3M of it, then Ethereum at $121.9M, Solana at $117.2M and Base at $94.5M. Tempo also has the most holders, at 29.1K. Every chain's supply comes from HyperSync.

| 17 Nov 2026 | Supply | Share | Holders |
| --- | --- | --- | --- |
| Tempo | $631,272,143 | 65.4% | 29,062 |
| Ethereum | $121,893,224 | 12.6% | 220 |
| Solana | $117,209,884 | 12.1% | |
| Base | $94,475,607 | 9.8% | 1,097 |
| Total | $964,850,857 | | |

## Why it's interesting

OUSD lives on four chains, and most of it sits on Tempo, the payments chain. If you're building on any of them, this shows where the supply and the holders actually are. It also shows how to rebuild every holder's balance on several chains in one pass, and check the result against the contract.

## What it pulls

- Every `Transfer` log on OUSD on three chains. The addresses are the official ones from Open Standard at [joinopenstandard.com/integrate](https://joinopenstandard.com/integrate), all with 6 decimals.
  - Ethereum [`0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436`](https://etherscan.io/address/0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436)
  - Base [`0xB2000000000000000000002fEb517dFeC7415344`](https://basescan.org/address/0xB2000000000000000000002fEb517dFeC7415344)
  - Tempo `0x20c0000000000000000000006a37DA5C996874BE`
- Every balance change of the OUSD mint on Solana, `ousd2mJsPEckLHcSCDxyKD7NDGARZcfLbDZkKiatYHB`, as `account_activity` rows from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). Each row has a token account's balance before and after a transaction. Summed over a transaction, transfers cancel out, so the sum of every change is every mint minus every burn. OUSD's first balance change on Solana is at slot 415,382,345, inside HyperSync's Solana history, so the script reads from slot 415,000,000.
- Supply on each chain is every mint minus every burn, and holders are addresses with a balance above zero. Some holders are contracts, such as liquidity pools. OUSD is redeemable 1:1 for US dollars, so supply is shown in dollars.

All four chains, and so the total, come from HyperSync. Public RPCs are read only for the checks below.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Sample output from the 17 Nov 2026 run, trimmed to the supply lines and the Solana check.

```
Open USD (OUSD) supply: $964,850,857
  Tempo    $   631,272,143   65.4%  29,062 holders, top 10 hold 73.0%
  Ethereum $   121,893,224   12.6%    220 holders, top 10 hold 84.8%
  Solana   $   117,209,884   12.1%
  Base     $    94,475,607    9.8%  1,097 holders, top 10 hold 79.3%
...
Checks
  ...
  Solana: rebuilt supply matches getTokenSupply on Solana's public RPC at slot 470,565,829
```

The script prints each chain's supply, share and holders above the checks. OUSD is minted and redeemed all the time, so your numbers will differ.

## Change the window or chain

- **Chains.** Each EVM chain is one entry in `EVM`, with its HyperSync slug, a public RPC and the token address. Add a chain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) by adding an entry.
- **Token.** Swap the addresses in `EVM` for any other multichain token, and change `DECIMALS` if it isn't 6.
- **Solana.** `SOLANA_MINT` and `SOLANA_FROM` set the Solana token and the slot to start from. Any SPL token whose first mint is after slot 391,000,000, where HyperSync's Solana history starts, can be summed the same way. The [HyperSync Solana docs](https://docs.envio.dev/docs/HyperSync/solana) cover the query fields.

## Check the numbers

The script checks itself on every run, using each chain's public RPC as the comparison. On Ethereum, Base and Tempo the rebuilt supply is compared with `totalSupply()` at the last block HyperSync returned, and the ten largest balances with `balanceOf()` at the same block. On Solana the script reads `getTokenSupply` first, then sums HyperSync up to the slot that call answered from, so both describe the same moment. In the 17 Nov run the Solana supply matched to the last unit.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every OUSD Transfer on
Ethereum, Base and Tempo and every OUSD balance change on Solana, and rebuild
supply and holder balances. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Add a Solana holder count from the same HyperSync account_activity rows
(https://docs.envio.dev/docs/HyperSync/solana), keeping each token account's latest
post_token_balance. Then print supply per chain at the end of every UTC day for the
last 30 days. Keep the standard library only, and check the Solana total against
getTokenSupply.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [Open Standard integration docs](https://joinopenstandard.com/integrate)
- [Envio Discord](https://discord.gg/envio)
