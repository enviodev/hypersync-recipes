# Durable nonce transactions on Solana

Counts every Solana transaction that opens with a System Program `AdvanceNonceAccount` instruction, day by day, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana). It also counts the nonce accounts and fee payers behind them and estimates their share of all successful transactions.

These are the numbers behind Envio's post on how much Solana activity still runs on durable nonces. The Solana Foundation plans to retire durable nonces and names Anza's Programmatic Signer and Blueshift's Vector as candidate replacements. No date is set yet. Details are on the [Durable Nonce Deprecation](https://solana.com/upgrades/durable-nonce-deprecation) page.

## What we found

Over the 30 UTC days from 10th October to 8th November 2026:

- 178M successful durable nonce transactions, about 6M a day on average (3.2M on the quietest day, 10.6M on the busiest)
- About 1 in 18 successful non-vote transactions (5.7%, sampled)
- 930k distinct nonce accounts and 620k distinct fee payers
- 453 fee payers sent 90% of the transactions

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a number of days to change the window, for example `python script.py 7`. A 30-day run reads about 180M instruction rows and takes a little over an hour.

## What it prints

One row per UTC day, then the totals for the window. This is the 30-day run from 9th November.

```
Day            Nonce txs  Nonce accts  Fee payers   Share
...
06 Nov             4.72M       120.0k       56.1k    5.0%
07 Nov             3.76M       103.8k       74.1k    4.6%
08 Nov             3.95M       112.5k       65.6k    4.5%

30 days: 178.0M nonce transactions, 930k nonce accounts, 620k fee payers
Share of successful non-vote transactions (sampled): 5.7%
Fee payers behind 90% of them: 453
```

## How it counts

- A durable nonce transaction must open with `AdvanceNonceAccount`, so the script asks HyperSync for top-level System Program instruction calls whose first four data bytes are `04000000` (instruction 4, little-endian), then keeps the ones at `instruction_address` `[0]`.
- Account 0 of that instruction is the nonce account. The fee payer comes from the parent transaction, joined on `(slot, transaction_index)`.
- HyperSync serves successful transactions' instructions, so every count here is of successful transactions. Vote transactions are excluded at ingest.
- Day boundaries are found from block times, so each day runs from 00:00 to 24:00 UTC.
- The share comes from 48 random 20-slot windows per day. Scaling those windows' nonce counts up to the full day lands within 11% of the exact daily count on every day.
- We checked nine slots across 12th October, 25th October, 3rd November and 9th November against Solana RPC `getBlock`. Successful non-vote transactions and durable nonce transactions matched exactly in every slot.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to find
every top-level instruction call to the System Program 11111111111111111111111111111111
with d4 = 04000000 (AdvanceNonceAccount) at instruction_address [0] over the last 7 days.
My API token is in the ENVIO_API_TOKEN environment variable. Count them per UTC day, with
distinct nonce accounts (a0) and fee payers, and chart the daily totals.
```

## Learn more

- [Solana on Envio](https://envio.dev/chains/solana)
- [Solana HyperSync overview](https://docs.envio.dev/docs/HyperSync/solana)
- [Solana HyperSync query and response reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [Solana curl examples](https://docs.envio.dev/docs/HyperSync/solana-curl-examples)
- [Indexing on Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Solana instruction handlers in HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [How to index and track stablecoin transfers on Solana](https://docs.envio.dev/blog/index-solana-stablecoin-transfers)
- [Query Builder for Solana](https://builder.hypersync.xyz/#solana)
