# USDC supply on Ethereum, day by day

In the 30 days from 5 Oct to 3 Nov 2026, **$25.1B of USDC was minted on Ethereum and $27.3B was burned**. That's $52.4B moving in and out of supply in a month, for a net change of -$2.2B.

| | 5 Oct to 3 Nov 2026 |
| --- | --- |
| Minted | 25.10B USDC |
| Burned | 27.32B USDC |
| Moved in and out | 52.42B USDC |
| Net | -2.22B USDC |

## Why it's interesting

Every dollar of USDC that enters or leaves Ethereum shows up as a mint or a burn on one contract. Add those up and you've got supply for any day you like, with no node and no balance snapshots. It's the simplest way to follow a stablecoin's flows, and the same script works for any ERC-20 that mints from and burns to the zero address.

## What it pulls

- Every `Transfer` log on USDC [`0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`](https://etherscan.io/address/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48) where the sender or the receiver is the zero address. The address comes from Circle's [USDC contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).
- A transfer from the zero address is a mint and a transfer to it is a burn. Days are UTC.

Every number here comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 30               # the last 30 days
python3 script.py 30 2026-11-04    # the 30 days before 4 Nov 2026, the window above
```

Sample output from the window above.

```
python script.py 30 2026-11-04
Net USDC minted or burned on Ethereum per UTC day, 05 Oct to 03 Nov
05 Oct      -52.7M USDC
...
03 Nov     -404.0M USDC
Minted    25.10B USDC
Burned    27.32B USDC
Total moved in and out  52.42B USDC, net -2.22B
```

Without an end date the window ends today, so the last day is partial and your numbers will differ.

## Change the window or chain

- **Window.** The first argument is the number of days. The second is an end date (UTC, not included), so you can rerun any past window exactly.
- **Chain.** USDC runs on many chains. Change `URL` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `USDC` to Circle's address for that chain.
- **Token.** Swap `USDC` for any other token that mints from and burns to the zero address, and adjust the decimals if they aren't 6.

## Check the numbers

USDC keeps its own total. The change in `totalSupply()` between the first blocks of two days should equal that day's mints minus burns, and it did on every day of the window above. Read it over a public RPC as the comparison.

```bash
cast call 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 "totalSupply()(uint256)" \
  --rpc-url https://ethereum-rpc.publicnode.com --block <BLOCK>
```

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every USDC mint and burn
on Ethereum and add them up by UTC day. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add Base and Arbitrum. Take each chain's HyperSync URL from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks and its USDC
address from https://developers.circle.com/stablecoins/usdc-contract-addresses,
then print one table of net minted per chain per day for the last 30 days. Keep
the standard library only. Then check one day on Base against the change in
USDC totalSupply() between the first block of that day and the next.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Circle USDC contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses)
- [Envio Discord](https://discord.gg/envio)
