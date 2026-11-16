# What people borrow against on Jupiter Lend

Pulls every borrow position opened on [Jupiter Lend](https://jup.ag/lend) on Solana with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana) and groups the positions by the collateral they were opened against.

## What we found

Jupiter Lend took its first position backed by a tokenized stock on 24 Mar 2026 (slot 408,556,080). From then to slot 470,205,922 (16 Nov 2026):

- 24,361 borrow positions were opened, and 7,635 of them (31.3%) were opened against a tokenized stock or ETF.
- SPYx, the tokenized S&P 500 ETF, is the second most used collateral with 4,067 positions. Only SOL has more, with 4,453.
- 4,880 wallets opened a stock-backed position.

| Collateral | Positions opened | Wallets |
|---|---:|---:|
| SOL (WSOL) | 4,453 | 3,380 |
| **SPYx** (S&P 500 ETF) | 4,067 | 3,234 |
| JupSOL | 3,291 | 2,356 |
| JLP | 2,557 | 1,838 |
| jlJUPUSD | 1,908 | 1,237 |
| **NVDAx** (Nvidia) | 1,414 | 1,225 |
| **TSLAx** (Tesla) | 1,192 | 1,037 |
| **QQQx** (Nasdaq 100 ETF) | 962 | 790 |
| cbBTC | 855 | 689 |
| INF | 816 | 649 |

A position here is one `init_position` instruction, which is what a wallet runs before it first supplies collateral to a vault. The table counts positions opened, not dollars. By value, SOL, JupSOL and JLP are far larger.

## Why it matters

Each Jupiter Lend vault is one collateral token paired with one debt token, and every position gets a numbered NFT. That makes "what are people borrowing against" a question you can answer from one instruction on one program: read the vault id from the instruction data and count. The same pull tells a lending team which new collateral types people take up, without an indexer to host.

## What it pulls

| | |
|---|---|
| Program | Jupiter Lend vaults (borrow), `jupr81YtYssSyPt8jbnGuiWon5f6x9TcDEFxYe3Bdzi`, from Jupiter's [program addresses](https://developers.jup.ag/docs/lend/program-addresses) |
| Instruction | `init_position`, Anchor discriminator `c5140a0161a0b15b`, from the [vaults IDL](https://github.com/jup-ag/jupiter-lend/blob/main/target/idl/vaults.json). Data holds `vault_id` (u16) and `next_position_id` (u32). Account 0 is the wallet |
| Filter | Successful transactions, top-level and inner calls, matched server-side on the program and `d8` |
| Vault names | Jupiter's API, `https://lite-api.jup.ag/lend/v1/borrow/vaults`, maps each vault id to its collateral and debt token |
| Window | Slot 391,001,451 (3 Jan 2026, the start of HyperSync's Solana history) to the chain head. 33,391 positions were opened in that window |

The stock tokens are [xStocks](https://xstocks.fi): SPYx, QQQx, NVDAx and TSLAx, each with a USDC vault and a JupUSD vault.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py                      # 3 Jan 2026 to the chain head
python script.py 391001451 470205922  # the exact window used above
```

It runs 16 requests side by side and finishes in a few minutes. The run ends with:

```
Slots 391,001,451 to 470,205,922
Positions opened in the whole window: 33,391
Positions opened since slot 408,556,080: 24,361
Backed by tokenized stocks: 7,635 (31.3%), from 4,880 wallets
Vaults whose highest position id equals Jupiter's totalPositions: 86 of 89 (3 more are a few positions behind the live API)
```

## Check the numbers yourself

- **Jupiter's own count:** position ids count up from 1 inside each vault, and Jupiter's API reports `totalPositions` per vault. The script compares the highest id it saw in each vault with that figure. For the window above, 86 of 89 vaults match exactly and the other 3 had new positions after the last slot. All eight stock vaults match (SPYx/USDC 3,080, SPYx/JupUSD 987, NVDAx/USDC 1,066, NVDAx/JupUSD 348, TSLAx/USDC 899, TSLAx/JupUSD 293, QQQx/USDC 625, QQQx/JupUSD 337).
- **Single positions:** every position is an NFT. Look one up on a Solana explorer from its slot and compare the vault.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to pull every
init_position instruction (d8 c5140a0161a0b15b) on the Jupiter Lend vaults program
jupr81YtYssSyPt8jbnGuiWon5f6x9TcDEFxYe3Bdzi from slot 391001451 to the head, successful
transactions only. My API token is in ENVIO_API_TOKEN. Split the slot range into segments and run
them in parallel, paging each with next_slot. After the 8-byte discriminator the data is vault_id
(u16) then next_position_id (u32), and account 0 is the wallet. Map vault ids to tokens with
https://lite-api.jup.ag/lend/v1/borrow/vaults and print positions and wallets per collateral token.
Then add the operate instruction (d8 d96ad06374972a87) to track collateral and debt per position,
and turn it into a HyperIndex indexer on Solana, deployed on Envio Cloud, so new positions show up live.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana)
- [Jupiter Lend developer docs](https://developers.jup.ag/docs/lend) and [program addresses](https://developers.jup.ag/docs/lend/program-addresses)
- [Jupiter Lend IDLs](https://github.com/jup-ag/jupiter-lend/tree/main/target/idl)
- [Envio Discord](https://discord.gg/envio)
