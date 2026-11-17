# Circles trust links on Gnosis Chain

Reads every `RegisterHuman` and `Trust` event from the [Circles](https://aboutcircles.com) v2 Hub on Gnosis Chain with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then replays them to count the trust links between humans that are live at the end of each month.

These are the numbers behind Envio's post on Circles trust links doubling in a year.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

With no arguments it reads up to the latest block. Pass an end block to rerun an exact window. The post used block 49,222,000.

```bash
python script.py 49222000
```

It reads about 1.2 million events in parallel block ranges and takes 5 to 10 minutes.

## What it prints

```
Circles v2 on Gnosis Chain, blocks 36,400,000 to 49,222,000
5,000 invitation bot accounts left out

as of           humans    live trust links
2024-10-31         271                 120
2024-11-30         387                 255
2024-12-31         462                 549
2025-01-31         844               1,984
2025-02-28       1,144               4,176
2025-03-31       1,437               5,090
2025-04-30       1,901               9,041
2025-05-31       4,749              36,100
2025-06-30       7,235              75,252
2025-07-31       8,535              98,118
2025-08-31       9,065             120,173
2025-09-30       9,491             154,870
2025-10-31       9,847             182,171
2025-11-30      10,500             191,076
2025-12-31      10,877             199,686
2026-01-31      11,907             216,559
2026-02-28      13,037             222,803
2026-03-31      14,616             217,038
2026-04-30      15,657             226,657
2026-05-31      18,144             237,791
2026-06-30      20,391             292,232
2026-07-31      21,211             326,516
2026-08-31      21,917             345,026
2026-09-30      22,443             362,480
2026-10-31      22,893             366,437
2026-11-11      23,066             366,802

2026-10-31: 366,437 live trust links between 22,893 humans, 2.01x the 182,171 on 2025-10-31
```

That run covers the Hub's first event in October 2024 to 11th November 2026.

## How it counts

- The Hub address `0xc12C1E50ABB450d6205Ea2C3Fa861b3B834d13e8` comes from the Circles docs ([The Circles Stack](https://docs.aboutcircles.com/circles-sdk/the-circles-protocol)).
- `Trust(truster, trustee, expiryTime)` is emitted when an avatar trusts another one, renews trust or removes it. Removing trust sets the expiry to the current time. A link counts as live at a month end when its latest expiry is after that moment.
- Only links where both sides are registered humans count. Links to or from groups and organisations are left out, as are links an avatar sets on itself.
- 5,000 accounts created by Circles' invitations-at-scale contract (`BotCreated` events from `0xd28b7c4f148b1f1e190840a1f7a796c5525d8902`) are registered as humans in the Hub so they can send invitations. They are left out of both the human count and the trust links.
- A link is one direction. If two humans trust each other, that is two links.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Trust and
PersonalMint event from the Circles v2 Hub on Gnosis Chain (0xc12C1E50ABB450d6205Ea2C3Fa861b3B834d13e8).
My API token is in the ENVIO_API_TOKEN environment variable. Show me, month by month, how many humans
minted their personal Circles and how many live trust links they hold.
```
