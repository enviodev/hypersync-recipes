# Huma Institutional drawdowns on Solana

Pulls every instruction run by [Huma](https://huma.finance)'s Institutional program on Solana with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana), decodes the drawdowns and principal repayments, and adds them up month by month.

## What we found

From slot 391,001,451 (3 Jan 2026) to slot 470,178,163 (16 Nov 2026):

- October was the biggest month of the year: 52 drawdowns took $216.79M of USDC out of Huma Institutional pools. The next biggest month was February at $113.85M.
- November had already reached $125.00M by 16 Nov, from 26 drawdowns.
- Across the whole window, 251 drawdowns came to $871.03M, and 219 principal repayments returned $754.65M.

| Month | Drawdowns | USDC drawn |
|---|---|---|
| Jan (from 3 Jan) | 7 | $10.00M |
| Feb | 33 | $113.85M |
| Mar | 25 | $65.39M |
| Apr | 11 | $30.00M |
| May | 13 | $29.70M |
| Jun | 20 | $65.30M |
| Jul | 19 | $65.00M |
| Aug | 20 | $70.00M |
| Sep | 25 | $80.00M |
| Oct | 52 | $216.79M |
| Nov (to 16 Nov) | 26 | $125.00M |

## Why it matters

Huma Institutional pools fund payment companies against their receivables. Each financing shows up onchain as `create_receivable`, `submit_receivable` and then `drawdown`, and each repayment as `make_principal_payment`. Pull one program's instructions and you have the whole credit book over time, with no indexer to host.

## What it pulls

| | |
|---|---|
| Program | Huma Institutional, `EVQ4s1b6N1vmWFDv8PRNc77kufBP8HcrSNWXQAhRsJq9` ([Huma docs](https://docs.huma.finance/ecosystem-resources/smart-contracts)) |
| Instructions | `drawdown` (discriminator `c828a26f9cde07f3`) and `make_principal_payment` (`28494b8a2d608742`), from the program's onchain Anchor IDL (`huma` v3.2.0). The first argument is a u128 `amount` in USDC base units |
| Filter | Successful transactions only, deduplicated by slot, transaction index and instruction address |
| Window | Slot 391,001,451 (3 Jan 2026, the start of HyperSync's Solana history) to the chain head |

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py                      # 3 Jan 2026 to the chain head
python script.py 452600000 463400000  # any slot range
```

## Check the numbers yourself

- **RPC walk:** every drawdown is signed by the borrower account. We walked that account's signatures over Solana RPC (`getSignaturesForAddress`, then `getTransaction`), decoded the drawdown instructions by discriminator, and summed the borrower's USDC balance change in each transaction. For October that gave 52 drawdowns and $216,790,001.01, the same as HyperSync to the cent.
- **Single transactions:** every row carries its slot. Look any of them up on a Solana explorer and compare the USDC moved.
- **Huma's own numbers:** huma.finance reports more than $20B of payment volume across all of Huma. The onchain drawdowns here are one part of that.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to pull every
instruction executed by the program EVQ4s1b6N1vmWFDv8PRNc77kufBP8HcrSNWXQAhRsJq9 from slot 391001451
to the head, successful transactions only. Page with next_slot and retry on HTTP 429. My API token is
in ENVIO_API_TOKEN. Decode instructions whose first 8 bytes are c828a26f9cde07f3 (drawdown) or
28494b8a2d608742 (make_principal_payment); the next 16 bytes are a little-endian u128 USDC amount
with 6 decimals. Print the count and USDC total per month for each. Then turn it into a HyperIndex
indexer on Solana with an onInstruction handler for each, deployed on Envio Cloud.
```
