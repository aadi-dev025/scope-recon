# scope-recon

A small recon tool for bug bounty / VDP work. It runs a few passive
subdomain sources at once, merges what they find into one list, and drops
anything that isn't in the program's scope.

## why

When I started doing bug bounty I kept doing the same thing by hand for
every target: query crt.sh, then hackertarget, then another site, then
copy all the results into one file and remove the duplicates. It was slow
and I'd lose track of which tool found what. Worse, a couple of times I
started poking at a host that turned out to be out of scope, which is a
good way to get kicked off a program.

So this does two things:

1. runs the passive sources together and merges them, keeping track of
   which source found each host
2. filters everything through a scope file, so out-of-scope hosts never
   even show up in the output

## passive only

It does not scan or send traffic to the target. All it does is ask public
third-party databases (certificate transparency logs, passive DNS) what
subdomains they already know about. That's the "passive" in passive recon.

The scope file is the safety rail. `out_of_scope` always beats
`in_scope`, and wildcard matching is done on a dot boundary so
`evil-example.com` doesn't sneak past a `*.example.com` rule.

## install

```
pip install -r requirements.txt
```

## use

Make a scope file (copy `scope.example.json`):

```json
{
  "program": "example-vdp",
  "in_scope": ["example.com", "*.example.com"],
  "out_of_scope": ["blog.example.com"]
}
```

Then:

```
python3 recon.py example.com --scope scope.json
```

or the wrapper, which timestamps the output into `out/`:

```
./run.sh example.com scope.json
```

Example output:

```
# recon for example.com
# 4 in-scope hosts, 2 dropped as out-of-scope

api.example.com                               [crtsh,hackertarget]
dev.example.com                               [rapiddns]
mail.example.com                              [hackertarget]
www.example.com                               [crtsh,rapiddns]
```

The `[...]` is which sources found that host. Add `--json` if you want to
pipe it into something else.

## options

```
--scope      path to the scope json (required)
--sources    comma list, default all: crtsh,hackertarget,rapiddns
--json       json output instead of the text list
--workers    how many sources to hit at once (default 4)
```

## sources

- `crtsh` -- certificate transparency logs (crt.sh)
- `hackertarget` -- hostsearch api (free, rate limited)
- `rapiddns` -- passive dns, scraped

They're in `reconlib/sources.py`. Each one is just a function that takes a
domain and returns a set of hostnames, so adding another is easy.

## tests

```
python3 -m pytest
```

The tests cover the scope logic, which is the part that can't be allowed
to get it wrong.

## what I'd do next

- add more sources (there are a bunch of free passive dns feeds)
- resolve the hosts and show which ones are actually live
- cache results so re-running the same domain doesn't re-hit everything
- the rapiddns scraper is fragile; if their html changes it just returns
  nothing instead of erroring, which is fine but not great

## notes

Only run this against targets you're actually allowed to test. The scope
file keeps the output clean but it's on you to point it at a real program.
