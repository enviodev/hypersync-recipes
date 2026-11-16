# MetaDAO launchpad raises on Solana

Pulls every instruction run by [MetaDAO](https://metadao.fi)'s launchpad programs on Solana with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana), then adds up what each completed raise asked for and what people committed to it.

## What we found

From slot 391,001,451 (3 Jan 2026) to slot 470,198,554 (16 Nov 2026):

- 25 raises completed. Their goals add up to $16.63M.
- People committed $244.85M of USDC to them, 14.7 times the goals.
- 12,916 wallets committed, and all 25 raises reached their goal.
- One raise set a $250K goal and drew $31.97M. The biggest drew $86.40M from 8,761 wallets.

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

## Why it matters

A MetaDAO raise is three instructions on one program. `initialize_launch` sets the goal, every `fund` is one wallet committing USDC, and `complete_launch` closes it. When a raise is oversubscribed the extra goes back to the backers, so the committed figure is demand, not money kept. Pull one program's instructions and you can see how much demand each raise drew, who showed up and when, with no indexer to host.

## What it pulls

| | |
|---|---|
| Programs | MetaDAO launchpad v0.4.1 to v0.8.0, IDs from the [MetaDAO programs repo](https://github.com/metaDAOproject/programs#deployments). Every 2026 raise so far ran on v0.7.0, `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM` |
| Instructions | `initialize_launch` (first argument `minimum_raise_amount`, the goal), `fund` (argument `amount`, both u64 in USDC base units) and `complete_launch`, matched by their Anchor discriminators |
| Filter | Successful transactions only, deduplicated by slot, transaction index and instruction address. Completed raises with 10 or more wallets, which leaves out test launches |
| Window | Slot 391,001,451 (3 Jan 2026, the start of HyperSync's Solana history) to the chain head |

A wallet is the `funder` account of a `fund` instruction. Wallets that backed several raises are counted once in the 12,916.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py                      # 3 Jan 2026 to the chain head
python script.py 391001451 470198554  # the exact window used above
```

The run ends with the summary:

```
Slots 391,001,451 to 470,198,554
Completed raises with 10 or more wallets: 25
Goals, added up: $16,628,000
Committed:       $244,847,736 (14.7x the goals)
Wallets that committed: 12,916
Launch accounts whose onchain total matches: 25 of 25
```

## Check the numbers yourself

- **Onchain totals:** every raise has a `Launch` account that stores its total committed amount. The script reads all of them with Solana RPC `getMultipleAccounts` and looks for the HyperSync sum in the account data. All 25 match to the last unit.
- **MetaDAO's own site:** [metadao.fi](https://metadao.fi) lists Mori Finance as raising $250,000 from 248 owners. The script gives the same goal and the same 248 wallets.
- **Single transactions:** every row carries its slot. Look any of them up on a Solana explorer and compare the USDC moved.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana) to pull every
instruction executed by the MetaDAO launchpad program moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM
from slot 391001451 to the head, successful transactions only. Page with next_slot and retry on
HTTP 429. My API token is in ENVIO_API_TOKEN. Match instructions by Anchor discriminator, the first
8 bytes of sha256("global:<name>"), for initialize_launch, fund and complete_launch. The u64 after
the discriminator is the goal for initialize_launch and the USDC amount for fund, both with 6
decimals. Account 0 is the launch. Print goal, total committed and distinct funders per completed
raise. Then turn it into a HyperIndex indexer on Solana with an onInstruction handler for each,
deployed on Envio Cloud, so new raises show up live.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana)
- [MetaDAO programs and deployments](https://github.com/metaDAOproject/programs)
- [MetaDAO docs](https://docs.metadao.fi)
- [Envio Discord](https://discord.gg/envio)
