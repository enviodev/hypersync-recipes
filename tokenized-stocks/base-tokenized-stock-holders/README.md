# Who holds Coinbase's tokenized stocks on Base

Up to Base block 56,450,544 on 12 Nov 2026, **69.4K addresses had held at least one of Coinbase's 338 tokenized stocks on Base, and 37.7K held one at that block**. Of the 32K that were wallets, 43% held two or more different stocks.

| Different stocks held | Wallets |
| --- | --- |
| 1 | 18,235 |
| 2 | 4,484 |
| 3 | 2,285 |
| 4 | 2,191 |
| 5+ | 4,781 |

## Why it's interesting

Holder counts are the first thing people ask about a new asset class, and they're hard to get when there are hundreds of tokens. This script rebuilds every balance of every Coinbase stock token on Base from the transfer history, so you get holders across the whole catalogue in one run. The same pattern works for any token list where you want holders, first-time buyers or portfolio breadth.

## What it pulls

- The token list from Coinbase's Tokenized Stocks API, `GET https://api.coinbase.com/v1/tokenized-stocks`, linked from Base's page on [tokenized stocks on Base](https://docs.base.org/specifications/b20/tokenized-stocks-on-base).
- Every ERC-20 `Transfer` log from those contracts since Base block 49,000,000 (before the first stock token transfer in August 2026), from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). The ever-held and hold-now counts come from HyperSync.
- Optionally, one `eth_getCode` call per holder through the RPC in `BASE_RPC_URL`, to keep only wallets.

A balance is transfers in minus transfers out for each token and address. The zero address (mints and burns) is never counted as a holder. A wallet is an address with no code, or an EIP-7702 delegated wallet (code starting `0xef0100`). Pools, vaults, routers and smart-account proxies are left out, so the wallet count errs on the low side.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py

# optional, keeps wallets only and prints the stocks-held breakdown for them
export BASE_RPC_URL=https://mainnet.base.org
python3 script.py
```

The transfer scan takes a few minutes. With `BASE_RPC_URL` set it makes one `eth_getCode` call per holder, which takes about half an hour on a public RPC.

Sample output from a run on 12 Nov 2026 at about 10:48 UTC, without `BASE_RPC_URL`:

```
Coinbase tokenized stocks on Base, 338 listed, up to block 56,450,544
69,397 addresses have ever held one, 37,660 hold one now
```

The wallet table above is from a run with `BASE_RPC_URL` set at block 56,415,615, about 08:50 UTC the same day. It kept 31,976 wallets, 16,317 with no code and 15,659 EIP-7702 wallets.

```
Different stocks held:
  1    18,235
  2     4,484
  3     2,285
  4     2,191
  5+    4,781
Hold two or more: 13,741 (43.0%)
```

## Change the window or chain

- **Start block.** `START` sets where the scan begins. Raise it to count only holders who arrived after a date, using the block number for that date.
- **Token list.** Replace `stock_tokens()` with your own dict of `address: symbol` to run the same holder count on any set of ERC-20s.
- **Chain.** Swap `HS` for another chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and supply that chain's token addresses.

## Check the numbers

The rebuilt balances were checked against Base's public RPC at the same block as the comparison. `balanceOf()` on 3,000 random token and holder pairs matched every rebuilt balance, and `totalSupply()` matched the sum of balances for all 72 tokens that had holders. You can repeat it for any pair with `cast call` or the token's page on Basescan.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Base to read every Transfer of
every Coinbase tokenized stock and rebuild each holder's balance.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a per-token table with the current holder count and the number of new holders
in the last 7 days, using the first-received timestamps the script already tracks.
Keep the standard library only. Then check that the per-token holder counts, as a
set of addresses, add up to the "hold one now" total.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Tokenized stocks on Base](https://docs.base.org/specifications/b20/tokenized-stocks-on-base)
- [Envio Discord](https://discord.gg/envio)
