# Open USD (OUSD) supply by chain

Reads every OUSD transfer on Ethereum, Base and Tempo with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It rebuilds OUSD supply and every holder's balance on each chain, then shows how much of each chain's supply the 10 largest holders hold. Solana supply comes from Solana's public RPC.

These are the numbers behind Envio's post on where OUSD sits.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
Open USD (OUSD) supply: $910,351,142
  Tempo    $   623,134,876   68.4%  1,577 holders, top 10 hold 73.6%
  Ethereum $   113,235,535   12.4%    170 holders, top 10 hold 86.7%
  Base     $    93,037,502   10.2%    995 holders, top 10 hold 81.1%
  Solana   $    80,943,228    8.9%
Across Ethereum, Base and Tempo, the top 10 holders on each chain hold 76.3% of the OUSD there
The top 10 holders on Tempo hold 50.4% of all OUSD
Checks
  Ethereum: replayed supply matches totalSupply() at block 26,348,668, top 10 balances match balanceOf()
  Base: replayed supply matches totalSupply() at block 53,546,437, top 10 balances match balanceOf()
  Tempo: replayed supply matches totalSupply() at block 47,551,374, top 10 balances match balanceOf()
  Solana supply read from getTokenSupply on Solana's public RPC
```

The numbers move as OUSD is minted and redeemed, so yours will differ.

## How it counts

- Token addresses are the official ones listed by Open Standard at [joinopenstandard.com/integrate](https://joinopenstandard.com/integrate). OUSD is live on Base, Ethereum, Solana and Tempo, with 6 decimals on each.
- OUSD is redeemable 1:1 for US dollars, so supply is shown in dollars.
- Supply on each EVM chain is every mint minus every burn. The script checks it against `totalSupply()` at the last block HyperSync returned.
- Holders are addresses with a positive balance on that chain. An address that holds on two chains counts on both. Some holders are contracts, such as liquidity pools.
- The top 10 holders are ranked per chain, and their balances are checked with `balanceOf()` at the same block.
- Solana is not covered by HyperSync, so the script only reads its total supply.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of
Open USD (OUSD) on Ethereum (0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436), Base
(0xB2000000000000000000002fEb517dFeC7415344) and Tempo (0x20c0000000000000000000006a37DA5C996874BE).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart OUSD supply per chain, day by day, and how much the 10 largest holders hold.
```
