# Backpack tokenized stocks on Solana

Counts the wallets holding the 94 stocks and ETFs that [Backpack Securities](https://backpack.exchange/tokenized-stocks/assets) issues on Solana, and pulls every mint and burn of those tokens with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana).

## What we found

Snapshot on 16 Nov 2026, around 16:40 UTC (slot 470.2M):

- 140,304 wallets hold at least $1 of these stock tokens, and 530,064 hold some
- The tokens in those wallets are worth $46.98M across 94 tickers (82 stocks, 12 ETFs and funds)
- 33,122 wallets hold $10 or more, 9,062 hold $100 or more and 2,167 hold $1,000 or more
- SpaceX (SPCX) is the biggest at $12.5M, then Micron (MU) at $6.4M and Take-Two (TTWO) at $5.0M
- Take-Two is the most widely held, in 41,905 wallets with at least $1

Holder counts are per wallet across all 94 tokens, so a wallet holding three stocks counts once. The $1 cut removes dust balances.

## Why it matters

Each of these tokens can be redeemed 1:1 for the real share through Backpack Securities, so the balances are real stock positions held in self-custody. They are plain Token-2022 mints, which means you can read every holder, mint and burn straight from the chain without asking the issuer for anything. The same two scripts work for any list of SPL or Token-2022 mints: swap `mints.json`.

## What it pulls

| | |
|---|---|
| Tokens | The 94 mints in `mints.json`, copied from Backpack's [Tokenized Securities Directory](https://backpack.exchange/tokenized-stocks/assets) |
| Program | Token-2022, `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` |
| `holders.py` | Every token account for each mint over Solana RPC (`getProgramAccounts`), priced with [Jupiter's price API](https://dev.jup.ag/docs/price), summed per wallet |
| `script.py` | `MintTo` (tag 7) and `MintToChecked` (14), where account 0 is the mint, and `Burn` (8) and `BurnChecked` (15), where account 1 is the mint. Outer and inner calls, successful transactions only, last 7 days by default |

The HyperSync filter in `script.py` is one `instruction_calls` selection per side, matched server-side on the program, the first data byte (`d1`) and the mint's account position (`a0` / `a1`) for all 94 mints at once. See [Query & Response](https://docs.envio.dev/docs/HyperSync/solana-query#instructionselection).

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python holders.py         # wallets and value held right now (Solana RPC + Jupiter prices)
python script.py          # every mint and burn in the last 7 days, by ticker
DAYS=1 python script.py
```

`holders.py` makes one `getProgramAccounts` call per mint and waits between calls, so it takes a few minutes on the public RPC. Set `SOLANA_RPC` to use your own. `script.py` splits the window into 100K-slot chunks and pulls them in parallel (`WORKERS`, default 8), backing off on rate limits. It writes every row to `stock_mint_burn.json`.

## Check the numbers yourself

- **Balances against supply:** `holders.py` prints each token's summed balances as a share of the supply stored on its mint account. They should all read 100%, give or take trades that land between the two calls.
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
HTTP 429. My API token is in ENVIO_API_TOKEN. Then read every token account for each mint with
getProgramAccounts, price the balances with Jupiter's price API and count wallets holding $1 or more.
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
