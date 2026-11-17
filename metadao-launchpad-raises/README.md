# MetaDAO launchpad raises on Solana

From slot 391,001,451 (3 Jan 2026) to slot 470,198,554 (16 Nov 2026), **25 raises completed on [MetaDAO](https://metadao.fi)'s launchpad, and people committed $244.8M of USDC against goals that added up to $16.6M**. That's 14.7 times the goals, from 12.9K wallets. All 25 reached their goal. One set a $250K goal and drew $32M, and the biggest drew $86.4M from 8.8K wallets.

| Raise | First commitment | Goal (USDC) | Committed (USDC) | x goal | Wallets |
|---|---|---|---|---|---|
| Ranger | 2026-01-06 | 6,000,000 | 86,398,012 | 14.4 | 8,761 |
| Credible Finance | 2026-07-13 | 2,000,000 | 32,775,016 | 16.4 | 790 |
| Rip Cars | 2026-07-21 | 250,000 | 31,968,872 | 127.9 | 723 |
| Laso Finance | 2026-06-30 | 750,000 | 25,637,316 | 34.2 | 715 |
| Jurassic | 2026-05-08 | 200,000 | 15,287,173 | 76.4 | 906 |
| Futardio cult | 2026-03-03 | 50,000 | 11,402,898 | 228.1 | 725 |
| ORDR | 2026-07-27 | 150,000 | 9,286,571 | 61.9 | 293 |
| SAT | 2026-11-05 | 100,000 | 7,911,340 | 79.1 | 227 |
| Mori Finance | 2026-11-09 | 250,000 | 7,700,010 | 30.8 | 248 |
| P2P Protocol | 2026-03-26 | 6,000,000 | 7,155,515 | 1.2 | 759 |
| Superclaw | 2026-03-04 | 50,000 | 5,950,859 | 119.0 | 290 |
| Kimia | 2026-08-01 | 60,000 | 727,114 | 12.1 | 58 |
| The Syndicate | 2026-10-07 | 250,000 | 631,771 | 2.5 | 200 |
| Cope | 2026-11-02 | 50,000 | 371,969 | 7.4 | 41 |
| MimiKrew | 2026-10-12 | 20,000 | 354,145 | 17.7 | 51 |
| DRAWUP | 2026-10-19 | 20,000 | 348,006 | 17.4 | 28 |
| HiveBits | 2026-09-07 | 140,000 | 242,675 | 1.7 | 150 |
| GeSIM | 2026-06-02 | 28,000 | 200,500 | 7.2 | 47 |
| PREDICT | 2026-09-21 | 10,000 | 163,023 | 16.3 | 52 |
| The Inner Table | 2026-10-20 | 150,000 | 159,454 | 1.1 | 81 |
| ACCRUE | 2026-09-14 | 10,000 | 55,402 | 5.5 | 39 |
| Final | 2026-11-06 | 50,000 | 50,858 | 1.0 | 54 |
| LFOWN | 2026-09-07 | 10,000 | 31,727 | 3.2 | 28 |
| Orendal | 2026-10-18 | 20,000 | 20,000 | 1.0 | 19 |
| Basket | 2026-07-29 | 10,000 | 17,509 | 1.8 | 29 |

Names are the token names each raise set onchain.

## Why it's interesting

A MetaDAO raise is three instructions on one program. `initialize_launch` sets the goal, every `fund` is one wallet committing USDC, and `complete_launch` closes it. When a raise is oversubscribed the extra goes back to the backers, so the committed figure shows demand, not money kept. Pull one program's instructions and you can see how much demand each raise drew, who showed up and when.

## What it pulls

- **Programs.** MetaDAO launchpad v0.4.1 to v0.8.0, with IDs from the [MetaDAO programs repo](https://github.com/metaDAOproject/programs#deployments). The 2026 raises above ran on v0.7.0, `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM`.
- **Instructions.** `initialize_launch` (its first argument, `minimum_raise_amount`, is the goal), `fund` (its `amount`) and `complete_launch`, matched by their Anchor discriminators. Both amounts are u64 in USDC base units.
- **Filter.** Successful transactions only, deduplicated by slot, transaction index and instruction address. Only completed raises with 10 or more wallets count, which leaves out test launches.
- **Window.** Slot 391,001,451 (3 Jan 2026, where HyperSync's Solana history starts) to the chain head.

A wallet is the `funder` account of a `fund` instruction. Wallets that backed several raises are counted once in the 12.9K.

Every goal, commitment and wallet count comes from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). Solana RPC is only used for the check at the end.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                      # 3 Jan 2026 to the chain head
python3 script.py 391001451 470198554  # the exact window used above
```

It prints one row per raise and ends with this summary.

```
Slots 391,001,451 to 470,198,554
Completed raises with 10 or more wallets: 25
Goals, added up: $16,628,000
Committed:       $244,847,736 (14.7x the goals)
Wallets that committed: 12,916
Launch accounts whose onchain total matches: 25 of 25
```

## Change the window

- **Slots.** Pass a start and end slot as the two arguments. With none it runs from 3 Jan 2026 to the head, so new raises show up on their own.
- **Test launches.** `MIN_WALLETS` is 10. Set it to 1 to see every completed launch.
- **New program versions.** When MetaDAO deploys a new launchpad, add its ID to `PROGRAMS`.
- **Your own RPC.** Set `SOLANA_RPC` to use your own endpoint for the check.

## Check the numbers

- **Onchain totals.** Every raise has a `Launch` account that stores its total committed amount. The script reads them all with Solana RPC `getMultipleAccounts` as the comparison and looks for the HyperSync sum in the account data. All 25 matched to the last unit.
- **MetaDAO's own site.** [metadao.fi](https://metadao.fi) listed Mori Finance as raising $250K from 248 owners. The script gives the same goal and the same 248 wallets.
- **Single transactions.** Look any raise's slot up on a Solana explorer and compare the USDC moved.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana-query) to pull every instruction on
MetaDAO's launchpad programs and decodes initialize_launch, fund and
complete_launch by Anchor discriminator. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a per-raise breakdown of commitments by size (under $1K, $1K to $10K, $10K to
$100K, over $100K) and print how many wallets fall in each band. Keep the standard
library only. Run it on a short slot range around one raise first, then check that
the bands add up to that raise's total committed and wallet count.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana), if you want new raises live behind a GraphQL API
- [MetaDAO programs and deployments](https://github.com/metaDAOproject/programs)
- [MetaDAO docs](https://docs.metadao.fi)
- [Envio Discord](https://discord.gg/envio)
