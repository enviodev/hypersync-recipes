# Who holds Coinbase's tokenized stocks on Base

Reads every transfer of every Coinbase tokenized stock on Base with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), rebuilds each address's balance, and counts how many different stocks each wallet holds.

These are the numbers behind Envio's post on tokenized stock holders on Base.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
export BASE_RPC_URL=https://mainnet.base.org   # optional, keeps wallets only
python script.py
```

The transfer scan takes a few minutes. With `BASE_RPC_URL` set, the script also calls `eth_getCode` once per holder, which takes about half an hour on a public RPC.

## What it prints

```
Coinbase tokenized stocks on Base, 338 listed, up to block 56,450,544
69,397 addresses have ever held one, 37,660 hold one now
```

That run was on 12th Nov 2026, at about 10:48 UTC, without `BASE_RPC_URL`.

With `BASE_RPC_URL` set, the same rule run at block 56,415,615 (about 08:50 UTC the same day) kept 31,976 wallets: 16,317 with no code and 15,659 EIP-7702 wallets. By different stocks held, that was:

```
Different stocks held:
  1    18,235
  2     4,484
  3     2,285
  4     2,191
  5+    4,781
Hold two or more: 13,741 (43.0%)
```

## How it counts

- The stock token list comes from Coinbase's Tokenized Stocks API, `GET https://api.coinbase.com/v1/tokenized-stocks`, linked from Base's docs on [tokenized stocks on Base](https://docs.base.org/specifications/b20/tokenized-stocks-on-base).
- The script reads every `Transfer` log from those token contracts since block 49,000,000, before the first stock token transfer in August 2026. HyperSync's default join returns each log with its block. Only logs whose address is a stock token and whose topic0 is `Transfer` are kept.
- A balance is the sum of transfers in minus transfers out for each token and address. Mints and burns use the zero address and are not counted as holders.
- A wallet is an address with no code, or an EIP-7702 delegated wallet (code starting `0xef0100`). Pools, vaults, routers and smart-account proxies are left out, so the wallet count errs on the low side.
- Checked against Base's public RPC at the same block: `balanceOf()` on 3,000 random token and holder pairs matched every rebuilt balance, and `totalSupply()` matched the sum of balances for all 72 tokens that have holders.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Base (endpoint
https://base.hypersync.xyz) to read every Transfer log of the Coinbase tokenized stocks listed at
https://api.coinbase.com/v1/tokenized-stocks. My API token is in the ENVIO_API_TOKEN environment
variable. Rebuild each address's balance per token, keep addresses with no code or EIP-7702 code,
and count how many different stocks each wallet holds.
```
