# Huma Institutional drawdowns on Solana

From slot 391,001,451 (3 Jan 2026) to slot 470,178,163 (16 Nov 2026), **251 drawdowns took $871.03M of USDC out of [Huma](https://huma.finance) Institutional pools on Solana, and 219 principal repayments returned $754.65M**.

- October was the biggest month of the year, with 52 drawdowns worth $216.79M. The next biggest was February at $113.85M.
- November had already reached $125.00M by 16 Nov, from 26 drawdowns.

| Month | Drawdowns | USDC drawn |
| --- | --- | --- |
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

## Why it's interesting

Huma Institutional pools fund payment companies against their receivables. Each financing shows up onchain as `create_receivable`, `submit_receivable` and then `drawdown`, and each repayment as `make_principal_payment`. Pull one program's instructions and you've got the whole credit book over time, with nothing to host.

It's also a tidy example of decoding Anchor instructions straight from HyperSync on Solana. Match the 8-byte discriminator, read the arguments, done.

## What it pulls

- **Program.** Huma Institutional, [`EVQ4s1b6N1vmWFDv8PRNc77kufBP8HcrSNWXQAhRsJq9`](https://solscan.io/account/EVQ4s1b6N1vmWFDv8PRNc77kufBP8HcrSNWXQAhRsJq9) ([Huma's smart contracts page](https://docs.huma.finance/ecosystem-resources/smart-contracts)).
- **Instructions.** Every instruction the program executed, with its slot, transaction index, instruction address, data and `tx_success`, plus each block's time.
- **Decoding.** `drawdown` (discriminator `c828a26f9cde07f3`) and `make_principal_payment` (`28494b8a2d608742`), from the program's onchain Anchor IDL (`huma` v3.2.0). The next 16 bytes are a little-endian u128 `amount` in USDC base units (6 decimals).
- **Filter.** Successful transactions only, deduplicated by slot, transaction index and instruction address. Months are UTC.

The counts and USDC totals come from HyperSync. When you don't pass an end slot, the script asks Solana's public RPC for the current slot with `getSlot`, and that's the only RPC call it makes.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                        # 3 Jan 2026 to the current slot
python3 script.py 391001451 470178163    # the window used above
```

It prints progress to stderr, then a `Slots <from> to <to>` line and, for `drawdown` and then `make_principal_payment`, one line per month with the count and USDC total, followed by a `total` line. October's drawdowns, for example, come to 52 and $216,790,001.01.

## Change the window

Pass a start slot and an end slot. 391,001,451 is where HyperSync's Solana history starts, so the script can't go earlier than 3 Jan 2026. For one month, find the first and last slot of the month on a Solana explorer and pass those. To follow another Anchor program, swap `PROGRAM` and the discriminators in `DISC`, which are the first 8 bytes of `sha256("global:<instruction_name>")`. The [Solana query docs](https://docs.envio.dev/docs/HyperSync/solana-query) list every field you can select.

## Check the numbers

- **An RPC walk, as the comparison.** Every drawdown is signed by the borrower account. We walked that account's signatures over Solana RPC (`getSignaturesForAddress`, then `getTransaction`), decoded the drawdown instructions by discriminator and summed the borrower's USDC balance change in each transaction. For October that gave 52 drawdowns and $216,790,001.01, the same as HyperSync to the cent.
- **Single transactions.** Every row has its slot. Look any of them up on [Solscan](https://solscan.io) and compare the USDC moved.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana-query) to pull every instruction
run by the Huma Institutional program
EVQ4s1b6N1vmWFDv8PRNc77kufBP8HcrSNWXQAhRsJq9, then decodes drawdown and
make_principal_payment by their 8-byte discriminators and sums the u128 USDC
amount by month. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Add a running balance of USDC drawn minus principal repaid, month by month,
and the 10 biggest single drawdowns with their slot. Keep the standard library
only. Run it for October 2026 first and check that October still comes to 52
drawdowns and $216,790,001.01.
```

To keep it live, ask the agent to turn it into a [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer on Solana with an instruction handler for each, and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [HyperSync Solana query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Huma docs](https://docs.huma.finance) and [smart contracts](https://docs.huma.finance/ecosystem-resources/smart-contracts)
- [Envio Discord](https://discord.gg/envio)
