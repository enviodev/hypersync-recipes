# Where tokenized Circle stock lives onchain

Five issuers have put tokenized Circle (CRCL) stock onchain. In a run on 17 Nov 2026 the script counted **5.4M shares, about $312M at Coinbase's published CRCLc NAV of $57.445**. Binance bStocks was the largest issuer at $127.4M, all on BNB Chain, followed by xStocks at $107.2M and Ondo at $68.1M. BNB Chain held 58.9% of it. HyperSync rebuilt $206.9M of the total. The other $105.3M is xStocks on X Layer and Solana, read from public RPCs.

| Issuer | Value | Share | Chains |
| --- | --- | --- | --- |
| Binance bStocks | $127.4M | 40.8% | BNB Chain |
| xStocks | $107.2M | 34.3% | X Layer, Solana, Ethereum, Ink, Mantle |
| Ondo | $68.1M | 21.8% | BNB Chain, Ethereum, Solana |
| Robinhood | $9.3M | 3.0% | Robinhood Chain |
| Coinbase | $0.1M | 0.0% | Base |

## Why it's interesting

The same stock comes in several wrappers from several issuers on eight chains. If you want to know how much of one stock is onchain, you have to find every issuer's token first and then add them up. This script does both, from each issuer's own list, and then sorts the EVM supply into wallets, DEX pools and lending markets so you can see how it's being used.

## What it pulls

- Token addresses from each issuer's own list. Ondo's token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses), the [xStocks product list](https://xstocks.fi/us/products), Robinhood's [stock token API](https://docs.robinhood.com/chain/stock-tokens), Coinbase's [tokenized stocks API](https://docs.base.org/sdks/tokenized-stocks), and Binance's CRCLB entry in the Trust Wallet token registry, which links to [bstocks.finance](https://www.bstocks.finance/).
- Every ERC-20 `Transfer` of each token on the EVM chains in `CHAINS`, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Supply on BNB Chain, Ethereum, Robinhood Chain, Ink, Mantle and Base is every mint minus every burn from HyperSync.
- Every balance change of Ondo's CRCL token on Solana, as `account_activity` rows from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). Transfers cancel out, so the sum is every mint minus every burn. Its first balance change is at slot 394,805,673, after HyperSync's Solana history starts at slot 391,000,000, so HyperSync has all of it.
- xStocks on X Layer and Solana from public RPCs (`totalSupply()` and `balanceOf` on X Layer, `getTokenSupply` and `getTokenAccountsByOwner` on Solana). HyperSync doesn't cover X Layer, and xStocks' Solana token is older than HyperSync's Solana history, so its supply can't be summed from its first mint. Those two, $105.3M of the total, don't come from HyperSync.
- `eth_getCode` and `eth_call` on each chain's public RPC to sort large holders into wallets, DEX pools and lending markets, and `totalSupply()` to check each replayed supply.
- One price for every token, Coinbase's published NAV for CRCLc.

xStocks mints every EVM token to one wallet (`0x5f7a4c11...a2ad`) and sends it out from there, so that wallet's balance counts as not yet issued. The xStocks minter on Solana is left out the same way. xStocks' TON and Tron tokens are left out because issued and unissued balances there can't be told apart. Every token here uses a share multiplier of 1.

Holders with at least 0.01% of a token are checked onchain. DEX pools answer `factory()` and `token0()` or are a known pool manager or vault (Uniswap v4, PancakeSwap Infinity). Lending markets are Aave style tokens or a known lending singleton (Morpho, Lista DAO Moolah). Wallets have no code or an EIP-7702 delegation. Smaller holders count as wallets.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

The Robinhood Chain token alone has over a million transfers, so a run takes about 30 minutes. Sample output from the 17 Nov 2026 run.

```
Tokenized Circle (CRCL) stock onchain: 5,435,080 shares, $312.2M at $57.445 (Coinbase CRCLc NAV)
  Binance bStocks $  127.4M  40.8%
      BNB Chain $  127.4M
  xStocks         $  107.2M  34.3%
      X Layer   $   57.8M
      Solana    $   47.5M
      Ethereum  $    1.0M
      Ink       $    0.4M
      Mantle    $    0.4M
  Ondo            $   68.1M  21.8%
      BNB Chain $   56.3M
      Ethereum  $    9.8M
      Solana    $    2.0M
  Robinhood       $    9.3M   3.0%
      Robinhood $    9.3M
  Coinbase        $    0.1M   0.0%
      Base      $    0.1M
By chain: BNB Chain 58.9%, X Layer 18.5%, Solana 15.9%, Ethereum 3.5%, Robinhood 3.0%, Ink 0.1%, Mantle 0.1%, Base 0.0%
On the EVM chains ($204.9M), by holder type
  wallet         $  153.2M  74.8%
  other contract $   46.2M  22.5%
  dex            $    3.9M   1.9%
  lending        $    1.6M   0.8%
Binance Hot Wallet 20 holds 79.3% of Binance's CRCLB
Checks
  Ondo on Ethereum: replayed supply matches totalSupply() at block 26,435,241
  ...
  Binance bStocks on BNB Chain: replayed supply matches totalSupply() at block 134,135,684
  Ondo on Solana: rebuilt supply matches getTokenSupply at slot 470,567,723
  xStocks on Solana and X Layer: read from public RPCs (getTokenSupply, totalSupply()), not rebuilt
```

Tokens are minted, redeemed and traded all the time, so your numbers will differ.

## Change the window or chain

- **Another stock.** The issuer lookups match on `CRCL` (Ondo and Robinhood), `CRCLx`, `CRCLc` and the CRCLB entry in `BSTOCKS`. Change all of them to another stock the issuers list, such as NVDA or TSLA, to get the same breakdown for that stock.
- **Chains.** `CHAINS` maps each chain to its HyperSync subdomain and a public RPC. Add any EVM chain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) where an issuer has deployed.
- **Holder threshold.** Lower the 0.01% cut-off (`v * 10000 >= total`) to classify more holders, at the cost of more RPC calls.

## Check the numbers

The script checks itself. For each EVM token it compares the supply replayed from HyperSync transfers with `totalSupply()` read over RPC at the same block, and prints a line per token. For Ondo on Solana it reads `getTokenSupply` first, then sums HyperSync up to the slot that call answered from. In the 17 Nov run every token matched. You can also compare each issuer's figure with the supply its own product page shows.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to replay every Transfer of every
issuer's tokenized Circle (CRCL) stock on the EVM chains HyperSync covers, then sorts
holders into wallets, DEX pools and lending markets. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a daily series of EVM supply per issuer for the last 30 days, built from the mint
and burn transfers the script already reads, and write it to supply_daily.csv. Keep
the standard library only. Then check that the last day of each series matches the
replayed supply the script prints for that issuer.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Ondo token addresses](https://docs.ondo.finance/addresses)
- [xStocks products](https://xstocks.fi/us/products)
- [Robinhood stock tokens](https://docs.robinhood.com/chain/stock-tokens)
- [Coinbase tokenized stocks](https://docs.base.org/sdks/tokenized-stocks)
- [Envio Discord](https://discord.gg/envio)
