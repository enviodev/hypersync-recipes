# Phantom CASH supply on Solana

From slot 391,000,000 (3 Jan 2026) to slot 470,148,462 (16 Nov 2026), **[Phantom](https://phantom.com)'s CASH stablecoin grew 41% on Solana, from $92.3M to $130.4M**. 723 mints added $186.9M and 7.3K burns removed $148.7M. On the same day, 216.7K wallets held at least $1 of CASH and 763.3K held some.

| | |
|---|---:|
| Supply on 3 Jan 2026 | $92.26M |
| Minted (723 mints) | $186.85M |
| Burned (7,340 burns) | $148.69M |
| Supply on 16 Nov 2026 | $130.42M |
| Wallets holding at least $1 | 216,688 |
| Wallets holding any CASH | 763,252 |

## Why it's interesting

CASH is a Token-2022 stablecoin, so every unit enters and leaves through `MintTo` and `Burn` instructions on the Token-2022 program. Pull those for one mint and you have its whole supply history. The same query works for any SPL or Token-2022 stablecoin. Just change the mint.

## What it pulls

- **Token.** CASH, mint `CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH`, from [Phantom's docs](https://docs.phantom.com/cash).
- **Program.** [Token-2022](https://spl.solana.com/token-2022), `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`.
- **Instructions.** `MintTo` (tag 7) and `MintToChecked` (14), where account 0 is the mint, and `Burn` (8) and `BurnChecked` (15), where account 1 is the mint. Top-level and inner calls, successful transactions only.
- **Filter.** One `instruction_calls` selection per side, matched on the server by program, the first data byte (`d1`) and the mint's account position (`a0` or `a1`). The [query reference](https://docs.envio.dev/docs/HyperSync/solana-query#instructionselection) has the details.
- **Window.** Slot 391,000,000 (3 Jan 2026, where HyperSync's Solana history starts) to the chain head.

Here's where each number comes from. The mints, burns and weekly changes come from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). The 16 Nov supply comes from Solana RPC `getTokenSupply` at run time, and the 3 Jan supply is that figure minus every mint and burn HyperSync returned in between. The holder counts come from `holders.py`, which reads every CASH token account with Solana RPC `getProgramAccounts`.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py     # mints, burns and weekly supply since 3 Jan 2026
python3 holders.py    # wallets holding CASH right now, over Solana RPC
```

`script.py` splits the range into 5M-slot chunks and pulls them in parallel. It backs off and retries on rate limits, and stops with an error rather than return a partial range. It prints the totals and the supply at the end of each week, and writes every row to `cash_mint_burn.json`.

`holders.py` pulls a few hundred MB from `getProgramAccounts`, so point `SOLANA_RPC` at your own RPC if the public one times out.

## Change the window or token

- **Start later.** `FROM_SLOT=440000000 python3 script.py` starts the pull at that slot.
- **Speed.** `WORKERS` (default 8) sets how many chunks run at once.
- **Another stablecoin.** Swap `CASH` for another mint and `DECIMALS` for its decimals. For a token on the classic SPL Token program, swap `T22` for `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`.
- **Your own RPC.** Set `SOLANA_RPC` for the `getTokenSupply` call and for `holders.py`.

## Check the numbers

- **Supply on 16 Nov.** `holders.py` adds up every CASH token account's balance and prints it next to `getTokenSupply`. The two matched to the cent.
- **Supply at the start.** A public CASH supply chart showed $92,256,948 for 3 Jan 2026, as the comparison. The script's figure is $92,256,947.15, so the mint and burn history checks out to within a dollar.
- **Single transactions.** Every row carries its slot. Look any of them up on a Solana explorer and compare the amount.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana-query) to pull every MintTo,
MintToChecked, Burn and BurnChecked instruction on Token-2022 for the CASH mint
CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH and rebuilds supply week by week.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Point it at <ANOTHER STABLECOIN MINT> instead, with the right program and decimals,
and print daily supply for the last 30 days. Keep the standard library only. Run it
on a short slot range first, then check that the latest supply matches
getTokenSupply for that mint.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana) and [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service), if you want CASH supply live behind a GraphQL API
- [Phantom CASH developer docs](https://docs.phantom.com/cash)
- [Token-2022 program](https://spl.solana.com/token-2022)
- [Envio Discord](https://discord.gg/envio)
