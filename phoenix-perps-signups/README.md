# Phoenix sign-ups and deposits on Solana

From slot 391,001,451 (3 Jan 2026) to slot 470,205,922 (16 Nov 2026), **59.8K wallets opened a trading account on [Phoenix](https://phoenix.trade), the perps exchange built by Ellipsis Labs on Solana**. 25.8K of them made a deposit, across 195.1K deposits worth $91.6M of USDC. October was the busiest month for new wallets, with 17.5K.

| Month | New wallets | All wallets | USDC deposited |
|---|---:|---:|---:|
| 2026-01 | 220 | 220 | 515,106 |
| 2026-02 | 1,463 | 1,683 | 401,595 |
| 2026-03 | 1,746 | 3,429 | 1,316,377 |
| 2026-04 | 1,268 | 4,697 | 2,065,615 |
| 2026-05 | 14,910 | 19,607 | 9,649,387 |
| 2026-06 | 7,484 | 27,091 | 15,587,387 |
| 2026-07 | 4,420 | 31,511 | 9,505,581 |
| 2026-08 | 5,499 | 37,010 | 12,810,055 |
| 2026-09 | 3,975 | 40,985 | 19,613,046 |
| 2026-10 | 17,548 | 58,533 | 14,346,079 |
| 2026-11 (to the 16th) | 1,237 | 59,770 | 5,747,539 |

A wallet is counted once, in the month it first opened an account. The window starts on 3 Jan 2026 because that's where HyperSync's Solana history starts, so accounts opened before then aren't in the count. Deposits are gross, so money a trader withdrew and put back in counts twice.

## Why it's interesting

Phoenix runs its whole exchange as one Solana program. Opening an account, depositing, placing an order and updating a quote are all instructions on it. Filter that program by two instruction discriminators and you get sign-ups and deposits for a perps exchange, straight from the chain.

## What it pulls

- **Program.** Phoenix perps, `EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih`, from Phoenix's public SDK, [rise-public](https://github.com/Ellipsis-Labs/rise-public) (`rust/ix/src/constants.rs`).
- **`RegisterTrader`.** Discriminator `4bf3e0a701053320`. Account 4 is the trader's wallet and account 5 is the new trader account.
- **`DepositFunds`.** Discriminator `ca2734d33514fa58`. Account 3 is the trader's wallet, and the u64 after the discriminator is the amount, with 6 decimals.
- **Filter.** Successful transactions, top-level and inner calls, matched on the server by program and `d8`, and deduplicated by slot, transaction index and instruction address.
- **Window.** Slot 391,001,451 (3 Jan 2026) to the chain head.

The discriminators are listed in [`instructions.json`](https://github.com/Ellipsis-Labs/rise-public/blob/master/instructions.json) in the SDK repo. A wallet can register more than one trader account (isolated subaccounts), which is why there are 82.2K `RegisterTrader` instructions for 59.8K wallets.

Phoenix takes USDC deposits through its Ember program, which wraps USDC 1:1 into the token the exchange settles in. `DepositFunds` moves that token into the exchange vault, so the amounts are USDC amounts.

Every count and dollar figure here comes from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana).

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                      # 3 Jan 2026 to the chain head
python3 script.py 391001451 470205922  # the exact window used above
```

It runs 16 requests side by side and takes about six minutes. It prints the monthly table and ends like this.

```
Slots 391,001,451 to 470,205,922
RegisterTrader instructions: 82,210
Wallets that opened a trading account: 59,770
DepositFunds instructions: 195,143
Wallets that deposited: 25,766
USDC deposited: $91,557,767
```

It also writes `signups_by_day.json` next to the script, with new wallets per UTC day.

## Change the window

- **Slots.** Pass a start and end slot as the two arguments. With none it runs from 3 Jan 2026 to the head.
- **Speed.** `WORKERS` sets how many requests run at once and `SEGMENT` how many slots each one covers.
- **More instructions.** Add another discriminator from `instructions.json` to the `d8` list and a branch in `pull` to decode it.

## Check the numbers

- **Vault balance changes.** HyperSync's `account_activity` table gives the token balance of Phoenix's vault (`csZXgw2G58hbiWc9ndxaxrQVYVvqdXgQzYLuznEzHJu`) before and after every transaction. For 12 deposits we picked at random, the vault's balance went up by exactly the decoded amount every time.
- **Trader accounts.** Read the trader account of any `RegisterTrader` row with Solana RPC `getAccountInfo`. Its owner is the Phoenix program.
- **Vault balance.** As an RPC comparison, `getTokenAccountBalance` on the vault returned $21.98M on 16 Nov 2026.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana-query) to pull the RegisterTrader
and DepositFunds instructions of the Phoenix perps program
EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih and counts wallets and USDC deposited
per month. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add PlaceMarketOrder (d8 5a76c0fcc0632791) and map each order's orderbook account to
a market with https://perp-api.phoenix.trade/v1/view/exchange/markets, then print
orders and distinct traders per market per week. Keep the standard library only.
Run it on a short slot range first, then check a few orders against a Solana
explorer.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana), if you want sign-ups and deposits live behind a GraphQL API
- [Phoenix docs](https://docs.phoenix.trade) and the [Rise SDK](https://github.com/Ellipsis-Labs/rise-public)
- [Envio Discord](https://discord.gg/envio)
