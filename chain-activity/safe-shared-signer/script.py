"""New Safes on Ethereum in 2025 and 2026, and the 2026 Safes that share one second signer.

Reads every ProxyCreation from Safe's canonical 1.3.0, 1.4.1 and 1.5.0 proxy factories on Ethereum with
Envio HyperSync, keeps proxies that point at an official Safe singleton, and decodes each Safe's SafeSetup
event (owners and threshold). Python 3 standard library only. Set ENVIO_API_TOKEN first.
"""
import collections, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
URL = "https://1.hypersync.xyz"
DEPLOYMENTS = "https://raw.githubusercontent.com/safe-global/safe-deployments/main/src/assets/"
FACTORY_FILES = ["v1.3.0/proxy_factory.json", "v1.4.1/safe_proxy_factory.json", "v1.5.0/safe_proxy_factory.json"]
SINGLETON_FILES = ["v1.3.0/gnosis_safe.json", "v1.3.0/gnosis_safe_l2.json", "v1.4.1/safe.json",
                   "v1.4.1/safe_l2.json", "v1.5.0/safe.json", "v1.5.0/safe_l2.json"]
PROXY_CREATION = "0x4f51faf6c4561ff95f067657e43439f0f856d97c04d9ec9070a6199ad418e235"  # ProxyCreation(address,address)
SAFE_SETUP = "0x141df868a6331af528e38c83b7aa03edc19be66e37ae67f9285bf4f8e3c6a1a8"      # SafeSetup(address,address[],uint256,address,address)
START_BLOCK = 21_500_000  # late December 2024, safely before 1 Jan 2025


def get(url, body=None):
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if ".hypersync.xyz" in url:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    for attempt in range(10):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def addresses(files):
    out = set()
    for f in files:
        for d in get(DEPLOYMENTS + f)["deployments"].values():
            if d["address"]:
                out.add(d["address"].lower())
    return out


FACTORIES, SINGLETONS = sorted(addresses(FACTORY_FILES)), addresses(SINGLETON_FILES)


def scan(job):
    first, last = job
    body = {"from_block": first, "to_block": last,
            "logs": [{"address": FACTORIES, "topics": [[PROXY_CREATION]]}, {"topics": [[SAFE_SETUP]]}],
            "field_selection": {"log": ["block_number", "address", "topic0", "topic1", "data"], "block": ["number", "timestamp"]}}
    created, setups = {}, {}
    while True:
        res = get(URL + "/query", body)
        times = {}
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                n = b["number"]
                times[int(n, 16) if isinstance(n, str) else n] = int(b["timestamp"], 16)
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                data = log["data"][2:]
                if log["topic0"] == PROXY_CREATION:
                    if log.get("topic1"):  # 1.4.1 and later: proxy indexed, singleton in data
                        proxy, singleton = log["topic1"][-40:], data[24:64]
                    else:  # 1.3.0: both in data
                        proxy, singleton = data[24:64], data[88:128]
                    if "0x" + singleton in SINGLETONS:
                        created.setdefault(proxy, times[log["block_number"]])
                else:
                    words = [data[i:i + 64] for i in range(0, len(data), 64)]
                    threshold, n = int(words[1], 16), int(words[4], 16)
                    owners = tuple("0x" + w[24:] for w in words[5:5 + n])
                    setups.setdefault(log["address"][2:].lower(), (threshold, owners))
        if res["next_block"] >= last:
            return created, setups
        body["from_block"] = res["next_block"]


def main():
    height = get(URL + "/height")["height"] + 1
    step = (height - START_BLOCK) // 32 + 1
    jobs = [(s, min(s + step, height)) for s in range(START_BLOCK, height, step)]
    created, setups = {}, {}
    with ThreadPoolExecutor(12) as pool:
        for c, s in pool.map(scan, jobs):
            for k, v in c.items():
                created.setdefault(k, v)
            for k, v in s.items():
                setups.setdefault(k, v)
    year = lambda t: datetime.fromtimestamp(t, timezone.utc).year
    y25 = [p for p, t in created.items() if year(t) == 2025]
    y26 = [p for p, t in created.items() if year(t) == 2026]
    print("New Safes on Ethereum from Safe's 1.3.0, 1.4.1 and 1.5.0 factories, up to block %s" % format(height - 1, ","))
    print("  2025: %s" % format(len(y25), ","))
    print("  2026 so far: %s (%.1fx 2025)" % (format(len(y26), ","), len(y26) / len(y25)))
    dist = collections.Counter("%d-of-%d" % (setups[p][0], len(setups[p][1])) for p in y26 if p in setups)
    print("2026 setups: " + ", ".join("%s %s" % (k, format(v, ",")) for k, v in dist.most_common(5)))
    co = collections.Counter(o for p in y26 if p in setups and setups[p][0] == 2 and len(setups[p][1]) == 2 for o in set(setups[p][1]))
    signer, count = co.most_common(1)[0]
    print("Most common owner across 2026 2-of-2 Safes: %s on %s Safes (%.1f%% of all 2026 Safes)" % (signer, format(count, ","), 100 * count / len(y26)))
    print("Every other 2026 Safe: %s" % format(len(y26) - count, ","))


if __name__ == "__main__":
    main()
