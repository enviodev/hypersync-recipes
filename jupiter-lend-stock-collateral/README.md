# What people borrow against on Jupiter Lend

Jupiter Lend took its first position backed by a tokenized stock on 24 Mar 2026 (slot 408,556,080). From then to slot 470,205,922 (16 Nov 2026), **24.4K borrow positions were opened, and 7.6K of them (31.3%) were backed by a tokenized stock or ETF**. SPYx, the tokenized S&P 500 ETF, was the second most used collateral with 4.1K positions, just behind SOL at 4.5K. 4.9K wallets opened a stock-backed position.

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

A position here is one `init_position` instruction, which a wallet runs before it first supplies collateral to a vault. The table counts positions opened, not dollars. By value, SOL, JupSOL and JLP are much larger.

## Why it's interesting

Each Jupiter Lend vault pairs one collateral token with one debt token, and every position gets a numbered NFT. So "what are people borrowing against" comes down to one instruction on one program. Read the vault id from the instruction data and count. If you run a lending market, it's a quick way to see which new collateral people actually pick up.

## What it pulls

- **Program.** Jupiter Lend vaults (borrow), `jupr81YtYssSyPt8jbnGuiWon5f6x9TcDEFxYe3Bdzi`, from Jupiter's [program addresses](https://developers.jup.ag/docs/lend/program-addresses).
- **Instruction.** `init_position`, Anchor discriminator `c5140a0161a0b15b`, from the [vaults IDL](https://github.com/jup-ag/jupiter-lend/blob/main/target/idl/vaults.json). The data holds `vault_id` (u16) and `next_position_id` (u32), and account 0 is the wallet.
- **Filter.** Successful transactions, top-level and inner calls, matched on the server by program and `d8`.
- **Vault names.** Jupiter's API at `https://lite-api.jup.ag/lend/v1/borrow/vaults` maps each vault id to its collateral and debt token.
- **Window.** Slot 391,001,451 (3 Jan 2026, where HyperSync's Solana history starts) to the chain head. 33.4K positions were opened in that whole window. The table above starts at the first stock-backed position.

The stock tokens are [xStocks](https://xstocks.fi). SPYx, QQQx, NVDAx and TSLAx each have a USDC vault and a JupUSD vault.

Every position count comes from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). Jupiter's API only supplies the token names and the cross-check below.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                      # 3 Jan 2026 to the chain head
python3 script.py 391001451 470205922  # the exact window used above
```

It runs 16 requests side by side and finishes in a few minutes. It prints the collateral table and ends like this.

```
Slots 391,001,451 to 470,205,922
Positions opened in the whole window: 33,391
Positions opened since slot 408,556,080: 24,361
Backed by tokenized stocks: 7,635 (31.3%), from 4,880 wallets
Vaults whose highest position id equals Jupiter's totalPositions: 86 of 89 (3 more are a few positions behind the live API)
```

## Change the window

- **Slots.** Pass a start and end slot as the two arguments. With no arguments it runs from 3 Jan 2026 to the head. HyperSync's Solana history starts at slot 391,001,451, so an earlier start won't add anything.
- **Which tokens count as stocks.** Edit the `STOCKS` set at the top of `script.py` when Jupiter adds new stock vaults.
- **Speed.** `WORKERS` sets how many requests run at once and `SEGMENT` how many slots each one covers.

## Check the numbers

Position ids count up from 1 inside each vault, and Jupiter's API reports `totalPositions` per vault. The script compares the highest id it saw in each vault with that figure, using Jupiter's API as the comparison. For the window above, 86 of 89 vaults matched exactly and the other 3 had new positions after the last slot. All eight stock vaults matched (SPYx/USDC 3,080, SPYx/JupUSD 987, NVDAx/USDC 1,066, NVDAx/JupUSD 348, TSLAx/USDC 899, TSLAx/JupUSD 293, QQQx/USDC 625, QQQx/JupUSD 337).

You can also look any single position up on a Solana explorer from its slot and compare the vault.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana-query) to pull every init_position
instruction (d8 c5140a0161a0b15b) on the Jupiter Lend vaults program
jupr81YtYssSyPt8jbnGuiWon5f6x9TcDEFxYe3Bdzi and counts positions per collateral token.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add the operate instruction (d8 d96ad06374972a87) so it also tracks collateral and
debt per position, and print the total collateral deposited per stock token. Keep
the standard library only. Run it on a short slot range first, then check one
position's collateral against the position NFT on a Solana explorer.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana), if you want new positions live behind a GraphQL API
- [Jupiter Lend developer docs](https://developers.jup.ag/docs/lend) and [program addresses](https://developers.jup.ag/docs/lend/program-addresses)
- [Jupiter Lend IDLs](https://github.com/jup-ag/jupiter-lend/tree/main/target/idl)
- [Envio Discord](https://discord.gg/envio)
