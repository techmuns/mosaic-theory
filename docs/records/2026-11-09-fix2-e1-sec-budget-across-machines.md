---
id:
status: open
date: 2026-11-09
prs: []
supersedes:
superseded-by:
---

# The SEC budget is the user's, not one machine's: each machine takes a declared third of 8 a second (2.67), and every redirect hop takes a slot (TeamNostra fix request 2, RE1-D1 and RE1-D2)

**WHAT.**
- **RE1-D1.** `vinci/netcache.py` now states the budget as the USER's total and splits it:
  - `SEC_USER_MAX_REQUESTS_PER_SEC = 8`: SEC's 10, less 2 in hand, for every machine together;
  - `SEC_MACHINES = 3`: the operator's two Macs and one GitHub Actions runner;
  - `SEC_MAX_REQUESTS_PER_SEC = 8 / 3 ≈ 2.67`: what one machine's shared pace file allows.

  Before, that pace file allowed 8 a second on each machine, so two machines sent 16.
- **RE1-D2.** The client no longer lets httpx follow redirects. `CachedHttp._send` follows each
  hop itself, and paces every hop by its OWN host (this instance's interval, plus an SEC slot when
  the hop is SEC's). It stops after 20 hops, httpx's default, and a refusal is judged by the host
  that answered.
- Nothing else about pacing changes: the one-token bucket, the flock'd file, the refusal hold-off
  and the process-wide stop are as #854 built them.

**WHY.**
- **SEC's own words settle the two-machine question, with no probe of the limit.** Read
  2026-11-09:
  - The Internet Security Policy (`sec.gov/privacy`): "Current guidelines limit users to a total of
    no more than 10 requests per second, regardless of the number of machines used to submit
    requests."
  - The developer page (`sec.gov/about/developer-resources`) says it of "each user", in the same
    words.
  - On enforcement, the Policy: "If a user or application submits more than 10 requests per
    second, further requests from the IP address(es) may be limited for a brief period", and access
    resumes "once the rate of requests has dropped below the threshold for 10 minutes".
  - "Accessing EDGAR Data" (`sec.gov/os/accessing-edgar-data`) gives the rate ("10
    requests/second") and the User-Agent format, but says nothing about machines.

  So the ceiling is the user's, whatever the number of machines. The limiter acts on IP addresses,
  in the plural. Two Macs at 8 a second each break the stated rule whether or not they share an
  address, and behind one address they would trip the limiter. This settles document 15 §5's open
  question ("how SEC treats two machines at 8 requests a second each") from SEC's documentation,
  as it asked.
- **Why three, not two.** Every workflow that reads SEC is `workflow_dispatch` only:
  - `monthly-score`;
  - `theme-intelligence-weekly`;
  - `weekly-screen`;
  - `validate-keys`.

  A run can therefore start while a Mac is working, and a runner is a machine sending as the same
  user (the same declared contact). Leaving it out would let a Mac, a Mac and a runner send 12 a
  second.
- **Why a committed constant, and not an env var per machine.** An env var lives on one machine,
  so two machines could each declare a whole share and be back at 16. A constant in git is the
  same number on every machine that pulls it.

**THE PROPOSED DESIGN (for the operator), and what is built.**
1. **Built now: a declared, equal share.** Each machine paces at 8 ÷ `SEC_MACHINES`, with no
   coordination and nothing that can fail open. It is safe by arithmetic. Each machine's bucket
   lets ceil(2.67) = 3 requests through any one-second window, so all three machines flat out send
   at most **9** in any second, under SEC's 10. The cost is speed (below).
2. **Proposed, not built: a lease coordinator in the R2 bucket the fact layer already uses.**
   - A machine about to send to SEC writes a lease object `sec-budget/leases/<machine>` with an
     expiry (e.g. 60 s), renewing it while it sends.
   - Its share is 8 ÷ the number of live leases.
   - A machine that cannot reach the bucket, or reads a lease it cannot parse, falls back to the
     declared share of option 1. That fallback is the safe floor, so the coordinator can only ever
     ADD speed.
   - To keep the sum ≤ 8 while machines join, a new machine starts at the floor and takes more
     only after one renewal period, by which time every other machine has seen its lease and cut
     its own share.
   - This gives a lone machine 8 a second again. It needs R2 credentials on every sender
     (including the runner) and one more network dependency on every SEC path, so it is the
     operator's call.
3. **Rejected: one egress machine.** Routing all SEC traffic through one Mac's process needs the
   machines networked together and that Mac always on.

**HOW VERIFIED.**
- **Reproduced first, then fixed.** `tests/test_sec_budget_across_machines.py` ran on `origin/main`
  `7c87164a` with 3 failed and 3 passed:
  - `test_two_machines_sending_at_once_stay_under_secs_ceiling_per_user`: "two machines sent 17
    in one second". These are real processes on a real clock, each with its own user cache.
    TeamNostra measured 16.47 a second, peak 16.
  - `test_a_redirect_hop_to_sec_takes_its_own_slot`: "peak 16 with redirects". TeamNostra measured
    16.
  - `test_every_machine_that_may_send_at_once_together_stays_under_secs_ceiling`: no
    `SEC_MACHINES` existed.

  After the fix all 6 pass.
- **The 3 that passed before are guards**, kept so the fix cannot over-reach:
  - a redirect still answers with the page it lands on, and a re-read is cached;
  - a hop off SEC takes no SEC slot;
  - a redirect loop fails loud, naming the URL.
- **The existing pins move to the share, unweakened.**
  - `tests/test_sec_pacing.py` asserted "at most 8 a second". It now asserts at most ceil(the
    share) = 3, which is tighter.
  - Its two-process test now requires the pair's minimum gap to be the share's interval (0.375 s,
    less 25 ms of jitter), where before it was 0.1 s.
  - Its control drops "peak > 8", which an independent 2.67-a-second pair can no longer reach. It
    keeps "minimum gap < the interval", which still shows that the check can see two unshared
    trains.
- **A real run at the new pacing**, on 2026-11-09, from this Mac:
  - six live `data.sec.gov/submissions/CIK….json` reads into a throwaway cache;
  - taking their turn from the machine's real pace file;
  - with the User-Agent from the primary's `.env`, which passes `sec_user_agent()`'s check (never
    printed).

  httpx's own request hook logged every request it sent: 6 requests and 0 redirect hops, gaps
  0.379–0.380 s, every body parsed.
- **The full offline suite** ran green before commit (`bin/commit`).

**BOUNDARY.**
- **17 and 16:** the most requests in any half-open one-second window over a mock transport, on
  this Mac, 2026-11-09, at `7c87164a`:
  - the 17 is from 2 processes × 24 requests, real clock;
  - the 16 is from 4 threads × 6 reads × 2 hops, virtual clock.
- **9:** arithmetic over the three declared machines (3 × ceil(8/3)), not a measurement. It counts
  a send at the moment it takes its slot. A send leaves some milliseconds later, and on a loaded
  machine that delay bunches sends. The full suite, run on this Mac at the same commit, measured
  **8** in one second from the two-machine test, whose slots allow 6. So the window figures are
  what the pacing permits, and SEC's limiter sees the wire.
- **0.379–0.380 s:** the 5 gaps between 6 live requests, 2026-11-09 on this Mac.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Every machine is three times slower on SEC: 2.67 a second where it had 8.** As arithmetic,
  not a measured run: 4,000 uncached requests take 25 minutes where they took 8.3. A page build
  touches one CIK "across ~13 reads" (`vinci/edgar/client.py`'s note), a few seconds. That is the
  price of the rule; the coordinator above is how to buy it back.
- **A fourth sender at once is outside the share**: a third machine, or two SEC workflows on two
  runners together. *Falsifier:* an SEC refusal (`SecRateLimitedError`) while no machine exceeds
  its share. Two workflows can be kept from overlapping with a workflow `concurrency:` group, which
  is not added here (group H's files).
- **If the operator never starts an SEC workflow while a Mac is working, `SEC_MACHINES = 2`
  (4 a second each) is also safe.** That is a one-line change, for the operator to rule.
- **Not changed here:**
  - efts' own 1-a-second pace (it is inside the share anyway);
  - `config.PacingConfig.sec_requests_per_sec`, a per-client interval that the share now
    overrides;
  - `validate_keys.py`'s unpaced, contactless request (RE1-D17, order 9).
- This narrows one acceptance in `docs/records/2026-10-29-sec-one-budget-per-machine.md`: "The
  2-a-second margin under SEC's 10 is the only allowance for them". Machines are now allowed for
  by the declared share, and the 2 a second is left for a browser or a notebook.
