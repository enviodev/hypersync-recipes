# Where tokenized Circle stock lives onchain

Five issuers have put tokenized Circle (CRCL) stock onchain. In one run the script counted **5.1M shares, about $380M at Coinbase's published CRCLc NAV of $73.99**. Binance bStocks was the largest issuer at $158.6M, all on BNB Chain, followed by xStocks at $124M and Ondo at $87.1M. BNB Chain held 60.7% of it.

| Issuer | Value | Share | Chains |
| --- | --- | --- | --- |
| Binance bStocks | $158.6M | 41.7% | BNB Chain |
| xStocks | $124.0M | 32.6% | X Layer, Solana, Ethereum, Ink, Mantle |
| Ondo | $87.1M | 22.9% | BNB Chain, Ethereum, Solana |
| Robinhood | $10.6M | 2.8% | Robinhood Chain |
| Coinbase | $0.1M | 0.0% | Base |

## Why it's interesting

The same stock now comes in several wrappers from several issuers on a dozen chains. If you want to know how much of one stock is onchain, you have to find every issuer's token first and then add them up. This script does both, from each issuer's own list, and then sorts the EVM supply into wallets, DEX pools and lending markets so you can see how it's being used.

## What it pulls

- Token addresses from each issuer's own list. Ondo's token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses), the [xStocks product list](https://xstocks.fi/us/products), Robinhood's [stock token API](https://docs.robinhood.com/chain/stock-tokens), Coinbase's [tokenized stocks API](https://docs.base.org/sdks/tokenized-stocks), and Binance's CRCLB entry in the Trust Wallet token registry, which links to [bstocks.finance](https://www.bstocks.finance/).
- Every ERC-20 `Transfer` of each token on the EVM chains in `CHAINS`, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Supply on BNB Chain, Ethereum, Robinhood Chain, Ink, Mantle and Base is every mint minus every burn from HyperSync.
- X Layer and Solana supply from public RPCs (`totalSupply()` and `balanceOf` on X Layer, `getTokenSupply` and `getTokenAccountsByOwner` on Solana). Those two chains, $121M of the total, don't come from HyperSync.
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

The Robinhood Chain token alone has over a million transfers, so a run takes about 20 minutes. Sample output:

```
Tokenized Circle (CRCL) stock onchain: 5,141,770 shares, $380.4M at $73.99 (Coinbase CRCLc NAV)
  Binance bStocks $  158.6M  41.7%
      BNB Chain $  158.6M
  xStocks         $  124.0M  32.6%
      X Layer   $   64.5M
      Solana    $   56.9M
      Ethereum  $    1.6M
      Ink       $    0.5M
      Mantle    $    0.5M
  Ondo            $   87.1M  22.9%
      BNB Chain $   72.3M
      Ethereum  $   12.2M
      Solana    $    2.5M
  Robinhood       $   10.6M   2.8%
      Robinhood $   10.6M
  Coinbase        $    0.1M   0.0%
      Base      $    0.1M
By chain: BNB Chain 60.7%, X Layer 17.0%, Solana 15.6%, Ethereum 3.6%, Robinhood 2.8%, Ink 0.1%, Mantle 0.1%, Base 0.0%
On the EVM chains ($256.5M), by holder type
  wallet         $  191.7M  74.7%
  other contract $   58.5M  22.8%
  dex            $    4.5M   1.8%
  lending        $    1.7M   0.7%
...
Checks
  Ondo on Ethereum: replayed supply matches totalSupply() at block 26,348,909
  ...
  Binance bStocks on BNB Chain: replayed supply matches totalSupply() at block 131,827,309
```

Tokens are minted, redeemed and traded all the time, so your numbers will differ.

## Change the window or chain

- **Another stock.** The issuer lookups match on the CRCL ticker. Change it to any stock the issuers list, such as NVDA or TSLA, to get the same breakdown for that stock.
- **Chains.** `CHAINS` maps each chain to its HyperSync subdomain and a public RPC. Add any EVM chain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) where an issuer has deployed.
- **Holder threshold.** Lower the 0.01% cut-off to classify more holders, at the cost of more RPC calls.

## Check the numbers

The script checks itself. For each EVM token it compares the supply replayed from HyperSync transfers with `totalSupply()` read over RPC at the same block, and prints a line per token. You can also compare each issuer's figure with the supply its own product page shows.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

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
