# Phantom CASH supply on Solana

Pulls every mint and burn of [Phantom](https://phantom.com)'s CASH stablecoin on Solana with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana), and works out the supply week by week. A second script counts the wallets holding CASH today over Solana RPC.

## What we found

From slot 391,000,000 (3 Jan 2026) to slot 470,148,462 (16 Nov 2026):

- CASH supply on Solana grew 41%, from $92.26M to $130.42M
- 723 mints added $186.85M and 7,340 burns removed $148.69M
- 216,688 wallets hold at least $1 of CASH, and 763,252 hold some (from `holders.py`)

Supply now comes from RPC `getTokenSupply` ($130,419,427.98). Supply on 3 Jan is that figure minus every mint and burn HyperSync returned in between, which gives $92,256,947.15. A public CASH supply chart shows $92,256,948 for 3 Jan, so the mint and burn history checks out to within a dollar.

## Why it matters

CASH is a Token-2022 stablecoin, so every unit enters and leaves through `MintTo` and `Burn` instructions on the Token-2022 program. Pull those for one mint and you have its whole supply history, with no indexer to host and no RPC log scraping. The same query works for any SPL or Token-2022 stablecoin: change the mint.

## What it pulls

| | |
|---|---|
| Token | CASH, mint `CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH` ([Phantom docs](https://docs.phantom.com/cash)) |
| Program | Token-2022, `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` |
| Instructions | `MintTo` (tag 7) and `MintToChecked` (14), where account 0 is the mint; `Burn` (8) and `BurnChecked` (15), where account 1 is the mint. Outer and inner calls, successful transactions only |
| Window | Slot 391,000,000 (3 Jan 2026, the start of HyperSync's Solana history) to the chain head |

The HyperSync filter is one `instruction_calls` selection per side, matched server-side on the program, the first data byte (`d1`) and the mint's account position (`a0` / `a1`). See [Query & Response](https://docs.envio.dev/docs/HyperSync/solana-query#instructionselection).

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py          # mints, burns and weekly supply since 3 Jan 2026
python holders.py         # wallets holding CASH right now (Solana RPC)
```

`script.py` splits the range into 5M-slot chunks and pulls them in parallel (`WORKERS`, default 8). It backs off and retries on rate limits, and stops with an error rather than return a partial range. It writes every row to `cash_mint_burn.json`. Set `FROM_SLOT` to start later, and `SOLANA_RPC` to use your own RPC.

## Check the numbers yourself

- **Supply now:** `script.py` reads `getTokenSupply` for the mint over RPC. `holders.py` sums every CASH token account's balance and prints it next to `getTokenSupply`; the two match to the cent.
- **Supply at the start:** the script works it out as supply now minus (minted minus burned) inside the window. Compare it with any public CASH supply chart for 3 Jan 2026.
- **Single transactions:** every row carries its slot. Look any of them up on a Solana explorer and compare the amount.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to pull every
MintTo/MintToChecked (d1 07/0e, account a0 = mint) and Burn/BurnChecked (d1 08/0f, account a1 = mint)
instruction on the Token-2022 program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb for the mint
CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH, from slot 391000000 to the head, successful transactions
only. Page with next_slot and retry on HTTP 429. My API token is in ENVIO_API_TOKEN. Then read the live
supply with getTokenSupply and print the supply at the end of every week. After that, adapt it to
<another stablecoin mint>.
```

To turn it into a live HyperIndex indexer instead, scaffold one with `pnpx envio init` (choose Svm). `envio init` adds Envio's agent skills to the new project's `.claude/skills/` folder, so your agent has the docs in context ([Quickstart with AI](https://docs.envio.dev/docs/HyperIndex/quickstart-with-ai)).

## Links

- [HyperSync for Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [Index Solana programs with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana), to turn this into a live indexer on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Phantom CASH developer docs](https://docs.phantom.com/cash)
- [Token-2022 program](https://spl.solana.com/token-2022)
- Questions: [Envio Discord](https://discord.gg/envio)
