# Uniswap v4 hooks on Ethereum

Reads every pool created on Uniswap v4 on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and counts how many use a hook, month by month.

These are the numbers behind Envio's post on Uniswap v4 hooks on Ethereum.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It prints the totals, pools per month and the most used hook contracts.

## How it counts

- Every pool starts with an `Initialize` event on the PoolManager, `0x000000000004444c5dc75cB358380D2e3dE08A90`, from [Uniswap's v4 deployments](https://docs.uniswap.org/contracts/v4/deployments).
- A pool uses a hook when the `hooks` address in its `Initialize` event isn't the zero address.
- Only logs whose address and event signature match are counted.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Initialize event on the Uniswap v4 PoolManager on Ethereum
(0x000000000004444c5dc75cB358380D2e3dE08A90). My API token is in the
ENVIO_API_TOKEN environment variable. Count new pools per month, split by whether
they use a hook, and show me the 20 most used hook contracts.
```
