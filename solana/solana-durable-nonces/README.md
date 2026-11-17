# Durable nonce transactions on Solana

Over the 30 UTC days from 10 Oct to 8 Nov 2026, **178M successful Solana transactions used a durable nonce, about 6M a day and 5.7% of successful non-vote transactions**. They came from 930K distinct nonce accounts and 620K fee payers. The quietest day had 3.2M and the busiest 10.6M.

## Why it's interesting

Durable nonces let a transaction be signed now and sent later, which custody setups, offline signers and some trading flows rely on. As of Nov 2026, the Solana Foundation plans to replace them, with candidate successors named on the [Durable Nonce Deprecation](https://solana.com/upgrades/durable-nonce-deprecation) page and no date set. If you run or build on any of those flows, this is how to measure how much activity uses them, and the same instruction filter works for any program and instruction on Solana.

## What it pulls

- Every top-level call to the System Program `11111111111111111111111111111111` whose first four data bytes are `04000000` (`AdvanceNonceAccount`, instruction 4, little-endian) at `instruction_address` `[0]`, from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). A durable nonce transaction has to open with that instruction.
- The parent transaction of each call, joined on `(slot, transaction_index)`, for the fee payer.
- Block times to find each UTC day's first slot, and 48 random 20-slot windows per day of all successful non-vote transactions for the share.

Every number here comes from HyperSync. Account 0 of the instruction is the nonce account. HyperSync serves successful transactions' instructions with vote transactions left out, so every count is of successful non-vote transactions. Scaling the sample windows' nonce counts up to a full day lands within 11% of the exact daily count on every day, so the share is a close estimate.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py      # the last 30 UTC days
python3 script.py 7    # the last 7 UTC days
```

A 30-day run reads about 180M instruction rows and takes a little over an hour. Sample output from the 30-day run on 9 Nov 2026:

```
Day            Nonce txs  Nonce accts  Fee payers   Share
...
06 Nov             4.72M       120.0k       56.1k    5.0%
07 Nov             3.76M       103.8k       74.1k    4.6%
08 Nov             3.95M       112.5k       65.6k    4.5%

30 days: 178.0M nonce transactions, 930k nonce accounts, 620k fee payers
Share of successful non-vote transactions (sampled): 5.7%
...
```

## Change the window or chain

- **Window.** Pass a number of days. A 7-day run takes about a quarter of the time.
- **Another instruction.** Swap the program id and the four-byte discriminator to count any instruction on Solana, like a token program's `MintTo` or a DEX's swap. The [Solana query reference](https://docs.envio.dev/docs/HyperSync/solana-query) lists every filter and field.

## Check the numbers

Nine slots across 12 Oct, 25 Oct, 3 Nov and 9 Nov were checked against Solana RPC `getBlock` as the comparison. Successful non-vote transactions and durable nonce transactions matched exactly in every slot.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana) to count every successful transaction
that opens with System Program AdvanceNonceAccount, per UTC day, with the nonce
accounts and fee payers behind them. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add an hour-of-day breakdown in UTC of nonce transactions for the window and write it
to hourly.csv. Keep the standard library only. Run it with 1 day first. Then check that
the 24 hourly counts add up to that day's total in the daily table.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [Solana query and response reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [Solana curl examples](https://docs.envio.dev/docs/HyperSync/solana-curl-examples)
- [Indexing Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Solana on Envio](https://envio.dev/chains/solana)
- [Durable Nonce Deprecation](https://solana.com/upgrades/durable-nonce-deprecation)
- [Envio Discord](https://discord.gg/envio)
