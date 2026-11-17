# Pendle and STRCx on Ethereum

Finds every address that has ever held STRCx, the [xStocks](https://xstocks.fi) token for Strategy's STRC preferred share, with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It then reads the live balance of each one at a single block and shows how much of the supply sits in Pendle's SY-STRCx contract, and how that grew day by day.

These are the numbers behind Envio's post on Pendle and STRCx.

## What it reads

- STRCx on Ethereum: `0x1aad217b8f78dba5e6693460e8470f8b1a3977f3`
- Pendle SY-STRCx: `0x3aaaf43a1f8d327fdf24dc93654eb17e319883c5`. Its `yieldToken()` returns STRCx.
- Backed's issuer wallet: `0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad`. Etherscan tags it "Backed: Deployer", the STRCx contract names it as its `burner()` and `multiplierUpdater()`, and every STRCx mint has landed there.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

The balance reads go to a public Ethereum RPC (`https://eth.drpc.org`). Set `ETH_RPC_URL` to use your own. The daily series needs an RPC that serves historical state. Pass a block number to pin the balances to that block, for example `python script.py 26387500`, and pass `--cached` to reuse the events saved in `logs.json`. A full run takes about two minutes.

## What it prints

```
STRCx 0x1aad217b8f78dba5e6693460e8470f8b1a3977f3 on Ethereum, balances at block 26,387,500
103,227 transfers, 5,247 addresses ever touched it, 5,123 hold some now
Balance multiplier 1.1013. Failed balance reads: 0

Check 1, balances against supply
  sum of balanceOf()     1,711,810
  totalSupply()          1,711,810   difference -0.0000
Check 2, Pendle SY against its own books
  STRCx.balanceOf(SY)                 535,275
  SY totalSupply x exchangeRate       535,275   difference 0.00

Who holds STRCx
  Pendle SY-STRCx             535,275   31.3%
  Backed issuer wallet        613,630   35.8%
  Everyone else               562,905   32.9%
  Pendle's share of STRCx outside the issuer wallet:  48.7%

Top 10 holders            balanceOf()   from Transfers    gap
  0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad      613,630      585,028   4.7%  Backed issuer
  0x3aaaf43a1f8d327fdf24dc93654eb17e319883c5      535,275      528,795   1.2%  Pendle SY
  0x37b0779a66edc491df83e59a56d485835323a555      500,001      456,418   8.7%
  ...

Pendle SY balance since 2026-08-24, end of each week
  2026-08-30      30,355
  2026-09-06     108,467
  ...
  2026-11-08     534,795
  2026-11-10     535,275
```

That run is from 10th November 2026. Balances move every block, so your numbers will differ. The script also writes `sy_daily.json`, Pendle's SY balance at the end of each day, which is what the chart uses.

## How it counts

- HyperSync is only used to find addresses and dates. It pulls every `Transfer` and `TransferShares` event on STRCx, and every `from` and `to` address becomes a possible holder.
- Balances come from `balanceOf()` at one block, batched 400 at a time through Multicall3. Adding up Transfer amounts does not work for STRCx: dividends are paid by raising a balance multiplier, which changes every balance without emitting a Transfer. The gap column shows how far the Transfer sums fall behind, from under 1% for new holders to almost 9% for older ones.
- Check 1: the balances of all addresses add up to `totalSupply()` at the same block.
- Check 2: the STRCx held by Pendle's SY matches Pendle's own accounting, SY `totalSupply()` times `exchangeRate()`.
- "Everyone else" is total supply minus Pendle's SY and Backed's issuer wallet. It includes other contracts and exchanges.
- The daily series reads `balanceOf()` on the SY at the last block of each day that had a STRCx event.
- Dollar values are not in the script. The post used DefiLlama's STRCx price at the time of the run.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to find every address that has
sent or received STRCx (0x1aad217b8f78dba5e6693460e8470f8b1a3977f3) on Ethereum. My API token is in
the ENVIO_API_TOKEN environment variable. Read balanceOf() for each address at one block over RPC,
check the total against totalSupply(), and show me which Pendle, Morpho or other DeFi contracts hold
STRCx and how their balances changed week by week.
```
