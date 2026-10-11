#!/usr/bin/env python3
"""scope-recon: run a bunch of passive subdomain sources at once, merge
them, and throw away anything that isn't in the program's scope.

I kept running crt.sh, then hackertarget, then a couple more by hand for
every target and then copy-pasting the results into one list. This does
that in one shot.

Only passive sources. It does not scan the target. The scope file decides
what shows up in the report, so you can't accidentally wander off-program.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from reconlib import scope as scopelib
from reconlib import sources
from reconlib import report


def gather(domain, source_names, workers):
    """Run the chosen sources in parallel. Returns {host: set(sources)}.
    A source that errors out just gets skipped with a warning instead of
    killing the whole run."""
    seen = {}

    def run_one(name):
        return name, sources.ALL[name](domain)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, n) for n in source_names]
        for fut in as_completed(futures):
            try:
                name, hosts = fut.result()
            except Exception as e:
                print("  ! a source failed: {}".format(e), file=sys.stderr)
                continue
            print("  + {} returned {} hosts".format(name, len(hosts)),
                  file=sys.stderr)
            for h in hosts:
                seen.setdefault(h, set()).add(name)
    return seen


def main():
    p = argparse.ArgumentParser(description="passive, scope-aware subdomain recon")
    p.add_argument("domain", help="apex domain, e.g. example.com")
    p.add_argument("-s", "--scope", required=True, help="path to scope json")
    p.add_argument("--sources", default="all",
                   help="comma list: crtsh,hackertarget,rapiddns (default all)")
    p.add_argument("--json", action="store_true", help="output json instead of text")
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    if args.sources == "all":
        chosen = list(sources.ALL.keys())
    else:
        chosen = [s.strip() for s in args.sources.split(",") if s.strip()]
        bad = [s for s in chosen if s not in sources.ALL]
        if bad:
            p.error("unknown source(s): {}".format(", ".join(bad)))

    sc = scopelib.load(args.scope)

    print("[*] gathering from: {}".format(", ".join(chosen)), file=sys.stderr)
    seen = gather(args.domain, chosen, args.workers)

    # scope filter. this is the part that matters.
    all_hosts = sorted(seen.keys())
    kept = sc.filter(all_hosts)
    dropped = len(all_hosts) - len(kept)

    result = {
        "domain": args.domain,
        "sources": chosen,
        "in_scope": kept,
        "dropped": dropped,
        "seen_in": {h: sorted(seen[h]) for h in kept},
    }

    out = report.to_json(result) if args.json else report.to_text(result)
    sys.stdout.write(out)
    print("[*] done: {} in scope, {} dropped".format(len(kept), dropped),
          file=sys.stderr)


if __name__ == "__main__":
    main()
