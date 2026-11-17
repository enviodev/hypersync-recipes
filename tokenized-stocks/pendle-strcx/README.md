# How much STRCx sits in Pendle

At Ethereum block 26,387,500 on 10 Nov 2026, **Pendle's SY-STRCx contract held 535K STRCx, 48.7% of the supply outside Backed's issuer wallet**. That's up from 30K at the end of August. 5.2K addresses had touched STRCx, the [xStocks](https://xstocks.fi) token for Strategy's STRC preferred share, and 5.1K held some.

| Holder | STRCx | Share of supply |
| --- | --- | --- |
| Pendle SY-STRCx | 535,275 | 31.3% |
| Backed issuer wallet | 613,630 | 35.8% |
| Everyone else | 562,905 | 32.9% |

## Why it's interesting

STRCx pays a yield, and Pendle lets people split that yield from the principal, so it's become a natural home for the token. The script also shows a gotcha worth knowing. STRCx pays dividends by raising a balance multiplier, which changes every balance without a Transfer event, so summing transfers drifts from the real balance by up to 9% for older holders. The fix is to find holders from events and then read their balances directly.

## What it pulls

- Every `Transfer` and `TransferShares` event on STRCx, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). HyperSync gives the 103K transfers and the 5.2K addresses that ever touched the token, and the dates for the daily series.
- `balanceOf()` for every one of those addresses at one block, batched 400 at a time through Multicall3 over a public Ethereum RPC. The holder balances, the Pendle share and the daily SY series come from these RPC reads, not from HyperSync.
- `totalSupply()` and the balance multiplier on STRCx, and `totalSupply()` and `exchangeRate()` on the SY, over the same RPC.

The contracts are STRCx [`0x1aad217b8f78dba5e6693460e8470f8b1a3977f3`](https://etherscan.io/token/0x1aad217b8f78dba5e6693460e8470f8b1a3977f3), Pendle SY-STRCx [`0x3aaaf43a1f8d327fdf24dc93654eb17e319883c5`](https://etherscan.io/address/0x3aaaf43a1f8d327fdf24dc93654eb17e319883c5) (its `yieldToken()` returns STRCx), and Backed's issuer wallet [`0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad`](https://etherscan.io/address/0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad). The STRCx contract names that wallet as its `burner()` and `multiplierUpdater()`, and every STRCx mint has landed there.

"Everyone else" is total supply minus Pendle's SY and the issuer wallet, so it includes other contracts. The daily series reads the SY's `balanceOf()` at the last block of each day that had a STRCx event. The script doesn't compute dollar values.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # balances a few blocks behind the HyperSync height
python3 script.py 26387500     # balances at the block above
python3 script.py --cached     # reuse the events saved in logs.json
```

Balance reads go to `https://eth.drpc.org` by default. Set `ETH_RPC_URL` to use your own, and note the daily series needs an RPC that serves historical state. A full run takes about two minutes. Sample output at block 26,387,500.

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
...

Pendle SY balance since 2026-08-24, end of each week
  2026-08-30      30,355
  2026-09-06     108,467
  ...
  2026-11-08     534,795
  2026-11-10     535,275
```

It also writes `sy_daily.json`, Pendle's SY balance at the end of each day.

## Change the window or chain

- **Block.** Pass a block number to read every balance at that block.
- **Another rebasing token.** Swap `STRCX` and `SY` for any token that moves balances without Transfer events and the contract you want to track. The find-then-read pattern stays the same.
- **Chain.** xStocks tokens live on several chains. Swap `HYPERSYNC` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `ETH_RPC_URL` for an RPC on that chain, and the addresses to match.

## Check the numbers

The script runs two checks over RPC at the same block. The balances of every address add up to `totalSupply()`, and the STRCx held by Pendle's SY matches Pendle's own books, SY `totalSupply()` times `exchangeRate()`. Both matched in the run above. The Pendle market itself is on [Pendle's app](https://app.pendle.finance) as an outside comparison.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every address that has sent or
received STRCx on Ethereum, then reads each balance with balanceOf() over RPC at one
block. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a table of the ten largest contract holders other than Pendle's SY and the issuer
wallet, with what each contract is from its verified name on Etherscan, and their
balance at the end of each week. Keep the standard library only. Then check that every
weekly total stays below totalSupply() at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Pendle docs](https://docs.pendle.finance)
- [xStocks](https://xstocks.fi)
- [Envio Discord](https://discord.gg/envio)
