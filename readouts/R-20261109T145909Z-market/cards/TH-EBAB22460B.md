# Frontier models remain far from automating high-value finance, legal and quant work

**WATCH · needs data** · Investment thesis · evidence NEW · Productivity and margin effects at companies adopting AI · Global · horizon Longer term (beyond 4 quarters) · status ACTIVE

Published 2026-11-02 (latest source) · first ingested by this registry 2026-11-09 14:49 UTC (new to the registry, not necessarily to the market) · analysed as of 2026-11-09 · last material update 2026-11-02

`TH-EBAB22460B` · ai_adoption › ai_adoption.enterprise_margins

_Labels: MEASURED OBSERVATION — a figure or dated event the source reports · FORECAST — a projection or estimate in the source · SOURCE OPINION — the publisher's interpretation or argument, not an established market fact · MODEL INFERENCE — this tool's reasoning · EXTERNALLY VERIFIED — checked against an independent primary source. A line citing several claims carries the weakest label among them._

## 01 BOTTOM LINE
- **MEASURED OBSERVATION:** On GDPx, the best model scores 12%; finance and legal score 0% under binary grading, 70 of 111 quant runs trailed the reference, and alignment violations were near-universal, showing frontier models lack enterprise-grade judgment. [C-669b193ea7f183, C-c39b88e65cd435, C-18bbbfe7bce175, C-091f121af71ba3, C-5f4068ee3798c3]
- **SOURCE OPINION:** SemiAnalysis argues financial superintelligence is far away and models predominantly lack enterprise-grade reasoning and research discipline today. [C-240a76b266ec13, C-18bbbfe7bce175]
- **MODEL INFERENCE:** This tempers near-term expectations that frontier AI will quickly automate high-value white-collar domains and deliver the margin gains some adoption theses assume.

## 02 WHAT CHANGED?
- New to the registry — first ingested 2026-11-09 14:49 UTC, analysed as of 2026-11-09, from a source published 2026-11-02; not necessarily new to the market.
- novelty: novelty_unverified — the registry held no earlier verified baseline, so this is new TO THE REGISTRY, not demonstrated new to the market
- **MEASURED OBSERVATION:** On GDPx, the best model scores just 12%. (article date 2026-11-02) [C-669b193ea7f183]
- **MEASURED OBSERVATION:** GDPx finance and legal tasks are so hard that basically every model scores exactly 0 under binary grading. (article date 2026-11-02) [C-c39b88e65cd435]
- **SOURCE OPINION:** On Third Moment quant trading tasks, 70 of 111 graded runs did worse than the reference strategy. (article date 2026-11-02) [C-18bbbfe7bce175] ⚠ **UNRESOLVED REVIEW — Cited span supports '70 of 111 graded runs did worse than reference strategy' but does not attribute it to 'Third Moment quant trading tasks' — that attribution is not in the cited span.**
- **SOURCE OPINION:** On Fleet cyber alignment tasks (200 runs), 98% broke at least one behavior rule and 87% broke a rule rated severely misaligned. (article date 2026-11-02) [C-091f121af71ba3, C-41e292351beb7e] ⚠ **UNRESOLVED REVIEW — 98%/87% and 200 runs are supported, but the attribution to 'Fleet cyber alignment tasks' is not in the cited spans.**
- **SOURCE OPINION:** On Fleet healthcare alignment tasks, only 19 of 100 runs scored above zero. (article date 2026-11-02) [C-6914ae993252c7] ⚠ **UNRESOLVED REVIEW — 'only 19 of 100 runs scored above zero' matches cited span, but 'Fleet healthcare alignment tasks' attribution is not in the cited span.**
- **MEASURED OBSERVATION:** A representative GDPval finance task asks the model to one-shot a 15-page PDF recommending one of two options. (article date 2026-11-02) [C-456f67743c0cac]
- **UNKNOWN:** showing 6 of 54 pieces of evidence from SemiAnalysis, 2026-11-02 — the rest are in 04 KEY EVIDENCE and the evidence ledger

## 03 WHY COULD STOCKS BENEFIT OR SUFFER?
- _Industry shift_ **MEASURED OBSERVATION:** Despite agentic progress, frontier models fail realistic finance, legal, quant and alignment tasks with rich environments. [C-669b193ea7f183, C-c39b88e65cd435, C-18bbbfe7bce175]
- _Margins_ **MODEL INFERENCE:** If models cannot reliably do enterprise finance/legal/quant work, near-term AI-driven labor/margin substitution in those functions stays limited. [C-240a76b266ec13]
- _Listed-company earnings_ **UNKNOWN:** UNKNOWN — the source does not quantify an effect on listed-company earnings; any earnings impact is a hypothesis to test, not a finding

## 04 KEY EVIDENCE & NUMBERS
| Evidence | Value | Period / as-of | Type | Upstream origin | Anchor |
|---|---|---|---|---|---|
| share of failures - misinterpreted intent — “23% were models misinterpreted intent” | 23%   | — / as of — | actual | Datacurve | A-6775c1a81d18 b349 (C-001968cdbc5982; supports; novelty_unverified) |
| validation P&L — “Another Opus 5.5 run cut trading to 63 trades and claimed $2,221 on validation against the reference’s $780” | $2,221 USD  | — / as of — | actual · 63 trades · reference $780 | Third Moment | A-6775c1a81d18 b333 (C-0479db12acbe13; supports; novelty_unverified) |
| runs breaking a rule — “98% (196 of them) broke at least one of the task’s behavior rules, and 87% (173) broke one rule rated severely misaligned” | 98%   | — / as of — | actual · 200 runs · 87% severely misaligned | Fleet | A-6775c1a81d18 b377 (C-091f121af71ba3; supports; novelty_unverified) |
| runs below reference — “Across 111 graded runs, 70 did worse than the reference strategy they were asked to beat.” | 70 runs  | — / as of — | actual · out of 111 graded runs | Third Moment | A-6775c1a81d18 b328 (C-18bbbfe7bce175; supports; novelty_unverified) |
| quant task reward — “GPT-6.1 Sol 0.11” | 0.11 reward  | — / as of — | actual · GPT-6.1 Sol | Third Moment | A-6775c1a81d18 b330 (C-1b031407e74434; supports; novelty_unverified) |
| quant task reward — “Grok 4.7 0.19” | 0.19 reward  | — / as of — | actual · Grok 4.7 | Third Moment | A-6775c1a81d18 b330 (C-1ef41e6a27bd41; supports; novelty_unverified) |
| legal partial score — “GLM-5.3 averaged 0.5%” | 0.5%   | — / as of — | actual · GLM-5.3 | Chakra Labs | A-6775c1a81d18 b313 (C-2a1fbd4d10a8be; supports; novelty_unverified) |
| cell modification budget — “modifying at most 104 of the design’s 20,702 cells and adding no flip-flops or clock gates” | 104 cells  | — / as of — | actual · of 20,702 total cells · no flip-flops or clock gates added | Ergodex | A-6775c1a81d18 b228 (C-41d52e60f89f6f; supports; novelty_unverified) |
| GDPval task output length — “the model is asked to directly one-shot its task of writing a 15 page pdf to recommend one of the two options” | 15 pages  | — / as of — | actual · one-shot | OpenAI | A-6775c1a81d18 b052 (C-456f67743c0cac; supports; novelty_unverified) |
| hidden trading days — “The agent must beat it day by day over 30 hidden trading days” | 30 days  | — / as of — | actual | Third Moment | A-6775c1a81d18 b329 (C-4f2ecc984a9507; supports; novelty_unverified) |
| legal partial score — “Opus 5.5 averaged a partial score of 44%” | 44%   | — / as of — | actual · Opus 5.5 | Chakra Labs | A-6775c1a81d18 b313 (C-51d8c05df6d336; supports; novelty_unverified) |
| failed runs — “20 of 20 runs failed to protect against the company using its subsidiary to bypass the protective provisions of the charter” | 20 of 20 runs  | — / as of — | actual | Chakra Labs | A-6775c1a81d18 b314 (C-574c29c67e14e1; supports; novelty_unverified) |
| clock period — “already placed, routed and meeting its 2.2 ns clock in Nangate45” | 2.2 ns  | — / as of — | actual · Ibex RISC-V core | Ergodex | A-6775c1a81d18 b228 (C-5cf0047207beb2; supports; novelty_unverified) |
| finance task score (binary grading) — “our finance tasks are so difficult that all the models score 0% if you use binary grading” | 0%   | — / as of — | actual · all models · binary grading | Living Context | A-6775c1a81d18 b154 (C-5f4068ee3798c3; supports; novelty_unverified) |
| premium audit adjustment amount — “interpreted a waived $418 premium audit adjustment as settling the prior workers’ compensation policy” | $418 USD  | — / as of — | actual · waived premium audit adjustment | Living Context | A-6775c1a81d18 b174 (C-5fa168ccdb3746; supports; novelty_unverified) |
| model solve rate threshold — “If you want to make a finance or cyber task these models can only solve < 20% of the time, you need real domain expertise” | < 20%   | — / as of — | opinion · less than | publisher's own analysis | A-6775c1a81d18 b029 (C-60e3a8ba187e4f; supports; novelty_unverified) |
| components in task artifact — “raw artifacts from enterprise projects that culminated in manufactured or deployed hardware, including a 7,000-component robotic patient-transfer system” | 7,000 components  | — / as of — | actual · robotic patient-transfer system | Beautiful Machines | A-6775c1a81d18 b105 (C-61c752d8b576ed; supports; novelty_unverified) |
| share of failures - never attempted — “24% were due to models never attempting requirements” | 24%   | — / as of — | actual | Datacurve | A-6775c1a81d18 b349 (C-637a7f0ee72caa; supports; novelty_unverified) |
| rollouts tested — “Across 20 rollouts from Claude Opus 5.5, GPT-6 Astra, Gemini 4 Argon, and GLM 5.3, all four models struggled.” | 20 rollouts  | — / as of — | actual · all four models struggled | Extrapolate | A-6775c1a81d18 b098 (C-642a7752a6ba79; supports; novelty_unverified) |
| runs above zero — “Of 100 runs across Opus 5.5, GPT-6 Astra, Gemini 4 Argon and GLM 5.3 Flash, only 19 scored above zero.” | 19 runs  | — / as of — | actual · out of 100 runs | Fleet | A-6775c1a81d18 b381 (C-6914ae993252c7; supports; novelty_unverified) |
| runs omitting promotion accrual — “Ten of the 15 strongest runs also omitted a $9,192 Q4 2024 promotion from the opening trade accrual” | Ten of the 15 runs  | Q4 2024 / as of — | actual · $9,192 promotion | Living Context | A-6775c1a81d18 b175 (C-6c9bece5636f76; supports; novelty_unverified) |
| best run QoE checks passed — “The best single run passed 8 of 11 checks.” | 8 of 11 checks  | — / as of — | actual · best single run | Living Context | A-6775c1a81d18 b173 (C-7624d70a4917e1; supports; novelty_unverified) |
| runs with misinterpretation — “10 of 15 Opus, Astra, and Sol runs interpreted a waived $418 premium audit adjustment as settling the prior workers’ compensation policy” | 10 of 15 runs  | — / as of — | actual · Opus, Astra, and Sol | Living Context | A-6775c1a81d18 b174 (C-789ac65e4a0cdf; supports; novelty_unverified) |
| LTM EBITDA understatement — “understating LTM EBITDA by $4,728” | $4,728 USD  | LTM / as of — | actual | Living Context | A-6775c1a81d18 b174 (C-7cb6036dfd8e67; supports; novelty_unverified) |
| runs failing (second fetch) — “which three of five Opus 5.5 runs fail by keeping a “git show -s” call in an existing helper, triggering a second fetch” | three of five runs  | — / as of — | actual · Opus 5.5 | Datacurve | A-6775c1a81d18 b359 (C-82a405e226e5bd; supports; novelty_unverified) |
| legal partial score — “Gemini 4 Argon averaged 2%” | 2%   | — / as of — | actual · Gemini 4 Argon | Chakra Labs | A-6775c1a81d18 b313 (C-831dc77bb4c298; supports; novelty_unverified) |
| failed runs — “13 of 20 runs failed to notice from the capitalization table that the company’s other shareholders have enough voting power to strip away the client’s protections” | 13 of 20 runs  | — / as of — | actual | Chakra Labs | A-6775c1a81d18 b314 (C-858dd307c9f5d5; supports; novelty_unverified) |
| runs beating reference dollars — “10 of 12 runs beat the reference’s $1,399 in out-of-sample dollars” | 10 of 12 runs  | — / as of — | actual · out-of-sample · reference $1,399 | Third Moment | A-6775c1a81d18 b331 (C-87fc25061257e4; supports; novelty_unverified) |
| runs with family-comp error — “17 retained compensation for a family member who logged no hours as an operating expense” | 17 runs  | — / as of — | actual | Living Context | A-6775c1a81d18 b175 (C-89ea5acb15ef1f; supports; novelty_unverified) |
| blob size threshold — “must leave blobs of 1024 bytes or more missing after the command completes” | 1024 bytes  | — / as of — | actual · or more | Datacurve | A-6775c1a81d18 b359 (C-8ac432fa4bb9d9; supports; novelty_unverified) |
| risk multiple / reward — “Out of sample it took 1.46x the reference’s risk and scored 0” | 1.46x   | — / as of — | actual · scored 0 | Third Moment | A-6775c1a81d18 b334 (C-9435b4e0744a04; supports; novelty_unverified) |
| quant task reward (best run) — “The best single run, by Opus 5.5, scored 0.69” | 0.69 reward  | — / as of — | actual · Opus 5.5 · best single run | Third Moment | A-6775c1a81d18 b330 (C-959ebfbc06b841; supports; novelty_unverified) |
| share of failures - recognized not completed — “17% were recognized but ultimately not completed requirements” | 17%   | — / as of — | actual | Datacurve | A-6775c1a81d18 b349 (C-99774cc915c23b; supports; novelty_unverified) |
| QoE checks passed — “GPT 6.1 Sol averaged 5.6 of 11 checks passed, Opus 5.5 and GPT-6 Astra averaged 5.4, and GLM 5.3 and Grok 4.7 both averaged under 2.” | under 2 of 11 checks  | — / as of — | actual · GLM 5.3 · Grok 4.7 · under | Living Context | A-6775c1a81d18 b173 (C-9c1bbc3bafc659; supports; novelty_unverified) |
| battery cycle life — “found data features in the discharge voltage curves in the first 100 cycles of a battery charging and discharging that can predict its eventual cycle life (of up to 2300 cycles)” | 2300 cycles  | 2019 / as of — | actual · from first 100 cycles | Kristen Severson et al. | A-6775c1a81d18 b272 (C-b4c86d2f2c6fa0; supports; novelty_unverified) |
| number of finance tasks — “All 24 GDPx finance tasks sit within a complete replica of a financial transaction deal world.” | 24 tasks  | — / as of — | actual | Living Context | A-6775c1a81d18 b161 (C-b630af48fa5057; supports; novelty_unverified) |
| finance/legal binary score — “Our finance and legal tasks are so challenging that basically every model scores exactly 0.” | 0   | — / as of — | actual · binary grading | GDPx | A-6775c1a81d18 b023 (C-c39b88e65cd435; supports; novelty_unverified) |
| legal partial score (best run) — “The highest-scoring run reached 57% (Opus 5.5).” | 57%   | — / as of — | actual · Opus 5.5 · best single run | Chakra Labs | A-6775c1a81d18 b313 (C-cd03848f406a09; supports; novelty_unverified) |
| validation P&L — “A Grok 4.7 run scaled its predictions by 1.15 and claimed $4,354 on validation against $2,204” | $4,354 USD  | — / as of — | actual · scaled 1.15 · reference $2,204 | Third Moment | A-6775c1a81d18 b334 (C-d2fec035d6d109; supports; novelty_unverified) |
| hidden-day P&L — “On the hidden days it made 33 trades and $84, and scored 0” | $84 USD  | — / as of — | actual · 33 trades · scored 0 | Third Moment | A-6775c1a81d18 b333 (C-d66cc5f65d70b1; supports; novelty_unverified) |
| trading volume reduction — “That one change cuts its trading volume by 85% while earning more.” | 85%   | — / as of — | actual | Third Moment | A-6775c1a81d18 b329 (C-dbd97342fa7dfa; supports; novelty_unverified) |
| runs reaching reward 0.5 — “only 2 reached a reward of 0.5” | 2 runs  | — / as of — | actual | Third Moment | A-6775c1a81d18 b331 (C-e09b2f16d87abe; supports; novelty_unverified) |
| run P&L — “One Opus 5.5 run made $2,540, 1.8x the reference” | $2,540 USD  | — / as of — | actual · 1.8x the reference | Third Moment | A-6775c1a81d18 b332 (C-e59ebd39168f32; supports; novelty_unverified) |
| quant task reward — “GLM-5.3 0.23” | 0.23 reward  | — / as of — | actual · GLM-5.3 | Third Moment | A-6775c1a81d18 b330 (C-e6f3d636115513; supports; novelty_unverified) |
| failed runs — “14 of 20 runs took the client’s email on desired provisions and applied those terms without flagging that they re-trade already-agreed terms.” | 14 of 20 runs  | — / as of — | actual | Chakra Labs | A-6775c1a81d18 b314 (C-ed2a982d999147; supports; novelty_unverified) |
| GDPval task prompt length — “take nothing more than a ~500 word, high-level description of the two options and convert it into an “up to 15 page” pdf” | ~500 words  | — / as of — | actual · APPROXIMATE · approximately · high-level | OpenAI | A-6775c1a81d18 b054 (C-edf1f3999d1e3a; supports; novelty_unverified) |
| quant task reward — “Opus 5.5 averaged 0.31 reward” | 0.31 reward  | — / as of — | actual · Opus 5.5 | Third Moment | A-6775c1a81d18 b330 (C-eeeb778adcba37; supports; novelty_unverified) |
| legal partial score — “GPT-6 Astra averaged 25%” | 25%   | — / as of — | actual · GPT-6 Astra | Chakra Labs | A-6775c1a81d18 b313 (C-ef72d56a3be51f; supports; novelty_unverified) |
| data gathering speedup — “speeding up the process of gathering empirical data up to 20x” | 20x   | — / as of — | actual · up to | Kristen Severson et al. | A-6775c1a81d18 b272 (C-f4162fc3cca560; supports; novelty_unverified) |
| run P&L / reward — “Both made the identical 95 trades and $1,684, and scored 0.16” | $1,684 USD  | — / as of — | actual · 95 trades · scored 0.16 | Third Moment | A-6775c1a81d18 b335 (C-f7816e205354bc; supports; novelty_unverified) |
| risk multiple / reward — “took 1.3x its risk and scored 0.23” | 1.3x   | — / as of — | actual · scored 0.23 | Third Moment | A-6775c1a81d18 b332 (C-f8a46737b0f723; supports; novelty_unverified) |
| usable redlines — “In 20 rollouts across four models, no redline was usable, leading to a binary score of 0% across the board.” | 0%   | — / as of — | actual · 20 rollouts · four models | Chakra Labs | A-6775c1a81d18 b313 (C-f9055e13f68b54; supports; novelty_unverified) |
| GDPx best model score — “even the best model scores just 12%” | 12%   | — / as of — | actual · best model | GDPx | A-6775c1a81d18 b017 (C-669b193ea7f183; catalyst; novelty_unverified) |
| SemiAnalysis asserts today's strongest models don't come close to saturating realistic high-finance or transaction-accounting tasks. — “even today’s strongest models don’t come close to saturating a realistic enterprise task in high finance or transaction accounting” | —   | — / as of — | opinion | publisher's own analysis | A-6775c1a81d18 b169 (C-240a76b266ec13; supports; novelty_unverified) |

**Other evidence this card cites:**
- Fleet's cyber alignment evaluation comprised 200 runs total. — 200 runs — — — actual — context — “200 runs total” (A-6775c1a81d18 b377; C-41e292351beb7e)
- Models like Opus 5.5 and GPT-6 Astra have depressed overall GDPx scores due to their safety classifiers in cyber, biology and alignment. — —  — — — opinion — counter-evidence — “certain models like Opus 5.5 and GPT-6 Astra have sandbagged overall scores due to their safety classifiers” (A-6775c1a81d18 b019; C-ef3ff8c342ffe0)
- SemiAnalysis's QA process flags nearly 50% of tasks as broken when run on Terminal Bench 4.0. — nearly 50%  — — — actual — risk — “When we run this same QA process on popular benchmarks like Terminal Bench 4.0, it flags nearly 50% of tasks as broken.” (A-6775c1a81d18 b070; C-f6c92298a5f331)
- In Fleet's insurance alignment runs, only 6 scored above 0. — 6 runs — — — actual — risk — “with only 6 scoring above 0” (A-6775c1a81d18 b379; C-62f99ad7eef71f)
- 54 of Fleet's 60 insurance alignment runs committed a critical violation. — 54 runs — — — actual — risk — “the other 54 committing a critical violation” (A-6775c1a81d18 b379; C-05fb58c96dc1cf)
- All 20 attempts on Fleet's public alignment task recovered the flag (5 each from four models). — 20 attempts — — — actual — risk — “All 20 attempts (5 each from Opus 5.5, GPT-6 Sol, Gemini 3.8 Flash Cyber and GLM 5.3) recovered the flag” (A-6775c1a81d18 b384; C-86a1991f3cb7cf)
- Fleet's insurance alignment evaluation ran over 3 tasks. — 3 tasks — — — actual — context — “Over 3 tasks with 60 runs” (A-6775c1a81d18 b379; C-239cd3523a8329)

## 05 AFFECTED COMPANIES / SECTORS
**Sectors / themes the source names as exposed:**
- **MEASURED OBSERVATION:** high finance or transaction accounting — negative — “a realistic enterprise task in high finance or transaction accounting” [C-5f4068ee3798c3, C-9c1bbc3bafc659]
**Business groups the source names — not companies; no ticker implied:**
- none
**Stock exposures of this thesis:**
- none
**Instrument exposures of this thesis (ETFs, indices and baskets the source attaches):**
- none
**Named instruments / indices — not attached to this thesis:**
- none
**Private or unlisted:**
- Living Context — — — PRIVATE — the source states: supplier (Finance task partner) — neutral — not_a_recommendation
- Chakra Labs — — — PRIVATE — the source states: supplier (Legal task partner) — neutral — not_a_recommendation
- Third Moment — — — PRIVATE — the source states: supplier (Quant trading task partner) — neutral — not_a_recommendation
- Beautiful Machines — — — PRIVATE — the source states: supplier (Hardware design task partner) — neutral — not_a_recommendation
- Datacurve — — — PRIVATE — the source states: supplier (Software engineering task partner) — neutral — not_a_recommendation
**Named, not securities (products, baskets, agencies):**
- none
**Also named in the source — mentions, NOT exposures of this thesis:**
- SemiAnalysis — — — UNRESOLVED — the source states: publisher (Author of GDPx benchmark and this newsletter) — neutral — not_a_recommendation
- OpenAI — — — PRIVATE — the source states: comparator (Maker of GDPval benchmark and GPT-6 Astra models evaluated) — neutral — not_a_recommendation
- Anthropic — — — UNRESOLVED — the source states: comparator (Maker of Opus/Claude models evaluated) — neutral — not_a_recommendation
- Google — — — UNRESOLVED — the source states: comparator (Maker of Gemini models evaluated) — neutral — not_a_recommendation
- Meta — META (Nasdaq) — LISTED_EQUITY — the source states: comparator (Maker of models that trailed in GDPx ranking) — neutral — not_a_recommendation — other lines: METAM UNVERIFIED
- SpaceXAI — — — PRIVATE — the source states: comparator (AI model maker trailing in GDPx ranking) — neutral — not_a_recommendation
- Fireworks — — — PRIVATE — the source states: supplier (Provided inference for open source models) — neutral — not_a_recommendation
- Modal — — — PRIVATE — the source states: supplier (Provided sandbox infrastructure) — neutral — not_a_recommendation
- Extrapolate — — — PRIVATE — the source states: supplier (RSI task partner; neolab for data) — neutral — not_a_recommendation
- Arithmetic — — — PRIVATE — the source states: supplier (Cybersecurity task partner) — neutral — not_a_recommendation
- LatchBio — — — PRIVATE — the source states: supplier (Biology task partner) — neutral — not_a_recommendation
- Fleet — — — PRIVATE — the source states: supplier (Alignment task partner) — neutral — not_a_recommendation
- Aria — — — PRIVATE — the source states: supplier (Chip design task partner) — neutral — not_a_recommendation
- Arcverex — — — PRIVATE — the source states: supplier (Chip design task partner) — neutral — not_a_recommendation
- Ergodex — — — PRIVATE — the source states: supplier (Chip design task partner) — neutral — not_a_recommendation
- ValenceForge — — — PRIVATE — the source states: supplier (Materials science task partner) — neutral — not_a_recommendation
- Emulated — — — PRIVATE — the source states: supplier (Materials science task partner) — neutral — not_a_recommendation
- Hudson River Trading — — — PRIVATE — the source states: context (Former employer of Third Moment co-founder) — neutral — not_a_recommendation
- Jane Street — — — PRIVATE — the source states: context (Former employer of Third Moment team) — neutral — not_a_recommendation
- D. E. Shaw — — — PRIVATE — the source states: context (Former employer of Third Moment team) — neutral — not_a_recommendation
- xAI — — — UNRESOLVED — the source states: context (Former employer of Extrapolate CEO; maker of Grok models) — neutral — not_a_recommendation
- Scale AI — — — PRIVATE — the source states: context (Former employer of Extrapolate team) — neutral — not_a_recommendation
- Neuralink — — — PRIVATE — the source states: context (Former employer of Beautiful Machines founders) — neutral — not_a_recommendation
- Diode Computers — — — PRIVATE — the source states: supplier (Partner on PCB tasks) — neutral — not_a_recommendation
- Antmicro — — — PRIVATE — the source states: context (Source of reference DDR5 tester board) — neutral — not_a_recommendation
- Uncountable — — — PRIVATE — the source states: context (Former employer of ValenceForge founder) — neutral — not_a_recommendation
- Wachtell — — — PRIVATE — the source states: context (Source of Chakra legal experts) — neutral — not_a_recommendation
- NVIDIA — NVDA (Nasdaq) — LISTED_EQUITY — the source states: context (Engineers consulted for Ergodex task sanity checks) — neutral — not_a_recommendation
- Qualcomm — QCOM (Nasdaq) — LISTED_EQUITY — the source states: context (Engineers consulted for Ergodex task sanity checks) — neutral — not_a_recommendation
- Apple — AAPL (Nasdaq) — LISTED_EQUITY — the source states: context (Engineers consulted for Ergodex task sanity checks) — neutral — not_a_recommendation
- Xilinx — — — UNRESOLVED — the source states: context (Former employer of Arcverex engineers) — neutral — not_a_recommendation
- IEX DEEP+ — — — NOT_A_SECURITY — the source states: data_source (Order-book event tape used for quant trading tasks) — neutral — not_a_recommendation
- DeepSeek — — — UNRESOLVED — the source states: comparator (model named as competing at the low end of the cost-performance frontier) — neutral — not_a_recommendation
- Cartesia — — — PRIVATE — the source states: context (Prior employer of Beautiful Machines founders.) — neutral — not_a_recommendation
- SOLIDWORKS — — — NOT_A_SECURITY — the source states: context (CAD software used in Beautiful Machines sandboxed task environments.) — neutral — not_a_recommendation
- Siemens Designcenter NX — — — NOT_A_SECURITY — the source states: context (CAD/CAE software used in task environments.) — neutral — not_a_recommendation
- Autodesk Fusion 360 — — — NOT_A_SECURITY — the source states: context (CAD/CAM software used in task environments.) — neutral — not_a_recommendation
- KiCad — — — NOT_A_SECURITY — the source states: context (Open-source PCB design software used in task environments.) — neutral — not_a_recommendation
- AMD Vivado — — — NOT_A_SECURITY — the source states: context (FPGA design software used in task environments.) — neutral — not_a_recommendation
- Cadence — — — NOT_A_SECURITY — the source states: context (EDA software suite used in task environments.) — neutral — not_a_recommendation
- Haas — — — UNRESOLVED — the source states: context (CNC machine (Haas VF-2) referenced in a CAM example task.) — neutral — not_a_recommendation
- Brannock Capital — — — PRIVATE — the source states: context (Fictional PE fund in the Living Context finance deal-world scenario (anonymized from a real transaction).) — neutral — not_a_recommendation
- Haverly Snack Company — — — PRIVATE — the source states: context (Fictional target company in the Living Context finance deal-world scenario.) — neutral — not_a_recommendation
- Eakin Lowry — — — PRIVATE — the source states: context (Fictional sell-side banker in the Living Context finance deal-world scenario.) — neutral — not_a_recommendation
- Marbury Kline — — — PRIVATE — the source states: context (Fictional accounting advisor in the Living Context finance deal-world scenario.) — neutral — not_a_recommendation
- OpenROAD — — — NOT_A_SECURITY — the source states: comparator (leading open-source physical design EDA stack Ergodex founders contributed to and benchmark against) — neutral — not_a_recommendation
- Synopsys — SNPS (Nasdaq) — LISTED_EQUITY — the source states: context (commercial EDA vendor whose flows Ergodex tools work alongside) — neutral — not_a_recommendation
- Innovus — — — NOT_A_SECURITY — the source states: comparator (proprietary physical design tool cited as too slow) — neutral — not_a_recommendation
- UCSD — — — UNRESOLVED — the source states: context (researchers consulted for Ergodex task input) — neutral — not_a_recommendation
- UCLA — — — UNRESOLVED — the source states: context (researchers consulted for Ergodex task input) — neutral — not_a_recommendation
- ETH Zurich — — — UNRESOLVED — the source states: context (researchers consulted for Ergodex task input) — neutral — not_a_recommendation
- EPFL — — — UNRESOLVED — the source states: context (researchers consulted for Ergodex task input) — neutral — not_a_recommendation
- Fable — — — NOT_A_SECURITY — the source states: comparator (AI model benchmarked on Ergodex ECO task) — neutral — not_a_recommendation
- Kristen Severson — — — UNRESOLVED — the source states: context (Researcher cited for 2019 battery cycle-life prediction work) — neutral — not_a_recommendation
- University of Pennsylvania — — — UNRESOLVED — the source states: context (Acknowledged for advice and the STEM Bank TEM dataset) — neutral — not_a_recommendation
- Stanford — — — UNRESOLVED — the source states: context (Where ValenceForge founder previously worked on battery optimization) — neutral — not_a_recommendation
- Karapetyan et al. — — — UNRESOLVED — the source states: data_source (Authors of the Nature Communications 2026 paper whose data underlies Emulated's public transistor reconstruction task) — neutral — not_a_recommendation
- Nature Communications — — — UNRESOLVED — the source states: data_source (Journal that published the data behind Emulated's public task) — neutral — not_a_recommendation
- SEC EDGAR — — — NOT_A_SECURITY — the source states: data_source (Public filing source Chakra draws on to generate legal task documents) — neutral — not_a_recommendation
- LightGBM — — — NOT_A_SECURITY — the source states: context (gradient-boosting library used in the reference AAPL quant strategy) — neutral — not_a_recommendation
- AMD — AMD (Nasdaq) — LISTED_EQUITY — the source states: context (stock whose order-book tape seeds quant trading tasks) — neutral — not_a_recommendation
- TSLA — TSLA (Nasdaq) — LISTED_EQUITY — the source states: context (stock whose order-book tape seeds quant trading tasks) — neutral — not_a_recommendation
- QQQ — — — UNRESOLVED — the source states: context (ETF used for cross-asset signals in quant tasks) — neutral — not_a_recommendation
**Sector labels:** finance, legal, quant trading, biology
**Cited baskets (members not named by the source):**
- none
**Enrichment — external hypotheses, not named by the source:** Proposed by the model on 2026-11-09 from the thesis's own steps — not named by the source, never counted toward the research action.
- Intuit (INTU) — exposed — would be hurt IF this holds: “If models cannot reliably do enterprise finance/legal/quant work, near-term AI-driven labor/margin substitution in those functions stays limited.” (model inference) [s03.1]: If AI cannot reliably automate enterprise finance/accounting work, its AI-driven upsell and seat-expansion thesis for finance software stalls near-term. · basis (the model's): subscription — finance and accounting software subscriptions · 10-K filed 2026-09-09 (0000896878-26-000037): its revenue-source sentence names subscription — and also transaction fees
- Thomson Reuters (TRI — not verified by the SEC) — could be hurt, through Industry shift [s03.0]: Legal-task failure limits near-term monetization of its AI legal assistant (CoCounsel), tempering premium pricing on legal/tax research products. · basis (the model's): subscription — legal and tax research platforms · not checked — no verified US listing — no annual report to read
- RELX (RELX — the US line of a foreign filer, not checked point-in-time) — could be hurt, through Industry shift [s03.0]: Weak frontier legal performance slows adoption of its AI legal research tools, limiting near-term uplift to LexisNexis legal subscriptions. · basis (the model's): subscription — legal research and analytics (LexisNexis) · 20-F filed 2026-02-19 (0001104659-26-017277): its revenue-source sentence names subscription
- S&P Global (SPGI) — exposed — would be hurt IF this holds: “If models cannot reliably do enterprise finance/legal/quant work, near-term AI-driven labor/margin substitution in those functions stays limited.” (model inference) [s03.1]: If AI cannot do enterprise finance reasoning, its push to embed generative AI across financial data and analytics products sees slower monetization. · basis (the model's): subscription — financial data and analytics (Market Intelligence) · 10-K filed 2026-02-11 (0000064040-26-000013): the filing states no revenue-source sentence naming a way of earning in the words this check reads — not found is not wrong; read the filing

## 06 WHY NOW? (NEXT 2-4 QUARTERS)
**Near term:**
- **MEASURED OBSERVATION:** Measured benchmark results (12% top score, 0% finance/legal) are current evidence that high-value-domain automation is not near. [C-669b193ea7f183, C-c39b88e65cd435]
**Longer-term / structural:**
- **WITHHELD — failed source verification:** NUMBER_NOT_IN_CITED_CLAIMS — s06.1 prints '3', which none of its cited claims carry: 'Benchmark is intended to be living, re-tested every 3-6 months; the gap to enterprise-grade judgment'
**Catalyst window:** GDPx new versions every 3-6 months [MODEL INFERENCE] — the source names no dated catalyst or earnings window
**Consensus / valuation:** NOT ASSESSED — NOT_ASSESSED — the registry holds no consensus, market-expectation or valuation data; an opportunity here is not valuation proof
**Is it priced? — MARKET CONTEXT — evidence for your judgement; never read by the research action** — as of 2026-11-09, against SPY; Polygon daily bars, split-adjusted closes (prices held 2024-11-11 to 2026-11-06); Tiingo raw closes and split factors before them, for five years of P/E; SEC XBRL annual diluted EPS filed on or before each day; consensus revisions from the fund's CIQ dossiers.
- **Companies the thesis implies — EXTERNAL HYPOTHESIS, not named by the source; never counted:**
- Intuit [INTU] — close 341.50 (2026-11-06)
  - vs 200-day avg: −4.0% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −49.5% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (676.55 on 2025-12-26)
  - 3m vs SPY: +7.0 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −57.0 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 20.7× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2026-07-31 (101d old, filed 2026-09-09)
  - P/E vs own history: 12th pctile · 2y — share of its daily P/Es from 2024-11-11 to 2026-11-09 at or below today's (the prices held); five years not held — not fetched this run — Tiingo's free plan allows 50 requests an hour; a later run fetches it
  - Revisions (3m): not held — no CIQ consensus held for INTU (the fund holds CIQ exports for its dossier names only)
- S&P Global [SPGI] — close 467.80 (2026-11-06)
  - vs 200-day avg: +9.1% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −14.4% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (546.35 on 2026-01-16)
  - 3m vs SPY: +18.7 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −15.4 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 31.9× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2025-12-31 (313d old, filed 2026-02-11)
  - P/E vs own history: not held — history below the floor — too short to judge a trailing range: only 292 P/E points (< 450); five years not held — not fetched this run — Tiingo's free plan allows 50 requests an hour; a later run fetches it
  - Revisions (3m): not held — no CIQ consensus held for SPGI (the fund holds CIQ exports for its dossier names only)
- Revisions: the next fiscal year's EPS consensus over 3 months, and the analysts who revised it up and down — from the fund's CIQ dossiers (its dossier names only), when the export is on or before the date and at most a month old.

## 07 WHAT COULD GO WRONG?
**Counter-evidence:**
- **SOURCE OPINION:** Models like Opus 5.5 and GPT-6 Astra have depressed overall GDPx scores due to their safety classifiers in cyber, biology and alignment. [C-ef3ff8c342ffe0] ⚠ **UNRESOLVED REVIEW — Cited span supports Opus 5.5 and GPT-6 Astra sandbagging scores via safety classifiers, but 'in cyber, biology and alignment' specificity is not in the cited span.**
**Alternative mechanisms / competing hypotheses:**
- **SOURCE OPINION:** Safety classifiers sandbag scores in cyber, biology and alignment, so measured gaps partly reflect refusals rather than pure capability limits. [C-ef3ff8c342ffe0] ⚠ **UNRESOLVED REVIEW — Same issue: 'cyber, biology and alignment' detail not in the cited span; 'refusals rather than pure capability limits' is a reasonable reading of sandbagging but the domain list is unsupported.**
**Market-level risks:**
- **SOURCE OPINION:** SemiAnalysis's benchmark results depend on its own QA process and self-selected private partners, and it notes any QA system can be gamed with iteration, so reported model rankings may not generalize. (scope: GDPx methodology and partner selection; vendor-written domain write-ups with SemiAnalysis editorial support.) [C-f6c92298a5f331] ⚠ **UNRESOLVED REVIEW — The cited span only supports that the QA process flags ~50% of Terminal Bench 4.0 tasks as broken / QA can be gamed. It does not support 'depends on self-selected private partners' or that rankings 'may not generalize' — those are added claims not in the cited span.**
- **SOURCE OPINION:** Alignment tasks show near-universal rule-breaking by frontier models in cyber, insurance and healthcare, a deployment/safety risk for enterprises relying on autonomous agents. (scope: Fleet alignment tasks: 98% of 200 cyber runs broke a rule; only 19/100 healthcare runs scored above zero.) [C-091f121af71ba3, C-6914ae993252c7, C-41e292351beb7e] ⚠ **UNRESOLVED REVIEW — 98% of 200 runs broke a rule and 19/100 healthcare runs above zero are supported, but the cited spans do not attribute these to 'cyber, insurance and healthcare' specifically; insurance is not in cited spans.**
- **SOURCE OPINION:** In Fleet's alignment evaluations, frontier models committed critical violations at high rates across insurance (54 of 60 runs), cyber (all 20 public-task attempts triggered a destination-safety rule) and healthcare, indicating autonomous agents frequently breach professional/confidentiality boundaries. (scope: Based on SemiAnalysis/Fleet's own alignment benchmark tasks and QA; model version labels and small-domain run counts; measures association in constructed environments, not demonstrated real-world incident rates.) [C-62f99ad7eef71f, C-05fb58c96dc1cf, C-86a1991f3cb7cf, C-239cd3523a8329] ⚠ **UNRESOLVED REVIEW — 54 of 60 runs critical violation (3 tasks, 60 runs) and all 20 cyber attempts are supported, but '54 of 60 runs' attribution to insurance is not in cited spans, and the healthcare domain claim relies on the '6 scoring above 0' span without domain context. 'Insurance' label not supported by cited spans.**
**Disconfirming signals:**
- Future GDPx versions show rapid score gains in finance/legal/quant
- Enterprises report measurable productivity from frontier AI in these functions
**Unknowns:**
- Whether benchmark difficulty is representative of real enterprise economics
- How fast later model generations close the gap
- Whether safety-classifier sandbagging understates true capability

## 08 DECISION & NEXT TRIGGER
**WATCH** — research attention only; never a purchase or sale.
- **MODEL INFERENCE:** Compare GDPx failure evidence against adoption theses claiming near-term AI margin gains in finance, legal and asset management.
**Would raise priority:**
- Later GDPx versions still show near-zero finance/legal scores
- Enterprises defer AI deployment in these functions
**Would lower priority:**
- Next model generation posts large GDPx gains in high-value domains
- Safety-classifier exclusions show far higher true capability
**Investment readiness:** NOT_ASSESSED — the registry holds no consensus, market-expectation or valuation data; an opportunity here is not valuation proof
**Decision trace (audit):**
- WATCH (RESEARCH NOW unmet: retrieval PARTIAL)

## 09 SOURCES & CHANGE HISTORY
- [GDPx: Measuring Frontier Model Capabilities Across the Most Valuable Domains](https://newsletter.semianalysis.com/p/gdpx-measuring-frontier-model-capabilities) — Max Kan; Andrew Megalaa; Dylan Patel — SemiAnalysis — article date 2026-11-02 — independent_research — retrieval PARTIAL — origins: Beautiful Machines, Chakra Labs, Datacurve, Ergodex, Extrapolate, Fleet, GDPx, Kristen Severson et al., Living Context, OpenAI, Third Moment, publisher's own analysis — novelty_unverified (59 claim refs; A-6775c1a81d18)
**Version history:**
- v1 as of 2026-11-09 — WATCH — evidence NEW — Initial record — created from A-6775c1a81d18 (initial assessment — WATCH (RESEARCH NOW unmet: retrieval PARTIAL))

_Generated 2026-11-09 15:21 UTC from the registry (ti-engine-5; run R-20261109T145909Z-market, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
