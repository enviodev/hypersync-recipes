# Active addresses without dusting

A sudden jump in daily active addresses is often not new users. Dusting contracts send one tiny transfer to each of thousands of addresses in a single transaction, and every one of those addresses shows up as active that day.

This script counts unique token recipients per day on any chain [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview) supports, then counts them again with the dusting transfers dropped. These are the numbers behind Envio's post on filtering out dusting before counting active addresses.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

Set `CHAIN` to the network name HyperSync uses, the subdomain in `https://<chain>.hypersync.xyz`. The [supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) page lists them all.

```bash
export ENVIO_API_TOKEN=your-token
CHAIN=<chain> python script.py
```

By default it covers the last 14 full UTC days. Pick your own window with `START` and `END` (both inclusive):

```bash
CHAIN=<chain> START=2026-10-30 END=2026-11-08 python script.py
```

Busy chains carry millions of Transfer logs a day, so a long window takes a while. `WORKERS` sets how many days run in parallel (default 2), and `OUT=daily.json` saves the results.

## What it prints

One row per day with every Transfer log, the unique recipients, and the unique recipients once dusting is dropped. Under each row it lists the contracts it dropped that day, with recipients, transfers, transactions and the average batch size. Add `TOP=3` to also list the biggest contracts it kept, so you can check the rule.

```
day            transfers   recipients  without dusting  dusters
2026-10-30     1,734,270       63,658           63,658        0
2026-10-31     1,146,356       86,771           86,771        0
2026-11-01     1,116,569      153,211          147,575        1
2026-11-02     1,336,812      100,897           94,028        1
2026-11-03     1,400,501      118,868           73,150        2
2026-11-04     1,914,031      172,683          164,919        1
2026-11-05     1,840,900      304,885          180,590        1
2026-11-06     2,267,337      644,781          292,094        5
2026-11-07     6,268,491    2,002,972          195,420        4
2026-11-08     5,979,105    2,767,882          395,487        3
```

That run covered 10 days on one chain. On the busiest day, 2.8 million addresses received a token and about 400,000 did once dusting was dropped.

## How it counts

- It reads every log with the ERC-20 and ERC-721 `Transfer` topic (`0xddf252ad...`) between the first and last block of each UTC day. The recipient is `topic2`. Mints to and burns from the zero address are left out.
- A recipient counts once per day, however many tokens it received.
- A contract is treated as a duster on a given day when all three are true:
  - it sent tokens to at least 10,000 addresses that day (`MIN_RECIPIENTS`)
  - it averaged at least 20 transfers per transaction (`MIN_PER_TX`)
  - at least 99% of its transfers went to a different address (`MIN_UNIQUE_SHARE`)
- "Without dusting" counts recipients from every other contract. An address that got dust and also a real transfer that day still counts.
- The rule is a filter on behaviour, not a judgement on any token. It also catches genuine batch airdrops, which you may want to count separately. Tune the three thresholds for your chain and check the dropped list before you publish a number.

## Learn more

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query): log selection, field selection and paging
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks): every value `CHAIN` can take
- [Analyzing all transactions to and from an address](https://docs.envio.dev/docs/HyperSync/tutorial-address-transactions): more HyperSync scripts for wallets and tokens
- [Wildcard indexing](https://docs.envio.dev/docs/HyperIndex/wildcard-indexing): index every ERC-20 transfer on a chain with HyperIndex and keep this filter live
- [How to index ERC-20 token transfers](https://docs.envio.dev/docs/HyperIndex/tutorial-erc20-token-transfers): a step-by-step HyperIndex tutorial
- [Chains on Envio](https://envio.dev/chains): every chain HyperSync and HyperIndex support

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every ERC-20
Transfer log on <chain> for the last 14 days. My API token is in the ENVIO_API_TOKEN
environment variable. For each day, count unique recipients, then count them again after
dropping contracts that sent one transfer per recipient in batches of 20 or more per
transaction to at least 10,000 addresses. Chart both lines.
```
