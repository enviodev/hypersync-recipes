# Phantom CASH supply on Solana

From slot 391,000,000 (3 Jan 2026) to slot 470,988,448 (18 Nov 2026), **[Phantom](https://phantom.com)'s CASH stablecoin grew 41% on Solana, from $92.1M to $130.0M**. 724 mints added $187.9M and 7.4K burns removed $150.0M. At the same slot, 212.5K wallets held at least $1 of CASH and 749.8K held some. HyperSync produced every one of these numbers.

| | |
|---|---:|
| Supply on 3 Jan 2026 (slot 391,000,000) | $92.07M |
| Minted (724 mints) | $187.90M |
| Burned (7,358 burns) | $150.01M |
| Supply on 18 Nov 2026 (slot 470,988,448) | $129.96M |
| Wallets holding at least $1 | 212,549 |
| Wallets holding any CASH | 749,777 |

## Why it's interesting

CASH is a Token-2022 stablecoin, so every unit enters and leaves through `MintTo` and `Burn` instructions on the Token-2022 program, and every balance it touches shows up in HyperSync's `account_activity` table. Pull those for one mint and you have its supply, its holders and its whole history since 3 Jan. The same queries work for any SPL or Token-2022 stablecoin. Just change the mint.

## What it pulls

- **Token.** CASH, mint `CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH`, from [Phantom's docs](https://docs.phantom.com/cash).
- **Supply and holders (`holders.py`).** Every `account_activity` row for the CASH mint from slot 391,000,000, where HyperSync's Solana history starts, to the chain head. That's 123.2M balance rows across 2.4M token accounts. The script keeps the latest balance of each token account, adds them up for the supply and groups them by owner for the holder counts, then saves the supply and its slot to `snapshot.json`.
- **Mints and burns (`script.py`).** `MintTo` (tag 7) and `MintToChecked` (14), where account 0 is the mint, and `Burn` (8) and `BurnChecked` (15), where account 1 is the mint. Top-level and inner calls, successful transactions only, matched on the server by program, the first data byte (`d1`) and the mint's account position (`a0` or `a1`). The [query reference](https://docs.envio.dev/docs/HyperSync/solana-query#instructionselection) has the details.
- **Supply over time.** `script.py` starts from the supply in `snapshot.json` and works back through every mint and burn, so the 3 Jan supply and the weekly series come from HyperSync too.

The supply, the holder counts, the mints and burns and the weekly series all come from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). Solana RPC `getTokenSupply` is read only as a labelled check.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 holders.py    # supply and wallets holding CASH, from HyperSync balances
python3 script.py     # mints, burns and weekly supply since 3 Jan 2026
```

Run `holders.py` first. It reads the full range in 200K-slot pieces and `script.py` in 500K-slot pieces. Both run in parallel, save each piece as they go (under `chunks/` and `mint_burn/`) and pick up where they left off if you stop them. A full first run takes about an hour. `script.py` also writes every mint and burn to `cash_mint_burn.json`.

Sample output from the 18 Nov 2026 run.

```
$ python3 holders.py
slots 391,000,000 to 470,988,448, 124,067,719 balance rows read
token accounts seen       2,418,311
wallets with any CASH     749,777
wallets with >= $1        212,549
wallets with >= $10       92,917
sum of balances           $129,963,449.12
...
$ python3 script.py
slots 391,000,000 to 470,988,448
mints 724  burns 7,358
minted $187,897,439.39  burned $150,007,406.39  net $37,890,033.00
supply at slot 470,988,448 (HyperSync balances, holders.py) $129,963,449.12
supply at slot 391,000,000 (that minus net) $92,073,416.12
change +41.2%
Check (RPC getTokenSupply at slot 470,989,790, less 0.00 net minted since)
  $130,146,980.14 at slot 470,988,448
  HyperSync is $183,531.02 lower (0.14%)
  CASH in accounts with no activity since slot 391,000,000

week of     supply at week end
2025-12-29  $92,073,406
...
2026-11-02  $130,177,830
2026-11-09  $131,645,866
2026-11-16  $129,963,449
```

## Change the window or token

- **Start later.** `FROM_SLOT=440000000 python3 script.py` starts the mint and burn pull at that slot.
- **Speed.** `WORKERS` sets how many pieces run at once (16 for `holders.py`, 24 for `script.py`).
- **Another stablecoin.** Swap `CASH` for another mint and `DECIMALS` for its decimals in both scripts. For a token on the classic SPL Token program, swap `T22` for `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`. If the token is older than 3 Jan 2026, some of its accounts may not have moved since, and the check line tells you how much that leaves out.

## Check the numbers

- **Supply on 18 Nov.** Both scripts print Solana RPC `getTokenSupply` as the comparison. RPC read $130,146,980.14 at slot 470,989,790, and the net minted between slot 470,988,448 and that slot was $0.00, so it's the same supply. HyperSync's $129,963,449.12 is $183,531.02 (0.14%) lower. That's CASH in token accounts that haven't moved since 3 Jan 2026, before HyperSync's Solana history starts, so they have no `account_activity` row yet. The holder counts are lower bounds for the same reason.
- **Supply on 3 Jan.** On RPC numbers the same mint and burn history gives $92,256,947.15, which matches a public CASH supply chart's $92,256,948 for that day to within a dollar.
- **Single transactions.** Every mint and burn row carries its slot. Look any of them up on a Solana explorer and compare the amount.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read holders.py, script.py and README.md in this folder. They use HyperSync on
Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to add up every CASH
balance from account_activity rows and to pull every MintTo, MintToChecked, Burn
and BurnChecked instruction on Token-2022 for the CASH mint
CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH, then rebuild supply week by week.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Point both at <ANOTHER STABLECOIN MINT> instead, with the right program and
decimals, and print daily supply for the last 30 days. Keep the standard library
only. Run it on a short slot range first, then check that the latest supply
matches getTokenSupply for that mint.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana) and [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service), if you want CASH supply live behind a GraphQL API
- [Phantom CASH developer docs](https://docs.phantom.com/cash)
- [Token-2022 program](https://spl.solana.com/token-2022)
- [Envio Discord](https://discord.gg/envio)
