# Backpack tokenized stocks on Solana

Counts the wallets holding the 94 stocks and ETFs that [Backpack Securities](https://backpack.exchange/tokenized-stocks/assets) issues on Solana, and pulls every mint and burn of those tokens, all with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana).

## What we found

Snapshot at slot 470,214,813 (16 Nov 2026, 17:26 UTC), from 583M balance rows:

- 140,081 wallets hold at least $1 of these stock tokens, and 530,563 hold some
- The tokens in those wallets are worth $46.64M across 94 tickers (82 stocks, 12 ETFs and funds)
- 32,988 wallets hold $10 or more, 9,033 hold $100 or more and 2,156 hold $1,000 or more
- SpaceX (SPCX) is the biggest at $12.8M, then Micron (MU) at $6.1M and Take-Two (TTWO) at $5.0M
- Take-Two is the most widely held, in 41,470 wallets with at least $1, then SpaceX in 33,788

Holder counts are per wallet across all 94 tokens, so a wallet holding three stocks counts once. The $1 cut removes dust balances.

## Why it matters

Each of these tokens can be redeemed 1:1 for the real share through Backpack Securities, so the balances are real stock positions held in self-custody. They are plain Token-2022 mints, which means you can read every holder, mint and burn straight from the chain without asking the issuer for anything. HyperSync keeps the balance of every token account after every transaction, so a holder list is one filtered read of that table with no node to run. The same two scripts work for any list of SPL or Token-2022 mints: swap `mints.json`.

## What it pulls

| | |
|---|---|
| Tokens | The 94 mints in `mints.json`, copied from Backpack's [Tokenized Securities Directory](https://backpack.exchange/tokenized-stocks/assets) |
| Program | Token-2022, `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` |
| `holders.py` | HyperSync's [`account_activity`](https://docs.envio.dev/docs/HyperSync/solana-query#the-account_activity-table) table filtered by the 94 mints. It keeps the latest `post_token_balance` and `post_owner` for each token account, then sums per wallet. Balances are turned into dollars with [Jupiter's price API](https://dev.jup.ag/docs/price) |
| `script.py` | `MintTo` (tag 7) and `MintToChecked` (14), where account 0 is the mint, and `Burn` (8) and `BurnChecked` (15), where account 1 is the mint. Outer and inner calls, successful transactions only, last 7 days by default |

The HyperSync filter in `script.py` is one `instruction_calls` selection per side, matched server-side on the program, the first data byte (`d1`) and the mint's account position (`a0` / `a1`) for all 94 mints at once. See [Query & Response](https://docs.envio.dev/docs/HyperSync/solana-query#instructionselection).

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python holders.py         # every holder and the value they hold, from HyperSync
python script.py          # every mint and burn in the last 7 days, by ticker
DAYS=1 python script.py
```

`holders.py` reads the tokens' whole history, about 580M balance rows from June 2026, in 100K-slot pieces with 16 workers. It saves each piece under `chunks/` and carries on from there if you stop it, so leave it running in the background; the full pass took us a few hours over the JSON API. `script.py` splits the window into 100K-slot chunks and pulls them in parallel (`WORKERS`, default 8), backing off on rate limits. It writes every row to `stock_mint_burn.json`.

## Check the numbers yourself

- **Against a Solana RPC node:** `check_rpc.py` counts the same holders a different way, with `getProgramAccounts` for each mint. Run three hours after the snapshot above, it gave 141,531 wallets with $1 or more and $46.56M held, against 140,081 and $46.64M from HyperSync. Take-Two had 43,182 wallets against 41,470. It also checks each token's summed balances against the supply on its mint account.
- **Value per token:** compare any ticker's value with its market cap on [app.sunrise.xyz/tokens](https://app.sunrise.xyz/tokens). On 16 Nov NVDA came out at $2.61M, TSLA at $883K and META at $1.01M in both.
- **Mints:** every mint address is on Backpack's directory with a Solscan link. Don't trust a ticker symbol alone.
- **Single transactions:** every row from `script.py` carries its slot. Look any of them up on a Solana explorer and compare the amount.

Prices move and people trade all day, so your numbers will differ a little from the snapshot above.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to pull every
MintTo/MintToChecked (d1 07/0e, account a0 = mint) and Burn/BurnChecked (d1 08/0f, account a1 = mint)
instruction on the Token-2022 program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb for the mints in
mints.json, over the last 7 days, successful transactions only. Page with next_slot and retry on
HTTP 429. My API token is in ENVIO_API_TOKEN. Then read the account_activity table filtered by the same
mints from slot 420,000,000 to the head, keep the latest post_token_balance and post_owner for each token
account, price the balances with Jupiter's price API and count wallets holding $1 or more.
After that, adapt it to <another list of token mints>.
```

To turn it into a live HyperIndex indexer instead, scaffold one with `pnpx envio init` (choose Svm). `envio init` adds Envio's agent skills to the new project's `.claude/skills/` folder, so your agent has the docs in context ([Quickstart with AI](https://docs.envio.dev/docs/HyperIndex/quickstart-with-ai)).

## Links

- [HyperSync for Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [Index Solana programs with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana), to turn this into a live indexer on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Backpack's Tokenized Securities Directory](https://backpack.exchange/tokenized-stocks/assets) and [how tokenized securities work](https://support.backpack.exchange/backpack-securities/tokenized-securities)
- [Sunrise docs on tokenized equities](https://docs.sunrise.xyz/equities/backpack-securities)
- [Token-2022 program](https://spl.solana.com/token-2022)
- Questions: [Envio Discord](https://discord.gg/envio)
