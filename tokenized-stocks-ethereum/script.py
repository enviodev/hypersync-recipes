# Tokenized stocks on Ethereum: which ones move the most, with Envio HyperSync.
# Reads every Transfer of every Ondo Global Markets and xStocks token on Ethereum over the last 30 full UTC days,
# then counts the transactions each token appears in. Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import csv
import datetime
import io
import json
import os
import re
import sys
import time
import urllib.request

URL = "https://eth.hypersync.xyz"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
# Ondo's token sheet, linked from https://docs.ondo.finance/addresses
ONDO_SHEET = ("https://www.dropbox.com/scl/fi/qjfxyg748mx0dwi6up86d/EXTERNAL-Ondo-GM-Tokens-Ondo-GM-Tokens.csv"
              "?rlkey=n3no1w78wrah3umsl0nr9s77i&dl=1")
# xStocks product list, with each token's Ethereum address
XSTOCKS = "https://xstocks.fi/us/products"
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
END = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.datetime.now(datetime.timezone.utc).date()

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read().decode()


def post(path, body=None):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


tokens = {}
for row in csv.DictReader(io.StringIO(fetch(ONDO_SHEET))):
    address = row["Ethereum Deployed Address"].strip().lower()
    if address and row["Type"] in ("Stock", "ETF"):
        tokens[address] = (row["Stock Name"], row["Symbol"])
page = fetch(XSTOCKS)
products = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S).group(1))
for p in products["props"]["pageProps"]["products"]:
    address = (p.get("addresses") or {}).get("ethereum")
    if address:
        tokens[address.lower()] = (p["name"].replace(" xStock", ""), p["symbol"])
print(f"{len(tokens)} Ondo and xStocks stock tokens on Ethereum")

start_ts = datetime.datetime.combine(END - datetime.timedelta(days=DAYS), datetime.time(), datetime.timezone.utc).timestamp()
end_ts = datetime.datetime.combine(END, datetime.time(), datetime.timezone.utc).timestamp()
# Blocks are 12 seconds, so start a little more than DAYS back and trim by timestamp.
height = post("/height")["height"]
first_block = height - (DAYS + (datetime.datetime.now(datetime.timezone.utc).date() - END).days + 2) * 7200

txs = collections.defaultdict(set)
wallets = collections.defaultdict(set)
weekly = collections.defaultdict(lambda: [set(), set()])  # transactions in the first and last 7 days
addresses = list(tokens)
for i in range(0, len(addresses), 500):
    chunk = set(addresses[i:i + 500])
    body = {"from_block": first_block, "logs": [{"address": list(chunk), "topics": [[TRANSFER]]}],
            "field_selection": {"block": ["number", "timestamp"],
                                "log": ["block_number", "address", "topic0", "topic1", "topic2", "transaction_hash"]}}
    while True:
        res = post("/query", body)
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                address = log["address"].lower()
                if address in chunk and log["topic0"] == TRANSFER and start_ts <= ts[log["block_number"]] < end_ts:
                    txs[address].add(log["transaction_hash"])
                    for topic in (log.get("topic1"), log.get("topic2")):
                        if topic and int(topic, 16):
                            wallets[address].add(topic[-40:])
                    t = ts[log["block_number"]]
                    if t < start_ts + 7 * 86400:
                        weekly[address][0].add(log["transaction_hash"])
                    elif t >= end_ts - 7 * 86400:
                        weekly[address][1].add(log["transaction_hash"])
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]

every_tx = set().union(*txs.values())
print(f"Transactions with a stock token transfer, {END - datetime.timedelta(days=DAYS):%d %b} to "
      f"{END - datetime.timedelta(days=1):%d %b} UTC  {len(every_tx):,}")
print(f"Tokens that moved  {len(txs):,}")
for address in sorted(txs, key=lambda a: -len(txs[a]))[:10]:
    name, symbol = tokens[address]
    n = len(txs[address])
    first, last = len(weekly[address][0]), len(weekly[address][1])
    print(f"  {symbol:<9} {name[:28]:<28} {n:>8,}  {n / len(every_tx):6.1%}  "
          f"{len(wallets[address]):>6,} wallets  first 7 days {first:>6,}  last 7 days {last:>6,}")
