# Trainium3's native PyTorch training stack broadens adoption, aiding AWS custom silicon

**WATCH · needs data** · Investment thesis · evidence MIXED · AI accelerators, GPUs, custom silicon and their direct supply chain · Global · horizon Next 2-4 quarters · status ACTIVE

Published 2026-11-05 (latest source) · first ingested by this registry 2026-10-30 12:13 UTC (new to the registry, not necessarily to the market) · analysed as of 2026-11-09 · last material update 2026-11-05

`TH-F2CD2F7AFC` · ai_infrastructure › ai_infrastructure.compute_semis

_Labels: MEASURED OBSERVATION — a figure or dated event the source reports · FORECAST — a projection or estimate in the source · SOURCE OPINION — the publisher's interpretation or argument, not an established market fact · MODEL INFERENCE — this tool's reasoning · EXTERNALLY VERIFIED — checked against an independent primary source. A line citing several claims carries the weakest label among them._

## 01 BOTTOM LINE
- **SOURCE OPINION:** Amazon has made a major course correction toward a first-class native PyTorch (TorchNeuron) experience on Trainium3, which the publisher's hands-on testing found promising (23.89%/30.47% MFU on Qwen3-32B, 93% FlexAttention pass rate, SOTA profiler), though still far from CUDA maturity. [C-2beeceb16d5c88, C-c03e1c527e8256, C-90d00b1ee88cfb, C-9c90bd72c762ab, C-8f717dcb83688c, C-c3c6925ad0e59f, C-f41ae4588179e6, C-0d63959e780679, C-a0502962445309, C-7a13343dc2f9ec] ⚠ **UNRESOLVED REVIEW — The cited spans support MFU figures, 93% FlexAttention pass rate, SOTA profiler, and 'nowhere close to CUDA maturity.' But '30.47% MFU on Qwen3-32B' and '93% FlexAttention pass rate' — the 93% span (89/96 test cases) is not tied to FlexAttention in its cited span; FlexAttention pass rate is not explicitly supported by cited spans. The MFU figures come from Qwen3-32B training per cited span C-a0502962445309, so that part holds.**
- **SOURCE OPINION:** The publisher believes the software course correction will meaningfully broaden Trainium3 adoption into training. [C-2beeceb16d5c88]
- **SOURCE OPINION:** ⟨update 2026-11-05 · SemiAnalysis⟩ SemiAnalysis's own AgentX benchmarks show TPUv7 Ironwood delivering competitive or superior tokens-per-dollar versus NVIDIA GB300/B200/B300 and AMD MI355X on FP8 across four models, winning external TPU inference customers (Oracle, OpenAI, Anthropic, Meta). [C-0ebc2279393608, C-4910e57ae3f8d9, C-93f1ce7c6016ba, C-64f6a11955d6bc, C-b9a5aee91ee3da, C-c6395aa93f3913, C-d317fa8617b762, C-40eb14789d5ab5, C-bb10099d468bb8] ⚠ **UNRESOLVED REVIEW — The cited spans support the tokens-per-dollar comparisons and the Oracle/OpenAI/Anthropic/Meta customers, but 'across four models' and 'winning external TPU inference customers' are not clearly tied to the customer span. The label MEASURED OBSERVATION is acceptable as the weakest among cited figures.**

## 02 WHAT CHANGED?
- v2 held 39 claim(s); this source adds: contradictory ×6, new ×27
- novelty: assessed against the registry's prior version — classes are relative to what the thesis already held, not to market knowledge
- [New supporting evidence — not a confirmation] **FORECAST:** TPUv8 with native FP4 support is expected in Q1 2027. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05; period Q1 2027) [C-328a06d9320182]
- [New supporting evidence — not a confirmation] **MEASURED OBSERVATION:** Qwen3.5 397B was the first model Google submitted to AgentX, two weeks before this article ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05; period two weeks ago) [C-f4a22cd685a861]
- [New supporting evidence — not a confirmation] **MEASURED OBSERVATION:** Oracle, OpenAI, Anthropic and Meta have all become customers of Google TPUs. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-bb10099d468bb8]
- [New supporting evidence — not a confirmation] **SOURCE OPINION:** In FP8 on Qwen 3.5 397B single-turn, TPUv7 Ironwood delivered up to 50% better performance per dollar than B200 and B300. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-0ebc2279393608, C-7d400bfcc93a1a, C-049146e4b952f9] ⚠ **UNRESOLVED REVIEW — The cited C-0ebc2279393608 supports 'up to 50% better performance per dollar than B200 and B300.' But the 'FP8 on Qwen 3.5 397B single-turn' scoping is only loosely supported by C-049146e4b952f9 (Qwen3.5 397B FP8). The label SOURCE OPINION is weakest cited and fine.**
- [New supporting evidence — not a confirmation] **SOURCE OPINION:** On GLM-5.2 vLLM AgentX FP8, TPUv7 delivers 1.2x to 2.7x the tokens per dollar of B200, B300 and MI355X from 60 to 300 tok/s/user. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-4910e57ae3f8d9] ⚠ **UNRESOLVED REVIEW — The tokens-per-dollar range and tok/s/user range match C-4910e57ae3f8d9, but that span does not mention 'GLM-5.2' model scope; the model attribution is unsupported by the cited span.**
- [New supporting evidence — not a confirmation] **MEASURED OBSERVATION:** On Qwen3.5 vLLM AgentX FP8 with llm-d, TPUv7 beats GB300 FP8 at every interactivity level and restores parity against GB300 FP4 at higher quality. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-93f1ce7c6016ba]
- [New supporting evidence — not a confirmation] **MEASURED OBSERVATION:** On Kimi K3 vLLM AgentX, TPUv7 is competitive with GB300 NVL72 at launch and delivers 1.15x to 2.5x the tokens per dollar of GB200, B200, B300 and MI355X. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-64f6a11955d6bc]
- [New supporting evidence — not a confirmation] **MEASURED OBSERVATION:** NVIDIA's first GB300 FP4 counter submission is still 1.64x worse per dollar than TPUv7 FP8 for external customers across most of the curve. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-b9a5aee91ee3da]
- [New supporting evidence — not a confirmation] **MEASURED OBSERVATION:** On GLM-5.2 FP8, TPUv7 delivers 4.4x the tokens per dollar of H200 at 150 tok/s/user. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-c6395aa93f3913]
- [New supporting evidence — not a confirmation] **SOURCE OPINION:** On Qwen3.5 397B AgentX, TPUv7 FP8 vLLM is 1.67x better perf per dollar than FP4 GB300 NVL72. ⟨new evidence from an origin already counted — not an independent confirmation⟩ (article date 2026-11-05) [C-d317fa8617b762, C-049146e4b952f9]
- **UNKNOWN:** showing 10 of 33 pieces of evidence from SemiAnalysis, 2026-11-05 — the rest are in 04 KEY EVIDENCE and the evidence ledger

## 03 WHY COULD STOCKS BENEFIT OR SUFFER?
- _Industry shift_ **SOURCE OPINION:** AWS moves Trainium to a first-class native PyTorch training experience, lowering the switching cost from CUDA for researchers. [C-e41f831681da1c, C-2beeceb16d5c88, C-f5d72399c08d5c]
- _Volumes_ **FORECAST:** Arm server CPU shipments grow faster than x86, lifting Arm share above 20% in 2026 and ~30% in 2027 ⟨cited figures: forecast; approximate⟩ [C-ae101db5717c0b, C-0aa530b9902c5f, C-1022b1afa327c5]
- _Listed-company earnings_ **MODEL INFERENCE:** Higher Trainium training adoption would improve AWS custom-silicon economics vs buying Nvidia GPUs; article gives no earnings figure.

## 04 KEY EVIDENCE & NUMBERS
| Evidence | Value | Period / as-of | Type | Upstream origin | Anchor |
|---|---|---|---|---|---|
| The global ML community trusts vLLM/SGLang as the default day-0 inference engine for open-source models. — “No matter the open source model, on day 0, the global ML community trusts vLLM/SGLang as the go-to engine for inference.” | 0   | day 0 / as of — | opinion | publisher's own analysis | A-9fadab568080 b037 (C-2598a5f20f1186; supports; novelty_unverified) |
| model size — “we tested its gpt-oss 20B training recipe” | 20B parameters  | — / as of — | actual · worked out of the box | publisher's own analysis | A-9fadab568080 b044 (C-6047f9ce36e043; supports; novelty_unverified) |
| DMA engines per physical core — “using the 16 DMA engines per physical core” | 16 DMA engines  | — / as of — | actual · per physical core | publisher's own analysis | A-9fadab568080 b084 (C-8243f3c0bb19d0; supports; novelty_unverified) |
| FlexAttention pass rate — “Trainium3 passed 89 out of 96 test cases, a 93% pass rate.” | 93%   | — / as of — | actual | publisher's own analysis | A-9fadab568080 b053 (C-8f717dcb83688c; supports; novelty_unverified) |
| MFU (eager) — “We measured 11,099 tokens per second in average training throughput on eager mode, at 23.89% MFU” | 23.89%   | — / as of — | actual · eager mode | publisher's own analysis | A-9fadab568080 b043 (C-90d00b1ee88cfb; supports; novelty_unverified) |
| training throughput (compiled) — “For compiled mode, we saw 14,156 tokens per second and 30.47% MFU, a 1.28x throughput improvement over eager mode.” | 14,156 tokens per second  | — / as of — | actual · compiled mode | publisher's own analysis | A-9fadab568080 b043 (C-9c90bd72c762ab; supports; novelty_unverified) |
| training throughput (eager) — “We measured 11,099 tokens per second in average training throughput on eager mode, at 23.89% MFU” | 11,099 tokens per second  | — / as of — | actual · eager mode | publisher's own analysis | A-9fadab568080 b043 (C-c03e1c527e8256; supports; novelty_unverified) |
| models in test corpus — “AWS collected a giant list of top 100k+ Hugging Face models” | 100k+ models  | — / as of — | actual · APPROXIMATE · 100k+ · Hugging Face models | publisher's own analysis | A-9fadab568080 b060 (C-c43041301a37f3; supports; novelty_unverified) |
| Alibaba is introducing new Yitian 720/730 server CPUs, cited as a 2027 Arm-based growth driver. — “Alibaba’s introduction of new Yitian 720/730 CPUs” | 720/730   | 2027 / as of — | forecast | publisher's own analysis | A-a7f0f66d2b3b b012 (C-2656679f1e097f; supports; new) |
| Arm server CPU market share — “Arm-based processors, meanwhile, had only recently surpassed 10% of the market” | 10%   | 2025 / as of — | actual · recently surpassed | publisher's own analysis | A-a7f0f66d2b3b b008 (C-5f8fcaed366329; supports; new) |
| Arm server CPU market share — “pushing their share of the server CPU market above 20%” | above 20%   | 2026 / as of — | forecast · above | publisher's own analysis | A-a7f0f66d2b3b b011 (C-ae101db5717c0b; supports; new) |
| performance per dollar advantage — “TPUv7 Ironwood) delivered up to 50% better performance per dollar than B200 and B300” | up to 50%   | — / as of — | actual · up to · single-turn · FP8 · Qwen 3.5 397B | publisher's own analysis | A-866829df2ed0 b003 (C-0ebc2279393608; supports; new) |
| context length — “The model supports a 1M-token context through DeepSeek Sparse Attention” | 1M tokens  | — / as of — | actual · DeepSeek Sparse Attention | not attributed by the source | A-866829df2ed0 b038 (C-1daf45184596c3; supports; new) |
| relative throughput — “At FP8, TPUv7 with llm-d beats GB300 at every interactivity, from >2x at high throughput to achieving more than 1000tok/s/user in the ultrafast region” | >2x   | — / as of — | actual · FP8 · llm-d · high throughput | publisher's own analysis | A-866829df2ed0 b068 (C-40eb14789d5ab5; supports; new) |
| tokens per dollar ratio — “TPUv7 still delivers a competitive 1.15x to 2.5x the tokens per dollar of GB200, B200 and B300” | 1.15x to 2.5x   | — / as of — | actual · vs GB200, B200, B300 | publisher's own analysis | A-866829df2ed0 b084 (C-46272d439ca14b; supports; new) |
| tokens per dollar ratio — “TPUv7 is the cheapest FP8 option, delivering 1.2x to 2.7x the tokens per dollar of B200, B300, and MI355X from 60 to 300 tok/s/user” | 1.2x to 2.7x   | — / as of — | actual · FP8 · 60 to 300 tok/s/user · vs B200/B300/MI355X | publisher's own analysis | A-866829df2ed0 b010 (C-4910e57ae3f8d9; supports; new) |
| model parameters — “Muse Spark Open is Meta’s latest 816B-parameter open model” | 816B parameters  | — / as of — | actual | Meta | A-866829df2ed0 b028 (C-945cca5da38542; supports; new) |
| On Google's internal cost basis, TPUv7 beat GB300 at 100 and 200 tok/s/user for Kimi K3 — “On Google’s internal cost it beat GB300 at 100 and 200 tok/s/user.” | 100 tok/s/user  | — / as of — | actual · Google internal cost basis | publisher's own analysis | A-866829df2ed0 b083 (C-94ba7a7ca28ad1; supports; new) |
| performance per dollar ratio — “their first GB300 FP4 counter submission is still 1.64x worse per dollar than TPUv7 FP8 for external customers across most of the curve” | 1.64x   | — / as of — | actual · worse per dollar · external customers · across most of the curve | publisher's own analysis | A-866829df2ed0 b018 (C-b9a5aee91ee3da; supports; new) |
| tokens per dollar ratio — “it delivers 1.2x to 2.7x the tokens per dollar of B200, B300, and MI355X at FP8 , and 4.4x that of H200 at 150 tok/s/user” | 4.4x   | — / as of — | actual · vs H200 · 150 tok/s/user · FP8 | publisher's own analysis | A-866829df2ed0 b039 (C-c6395aa93f3913; supports; new) |
| systolic array padded — “64 head dim, which means that for long-context attention, 25% of the systolic array is padded” | 25%   | — / as of — | actual · long-context attention | publisher's own analysis | A-866829df2ed0 b030 (C-c76cb54a24b837; supports; new) |
| performance per dollar ratio — “it is 1.67x better perf per dollar than even FP4 GB300 NVL72” | 1.67x   | — / as of — | actual · TPUv7 FP8 vs GB300 NVL72 FP4 | publisher's own analysis | A-866829df2ed0 b052 (C-d317fa8617b762; supports; new) |
| megakernel speedup — “AMD reports that it cuts a decode step from about 2,459 launches to 210 and runs 2.31x faster at batch 1” | 2.31x   | — / as of — | actual · APPROXIMATE · batch 1 · eight MI350X GPUs · 2,459 to 210 launches | AMD | A-866829df2ed0 b077 (C-e1505a74d93178; supports; new) |
| time-to-first-step reduction — “targeting up to a 2 orders of magnitude reduction in time-to-first-step for both eager and compiled modes, with minimal or no performance regression” | 2 orders of magnitude   | — / as of — | forecast · targeting · up to | publisher's own analysis | A-9fadab568080 b047 (C-3e3ab62fd92fc1; catalyst; novelty_unverified) |
| Arm server CPU market share — “TrendForce expects Arm-based CPUs to capture approximately 30% of the server CPU market in 2027” | approximately 30%   | 2027 / as of — | forecast · APPROXIMATE · approximately | publisher's own analysis | A-a7f0f66d2b3b b012 (C-0aa530b9902c5f; catalyst; new) |
| Qwen3.5 397B was the first model Google submitted to AgentX, two weeks before this article — “Two weeks ago, Qwen3.5 397B became the first model Google submitted to AgentX.” | Two weeks   | two weeks ago / as of — | actual · first model Google submitted to AgentX | publisher's own analysis | A-866829df2ed0 b052 (C-f4a22cd685a861; catalyst; new) |
| AWS pass rates are not yet 100% but are climbing rapidly with agent swarms fixing remaining failures, and its internal summary shows gaps transparently. — “AWS is climbing rapidly, with agent swarms systematically fixing the remaining failures” | —   | — / as of — | opinion · pass rates not at 100% yet | publisher's own analysis | A-9fadab568080 b061 (C-2121bbf831157a; supports; novelty_unverified) |
| Anthropic's head of performance publicly said performance analysis on Trainium is better than on Nvidia GPUs. — “Anthropic’s head of performance (who is ex-Jane and Finch Street) has publicly said that performance analysis on Trainium is way better than performance analysis on Nvidia GPUs” | —   | — / as of — | opinion | Tristan Hume on Twitter | A-9fadab568080 b065 (C-2ba269efa6eecd; supports; novelty_unverified) |
| The publisher believes Amazon's software course correction will meaningfully broaden Trainium3 adoption. — “Amazon has made a major course correction to its software strategy, and we believe it will meaningfully broaden Trainium3 adoption.” | —   | — / as of — | opinion | publisher's own analysis | A-9fadab568080 b027 (C-2beeceb16d5c88; supports; novelty_unverified) |
| MatMul MFU vs GB300 — “Trainium3 achieved a visibly higher MFU than GB300, starting from the mid-range, where the matrix multiplication performs 1 GFLOP of computation.” | —  GB300 | — / as of — | actual | publisher's own analysis | A-9fadab568080 b050 (C-69874c12e5194e; supports; novelty_unverified) |
| Trainium is investing in the vLLM/SGLang community with hardware access and early SGLang support on native PyTorch. — “Trainium rapidly invest in the vLLM/SGLang community with hardware access and early access to Trainium on SGLang built on native PyTorch (TorchNeuron)” | —   | — / as of — | actual | publisher's own analysis | A-9fadab568080 b038 (C-7a13343dc2f9ec; supports; novelty_unverified) |
| MatMul performance range — “It was only after 100 GFLOP that GB300 and B200 started outperforming Trainium3, and Trainium3 won again after 1 TFLOP.” | —  GB300 and B200 | — / as of — | actual | publisher's own analysis | A-9fadab568080 b050 (C-b794dd6acb3e8e; supports; novelty_unverified) |
| The publisher judges Trainium's profiler to be industry-leading and state of the art. — “Trainium’s profiler is by far leading the industry and is SOTA status.” | —   | — / as of — | opinion | publisher's own analysis | A-9fadab568080 b064 (C-c3c6925ad0e59f; supports; novelty_unverified) |
| Custom attention variants on Trainium3 matched the numerics of Nvidia GPUs. — “we tried implementing custom attention variants not in the FlexAttention benchmark suite for Trainium3, and it matched the numerics of Nvidia GPUs” | —   | — / as of — | actual | publisher's own analysis | A-9fadab568080 b054 (C-cb22de28c7009a; supports; novelty_unverified) |
| AWS hired the lead of Google's native Torch-on-TPU effort to work on native Torch for Trainium. — “AWS has even hired the lead of Google’s native Torch on TPU effort to work on native Torch for Trainium.” | —   | — / as of — | actual | publisher's own analysis | A-9fadab568080 b027 (C-d14265b996b7fb; supports; novelty_unverified) |
| AWS Neuron team is shifting Trainium to a first-class native PyTorch training experience. — “The AWS Neuron team is aggressively working to change this pitfall with the biggest shift being moving towards a first-class, native PyTorch training experience.” | —   | — / as of — | actual | publisher's own analysis | A-9fadab568080 b002 (C-e41f831681da1c; supports; novelty_unverified) |
| Porting from GPU requires essentially only replacing .to('cuda') with .to('neuron'), with most PyTorch ATen operators working out of the box. — “the only change needed is replacing .to(”cuda”) with .to(”neuron”), and in theory the vast majority of the PyTorch ATen operators will work decently well out of the box” | —   | — / as of — | opinion · in theory · vast majority of operators | publisher's own analysis | A-9fadab568080 b031 (C-f5d72399c08d5c; supports; novelty_unverified) |
| Google Axion CPUs in high-volume shipment; Microsoft Cobalt 100 and Arm AGI processors in mass production/shipment — “Google’s in-house Axion CPUs have entered high-volume shipments, and Microsoft’s Cobalt 100 and Arm’s internally developed AGI processors have also entered mass production and shipment” | —   | 2026 / as of — | actual | publisher's own analysis | A-a7f0f66d2b3b b011 (C-865ff34f1cba43; supports; new) |
| Long-context, multi-turn agentic serving is where inference spend is heading, which is why customers want AgentX results — “long-context, multi-turn agentic serving is where inference spend is heading” | —   | — / as of — | opinion | publisher's own analysis | A-866829df2ed0 b004 (C-09420e825af25c; supports; new) |
| The Kimi K3 TPU result was built by the vLLM ecosystem (Inferact, founded by vLLM's creators) with Google, open source on vLLM TorchTPU — “This result came from the vLLM ecosystem, not from Google alone. Inferact, founded by vLLM’s creators and maintainers, built the K3 megakernels with Google” | —   | — / as of — | actual · open source · vLLM ecosystem | publisher's own analysis | A-866829df2ed0 b088 (C-21f5cb0bcf0e4a; supports; new) |
| Current and potential TPU customers are asking Google for AgentX results because the benchmark closely matches their real inference workloads — “current TPU customers are asking Google for AgentX results because of how realistic the AgentX benchmark is and how similar it is to their real inference workload” | —   | — / as of — | opinion | publisher's own analysis | A-866829df2ed0 b014 (C-3c099e0b84d9ec; supports; new) |
| Meta is an early TPU adopter already deploying TPUv7 in production using SGLang-TorchTPU. — “Meta is one of the early adopters of TPU and is already deploying TPUv7 in production using SGLang-TorchTPU” | —   | — / as of — | actual | publisher's own analysis | A-866829df2ed0 b026 (C-81bf6db529c583; supports; new) |
| NVIDIA is now slower moving than AMD, Google and Amazon on external suggestions, git commits and feedback. — “Nvidia is now slower moving than AMD, Google, and Amazon to external suggestion, git commits, and feedback” | —   | — / as of — | opinion | publisher's own analysis | A-866829df2ed0 b020 (C-8690214eaae524; supports; new) |
| relative performance — “With llm-d disaggregated serving, TPUv7 beats GB300 FP8 at every interactivity level and restores parity even against GB300 FP4 at higher quality / accuracy” | —   | — / as of — | actual · FP8 · llm-d disaggregated serving | publisher's own analysis | A-866829df2ed0 b011 (C-93f1ce7c6016ba; supports; new) |
| Oracle, OpenAI, Anthropic and Meta have all become customers of Google TPUs. — “Oracle, OpenAI , Anthropic, and Meta all becoming customers of TPUs” | —   | — / as of — | actual | publisher's own analysis | A-866829df2ed0 b001 (C-bb10099d468bb8; supports; new) |
| NVIDIA's FP4 counter submission beats TPUv7 FP8 on decode but overtuned at expense of prefill, so TPUv7 FP8 still beats GB300 NVL72 FP4 on end-to-end performance — “they overtuned decode at the expense of prefill, hurting overall end-to-end performance. Thus, on end-to-end performance, TPUs FP8 is currently still beating GB300 NVL72 FP4” | —   | — / as of — | opinion · end-to-end performance | publisher's own analysis | A-866829df2ed0 b063 (C-c58183a4c223ef; supports; new) |
| Major hyperscalers/AI labs use Qwen3.5 397B and scaled versions as proxy models for hardware purchasing and capacity planning decisions — “certain major hyperscalers/AI lab use Qwen3.5 397B and multi trillion parameter scale up version based on Qwen3.5 397B architecture as proxy models when making hardware purchasing and capacity planning decisions” | —   | — / as of — | opinion · proxy models · hardware purchasing and capacity planning | publisher's own analysis | A-866829df2ed0 b054 (C-d51cacb1d57836; supports; new) |
| AMD is giving upstream OSS maintainers liberal cluster access and rapidly increasing its CI fleet with minimal bureaucracy — “AMD has been increasingly less stingy and providing the upstream vLLM, TileRT, SGLang, Tokenspeed, etc. maintainers liberal access to clusters and rapdily increasing the CI fleet without miminal levels of bureaucracy” | —   | — / as of — | opinion | publisher's own analysis | A-866829df2ed0 b023 (C-e4d701dff884b7; supports; new) |
| Arm server CPU growth in 2027 driven primarily by ramp-up in NVIDIA Vera CPU shipments — “Growth will be driven primarily by a substantial ramp-up in NVIDIA Vera CPU shipments” | —   | 2027 / as of — | forecast | publisher's own analysis | A-a7f0f66d2b3b b012 (C-1022b1afa327c5; catalyst; new) |
| AMD's server CPU market share expected to increase further with new product launches in 1H 2027 — “AMD's market share is expected to increase further as the company plans to launch new products in the first half of 2027” | —   | 1H 2027 / as of — | forecast | publisher's own analysis | A-a7f0f66d2b3b b013 (C-98c8f03b45a9ca; catalyst; new) |
| TPUv8 with native FP4 support is expected in Q1 2027. — “we will need to wait until Q1 2027 for TPUv8 with FP4 support” | —   | Q1 2027 / as of — | forecast · TPUv7 has no native FP4 support | publisher's own analysis | A-866829df2ed0 b041 (C-328a06d9320182; catalyst; new) |

**Other evidence this card cites:**
- The Trainium stack is nowhere near CUDA ecosystem maturity, but heading in the right direction. — —  — — — opinion — counter-evidence — “It’s nowhere close to the maturity of the CUDA ecosystem, but the direction is right.” (A-9fadab568080 b003; C-f41ae4588179e6)
- Compiled-mode MFU measured at 30.47%. — 30.47%  — — — actual — context — “For compiled mode, we saw 14,156 tokens per second and 30.47% MFU, a 1.28x throughput improvement over eager mode.” (A-9fadab568080 b043; C-0d63959e780679)
- The publisher trained Qwen3-32B on 16 Trainium2 chips and tried a rack-scale Trainium3 UltraServer with 64 physical chips. — —  — — — actual — context — “we trained a Qwen3-32B on 16 Trainium2 chips, 64 LNC=2 logical cores in total, and we also tried doing it on a rack-scale Trainium3 UltraServer with 64 physical chips.” (A-9fadab568080 b040; C-a0502962445309)
- On Kimi K3 vLLM AgentX, TPUv7 is competitive with GB300 NVL72 at launch and delivers 1.15x to 2.5x the tokens per dollar of GB200, B200, B300 and MI355X. — 1.15x to 2.5x  — — — actual — supports — “Competitive with GB300 NVL72 at launch; With TPUv7 delivering 1.15x to 2.5x the tokens per dollar of GB200, B200, B300, and MI355X” (A-866829df2ed0 b012; C-64f6a11955d6bc)
- On GLM-5.3 at 100 tok/s/user, GB300 FP4 delivers 3.6x the tokens per dollar of TPUv7. — 3.6x  — — — actual — counter-evidence — “At 100 tok/s/user, GB300 and GB200 FP4 deliver 3.6x and 3.5x the tokens per dollar of TPUv7” (A-866829df2ed0 b041; C-7d400bfcc93a1a)
- TPUv7 FP8 could beat GB300 NVL72 FP4 on the Qwen3.5 397B model — 397B parameters — — — opinion — context — “Qwen3.5 397B FP8 showing that even TPUv7 FP8 could beat GB300 NVL72 FP4” (A-866829df2ed0 b018; C-049146e4b952f9)
- x86 segment accounted for nearly 90% of server CPU market in 2025 — nearly 90%  — 2025 — actual — counter-evidence — “The x86 segment, led by Intel and AMD, accounted for nearly 90% of the server CPU market in 2025” (A-a7f0f66d2b3b b008; C-040ac638d8dbbf)
- gpt-oss training run had compilation time of 27 minutes 17 seconds. — 27 minutes and 17 seconds time — — — actual — counter-evidence — “For gpt-oss, this training run came at a ridiculously high compilation time of 27 minutes and 17 seconds” (A-9fadab568080 b046; C-ead98710d7a634)
- Trainium Torch will not support TorchAO MXFP8 at launch, prioritizing BF16 training first. — 0  — day 0 — actual — counter-evidence — “Trainium Torch will not support TorchAO MXFP8 on day 0 until they have made the BF16 training experience great” (A-9fadab568080 b033; C-61e0ae0df73695)
- MoE combine and dispatch operations account for 60-70% of communication volume in MoE training/inference. — 60-70%  — — — actual — counter-evidence — “MoE combine and MoE dispatch are among the most important comms ops and take anywhere from 60-70% of the communication volume” (A-9fadab568080 b045; C-3709dfeba3a7e2)
- All 7 failed FlexAttention cases on Trainium3 occurred at large batch/sequence length and were due to compilation timeouts, not numerical errors. — 7 cases — — — actual — counter-evidence — “All 7 failed cases were at large batch size (4) and sequence length (8192), and all failed due to compilation exceeding the time budget rather than numerical errors” (A-9fadab568080 b053; C-d7fb27d367ba02)
- It took over 9 months of pushing AMD leadership to get engineers enough stable nodes to reach 93% parity on gating test groups. — 9 months — — — actual — counter-evidence — “which took over 9 months of fighting with AMD senior leadership, was getting their engineers enough stable nodes to achieve 93% parity on gating test groups” (A-9fadab568080 b057; C-47cf21c7bf0774)
- At one unnamed hardware vendor, CI numbers shown to leadership were 99.99% while actual gating parity was below 5%. — 99.99%  — — — actual — counter-evidence — “by the time CI numbers reached senior leadership, they showed 99.99%, while the actual gating parity pass rate at the time was below 5%” (A-9fadab568080 b062; C-42218bf8c5f870)
- Trainium does not yet support PyTorch's TokenSwitch MoE API; AWS has committed to collaborate with Meta's PyTorch team to add support. — —  — — — actual — counter-evidence — “the AWS team has committed to collaborating with the Meta PyTorch team to modify the TokenSwitch ABC such that it can support Trainium too” (A-9fadab568080 b045; C-60b12eb4e73294)
- AMD's server CPU market share estimated to increase to approximately 27% in 2026 — approximately 27%  — 2026 — forecast — counter-evidence — “TrendForce estimates that the company’s share of the server CPU market will increase significantly to approximately 27% in 2026” (A-a7f0f66d2b3b b010; C-6c2c4ac5a74a70)
- NVIDIA NVFP4 still beats TPUv7 FP8 on GLM-5.2, but with accuracy/quality loss. — —  — — — actual — counter-evidence — “NVIDIA NVFP4 still beats TPUv7 FP8, but with accuracy / quality loss” (A-866829df2ed0 b010; C-25c082eebb3cd6)
- On GLM-5.3 at 100 tok/s/user, GB200 FP4 delivers 3.5x the tokens per dollar of TPUv7. — 3.5x  — — — actual — counter-evidence — “At 100 tok/s/user, GB300 and GB200 FP4 deliver 3.6x and 3.5x the tokens per dollar of TPUv7” (A-866829df2ed0 b041; C-b54c975a0db1ce)
- After four NVIDIA refreshes, GB300 FP4 now leads TPUv7 by 1.5x to 2.6x on Kimi K3. — 1.5x to 2.6x  — — — actual — counter-evidence — “GB300 FP4 now leads by 1.5x to 2.6x after four NVIDIA refreshes” (A-866829df2ed0 b084; C-4d9a6581f5a9b8)
- VR200 delivers 4.3x to 5.6x the tokens per dollar of TPUv7 on Kimi K3. — 4.3x to 5.6x  — — — actual — counter-evidence — “VR200 delivers 4.3x to 5.6x TPUv7” (A-866829df2ed0 b084; C-ca979b9d2149b4)
- In a comparison SemiAnalysis calls unfair, Rubin NVL72 is up to 6x better perf per dollar than TPUv7. — up to 6x  — — — actual — counter-evidence — “between TPUv7 & Rubin NVL72, Rubin is up to 6x better perf per dollar” (A-866829df2ed0 b085; C-974463c6db4ad5)
- Bureaucracy is one of the biggest risks to NVIDIA's moat per SemiAnalysis. — —  — — — opinion — risk — “This is one of the biggest risks to NVIDIA Moat that Jensen has to tackle” (A-866829df2ed0 b020; C-cf964f66949928)
- Rubin's InferenceX results remain preview submissions not independently reproduced. — —  — — — actual — risk — “Rubin’s results remain preview submissions” (A-866829df2ed0 b086; C-7bf6aaf2c1e36e)

## 05 AFFECTED COMPANIES / SECTORS
**Sectors / themes the source names as exposed:**
- **FORECAST:** Arm-based processors — positive — “Arm-based processors, meanwhile, had only recently surpassed 10% of the market” [C-5f8fcaed366329, C-ae101db5717c0b, C-0aa530b9902c5f]
- **MEASURED OBSERVATION:** x86 segment — negative — “The x86 segment, led by Intel and AMD” [C-040ac638d8dbbf]
- **MEASURED OBSERVATION:** TPU — positive — “Google is selling TPUs to external customers” [C-bb10099d468bb8, C-0ebc2279393608]
**Business groups the source names — not companies; no ticker implied:**
- hyperscalers — Furthermore, certain major hyperscalers/AI lab use Qwen3.5 397B and multi trillion… (paragraph 54) [C-d51cacb1d57836]
- Not checkable on this machine — the text of 28 paragraph(s) holding this thesis's evidence is not held here (an exported registry carries no article text), so business groups the source names there cannot be read.
**Stock exposures of this thesis:**
- Amazon — AMZN (Nasdaq) — LISTED_EQUITY — the source states: potential_beneficiary (Owner of AWS/Trainium; subject of the article's positive software-progress thesis) — this thesis reads it as potential beneficiary [SOURCE OPINION] — positive — not_a_recommendation
- AWS — — — UNRESOLVED — the source states: potential_beneficiary (Amazon cloud unit developing Trainium and the Neuron/TorchNeuron stack) — this thesis reads it as potential beneficiary [SOURCE OPINION] — positive — not_a_recommendation
- Arm — — — UNRESOLVED — the source states: potential_beneficiary (Arm architecture provider and in-house AGI processor developer) — this thesis reads it as potential beneficiary [SOURCE OPINION] — positive — not_a_recommendation
- Google — — — UNRESOLVED — the source states: potential_beneficiary (Deploys in-house Arm-based Axion server CPUs) — this thesis reads it as potential beneficiary [SOURCE OPINION] — positive — not_a_recommendation
- Microsoft — MSFT (Nasdaq) — LISTED_EQUITY — the source states: potential_beneficiary (Deploys in-house Arm-based Cobalt 100 server CPUs) — this thesis reads it as potential beneficiary [SOURCE OPINION] — positive — not_a_recommendation — other lines: MSFT VERIFIED; MSFT VERIFIED
- Alibaba — — — UNRESOLVED — the source states: potential_beneficiary (Introducing new Yitian 720/730 Arm-based server CPUs) — this thesis reads it as potential beneficiary [SOURCE OPINION] — positive — not_a_recommendation
- Intel — INTC (Nasdaq) — LISTED_EQUITY — the source states: potentially_harmed (x86 server CPU supplier facing shipment delays and declining market share) — this thesis reads it as potentially harmed [SOURCE OPINION] — negative — not_a_recommendation
- Meta — META (Nasdaq) — LISTED_EQUITY — the source states: spending_customer (TPU customer deploying TPUv7 in production; maker of Muse Spark Open model and PyTorch) — this thesis reads it as spending customer [SOURCE OPINION] — neutral — not_a_recommendation — other lines: METAM UNVERIFIED
- Oracle — ORCL (NYSE) — LISTED_EQUITY — the source states: spending_customer (Named as TPU external customer) — this thesis reads it as spending customer [SOURCE OPINION] — neutral — not_a_recommendation — other lines: ORCL PRD VERIFIED
**Instrument exposures of this thesis (ETFs, indices and baskets the source attaches):**
- none
**Named instruments / indices — not attached to this thesis:**
- none
**Private or unlisted:**
- Anthropic — — — PRIVATE — the source states: spending_customer (Key Trainium customer running production inference and RL; its performance team praises the profiler) — positive — not_a_recommendation
**Named, not securities (products, baskets, agencies):**
- vLLM — — — NOT_A_SECURITY — the source states: context (Open-source inference engine ecosystem Trainium is investing in) — neutral — not_a_recommendation
- SGLang — — — NOT_A_SECURITY — the source states: context (Open-source inference engine ecosystem Trainium is investing in) — neutral — not_a_recommendation
- TorchTitan — — — NOT_A_SECURITY — the source states: context (Open-source PyTorch pre-training framework Trainium supports) — neutral — not_a_recommendation
- QuACK — — — NOT_A_SECURITY — the source states: comparator (Nvidia-based intra-kernel profiler used as a comparator to Neuron Explorer) — neutral — not_a_recommendation
- VR200 — — — NOT_A_SECURITY — the source states: comparator (NVIDIA next-gen accelerator used as a perf-per-dollar comparator against TPUv7) — neutral — not_a_recommendation
**Also named in the source — mentions, NOT exposures of this thesis:**
- Nvidia — NVDA (Nasdaq) — LISTED_EQUITY — the source states: comparator (Incumbent GPU/CUDA competitor against which Trainium is benchmarked (GB300, B200, profiler)) — negative — not_a_recommendation
- AMD — AMD (Nasdaq) — LISTED_EQUITY — the source states: comparator (GPU competitor cited for weaker profiler and historical CI/parity struggles) — negative — not_a_recommendation
- Tristan Hume — — — UNRESOLVED — the source states: context (Anthropic head of performance cited as a source praising the Trainium profiler) — neutral — not_a_recommendation
- Hugging Face — — — PRIVATE — the source states: context (Provider of PyTorch ecosystem libraries now supported on Trainium Torch) — neutral — not_a_recommendation
- SemiAnalysis — — — UNRESOLVED — the source states: publisher (Author/publisher conducting the hands-on testing) — neutral — not_a_recommendation
- PyTorch — — — NOT_A_SECURITY — the source states: context (ML framework (Meta) at the center of Trainium's software course correction) — neutral — not_a_recommendation
- Inferact/RadixArk — — — PRIVATE — the source states: context (Partner that helped bring TPUs into vLLM/SGLang ecosystem) — neutral — not_a_recommendation
- Codex — — — NOT_A_SECURITY — the source states: context (Coding assistant used to set up Trainium profiling) — neutral — not_a_recommendation
- Claude — — — NOT_A_SECURITY — the source states: context (Anthropic's model, initially refused to write Trainium kernels) — neutral — not_a_recommendation
- Twitter — — — UNRESOLVED — the source states: data_source (platform cited as source of Tristan Hume's public statement) — neutral — not_a_recommendation
- TrendForce — — — UNRESOLVED — the source states: publisher (Author and research firm producing the forecasts) — neutral — not_a_recommendation
- OpenAI — — — PRIVATE — the source states: potential_beneficiary (Named as introducing new Arm-based server processors in 2027) — positive — not_a_recommendation
- Huawei — — — UNRESOLVED — the source states: potential_beneficiary (Named as introducing new Arm-based server processors in 2027) — positive — not_a_recommendation
- TSMC — — — UNRESOLVED — the source states: supplier (Foundry whose tight capacity limits AMD's server CPU orders) — neutral — not_a_recommendation
- Inferact — — — PRIVATE — the source states: supplier (OSS ecosystem developer (vLLM creators) that built Kimi K3 megakernels with Google) — neutral — not_a_recommendation
- RedHat — — — UNRESOLVED — the source states: context (Named vLLM maintainer) — neutral — not_a_recommendation
- RadixArk — — — PRIVATE — the source states: supplier (OSS developer and SGLang maintainer submitting TPUv7 benchmark results) — neutral — not_a_recommendation
- Microsoft Azure — — — UNRESOLVED — the source states: context (Named buyer of compute supporting InferenceX benchmark) — neutral — not_a_recommendation
- Huggingface — — — PRIVATE — the source states: context (ML community supporter of InferenceX) — neutral — not_a_recommendation
- MiniMax — — — UNRESOLVED — the source states: context (Named AI lab supporting the benchmark) — neutral — not_a_recommendation
- ZAI — — — UNRESOLVED — the source states: context (Named AI lab; developer of GLM model) — neutral — not_a_recommendation
- Qwen — — — NOT_A_SECURITY — the source states: context (Named AI lab / model used in benchmarks (Qwen3.5)) — neutral — not_a_recommendation
- Moonshot Kimi — — — PRIVATE — the source states: context (Named AI lab; developer of Kimi K3 model) — neutral — not_a_recommendation
- SambaNova — — — PRIVATE — the source states: context (Accelerator vendor to be added to InferenceX) — neutral — not_a_recommendation
- Trainium2/3 — — — NOT_A_SECURITY — the source states: comparator (AWS custom silicon to be benchmarked) — neutral — not_a_recommendation
- OpenAI Jalapeño — — — NOT_A_SECURITY — the source states: comparator (Accelerator/chip on InferenceX benchmark) — neutral — not_a_recommendation
- Nvidia Rubin NVL72 — — — NOT_A_SECURITY — the source states: comparator (NVIDIA next-gen rack; benchmarked up to 6x better perf per dollar vs TPUv7 (preview)) — positive — not_a_recommendation
- Google Deepmind — — — PRIVATE — the source states: context (AI lab co-designing models to fit TPUs) — neutral — not_a_recommendation
- llm-d — — — NOT_A_SECURITY — the source states: context (Open-source Kubernetes router for disaggregated prefill/decode serving used in TPU benchmarks) — neutral — not_a_recommendation
- LMCache — — — NOT_A_SECURITY — the source states: context (ML community project supporting the InferenceX benchmark) — neutral — not_a_recommendation
- Ray — — — NOT_A_SECURITY — the source states: context (Ecosystem project TPU partners with upstream) — neutral — not_a_recommendation
- TileRT — — — NOT_A_SECURITY — the source states: context (OSS project receiving AMD cluster access) — neutral — not_a_recommendation
- Tokenspeed — — — NOT_A_SECURITY — the source states: context (OSS project receiving AMD cluster access) — neutral — not_a_recommendation
- Bryan Shan — — — UNRESOLVED — the source states: context (Named author of a referenced prior SemiAnalysis TileRT article) — neutral — not_a_recommendation
- Daniel Nishball — — — UNRESOLVED — the source states: context (Named author of a referenced prior SemiAnalysis TileRT article) — neutral — not_a_recommendation
**Sector labels:** AI training accelerators, custom AI silicon, Semiconductors, Arm-based server CPUs, x86 server CPUs, AI accelerators, inference compute
**Cited baskets (members not named by the source):**
- none
**Enrichment — external hypotheses, not named by the source:** Proposed by the model on 2026-11-09 from the thesis's own steps — not named by the source, never counted toward the research action.
- Marvell Technology (MRVL) — exposed — would benefit IF this holds: “Higher Trainium training adoption would improve AWS custom-silicon economics vs buying Nvidia GPUs; article gives no earnings figure.” (model inference) [s03.2]: Co-designs AWS Trainium custom silicon; broader Trainium training adoption lifts its data-center custom-ASIC and connectivity revenue. · basis (the model's): product sales — custom compute ASICs for hyperscalers · 10-K filed 2026-03-11 (0001835632-26-000011): the filing states no revenue-source sentence naming a way of earning in the words this check reads — not found is not wrong; read the filing
- Broadcom (AVGO) — exposed — would benefit IF this holds: “Higher Trainium training adoption would improve AWS custom-silicon economics vs buying Nvidia GPUs; article gives no earnings figure.” (model inference) [s03.2]: Designs hyperscaler custom AI silicon (including Google TPU); rising custom-silicon adoption versus merchant GPUs expands its ASIC and networking revenue. · basis (the model's): product sales — custom AI accelerator ASICs and networking · 10-K filed 2025-12-18 (0001730168-25-000121): the filing states no revenue-source sentence naming a way of earning in the words this check reads — not found is not wrong; read the filing
- Alphabet (GOOGL, GOOG) — exposed — would benefit IF this holds: “Higher Trainium training adoption would improve AWS custom-silicon economics vs buying Nvidia GPUs; article gives no earnings figure.” (model inference) [s03.2]: TPUv7 Ironwood winning external inference customers improves Google Cloud custom-silicon economics and wins workloads versus buying Nvidia GPUs. · basis (the model's): usage-based — Google Cloud TPU compute · 10-K filed 2026-02-05 (0001652044-26-000018): its revenue-source sentences name advertising — not usage-based
- Credo Technology (CRDO) — exposed — would benefit IF this holds: “Higher Trainium training adoption would improve AWS custom-silicon economics vs buying Nvidia GPUs; article gives no earnings figure.” (model inference) [s03.2]: Supplies connectivity for hyperscaler custom-silicon clusters; expanded Trainium/TPU deployments increase demand for its interconnect products. · basis (the model's): product sales — connectivity products for AI accelerator clusters · 10-K filed 2026-06-15 (0001628280-26-043303): the filing states no revenue-source sentence naming a way of earning in the words this check reads — not found is not wrong; read the filing

## 06 WHY NOW? (NEXT 2-4 QUARTERS)
**Near term:**
- **FORECAST:** TPUv7 FP8 already beats or matches NVIDIA/AMD on multiple AgentX models now; TPUv8i and TPUv8 (FP4) benchmarks and the Rubin comparison are near-term catalysts. [C-93f1ce7c6016ba, C-64f6a11955d6bc, C-328a06d9320182, C-d317fa8617b762]
- **FORECAST:** Arm share pushes above 20% in 2026, with substantial 2027 ramp led by NVIDIA Vera and multiple hyperscaler in-house processors. ⟨cited figures: forecast; approximate⟩ [C-ae101db5717c0b, C-0aa530b9902c5f, C-1022b1afa327c5]
- **SOURCE OPINION:** Hands-on benchmarks show decent training performance and broad library support now, with compilation-time friction being actively addressed. ⟨cited figures: forecast; approximate⟩ [C-c03e1c527e8256, C-9c90bd72c762ab, C-8f717dcb83688c, C-ead98710d7a634, C-3e3ab62fd92fc1, C-c43041301a37f3] ⚠ **UNRESOLVED REVIEW — Supports throughput/MFU, 93% pass rate, 27min compile time, and the 2-orders-of-magnitude reduction target. But 'broad library support now' relies on C-c43041301a37f3 (100k+ HF models collected), which is a list AWS collected, not demonstrated broad support — an overstatement.**
**Longer-term / structural:**
- **MODEL INFERENCE:** TPU is replicating NVIDIA's ecosystem playbook by giving OSS maintainers liberal chip access, building a durable inference software moat.
- **FORECAST:** AI inference adoption is structurally reshaping the server CPU market away from x86 dominance toward Arm. ⟨cited figures: forecast; approximate⟩ [C-5f8fcaed366329, C-0aa530b9902c5f]
- **SOURCE OPINION:** The publisher frames Trainium as a potential challenger to Nvidia's training dominance if software matures, but concedes it is nowhere near CUDA ecosystem maturity. [C-f41ae4588179e6, C-2beeceb16d5c88]
**Catalyst window:** Q1 2027 TPUv8 with FP4 support [MEASURED OBSERVATION]
**Consensus / valuation:** NOT ASSESSED — NOT_ASSESSED — the registry holds no consensus, market-expectation or valuation data; an opportunity here is not valuation proof
**Is it priced? — MARKET CONTEXT — evidence for your judgement; never read by the research action** — as of 2026-11-09, against SPY; Polygon daily bars, split-adjusted closes (prices held 2024-11-11 to 2026-11-06); Tiingo raw closes and split factors before them, for five years of P/E; SEC XBRL annual diluted EPS filed on or before each day; consensus revisions from the fund's CIQ dossiers.
- Amazon [AMZN] — close 259.30 (2026-11-06)
  - vs 200-day avg: +6.3% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −8.7% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (284.02 on 2026-08-03)
  - 3m vs SPY: −1.9 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −3.5 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 36.2× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2025-12-31 (313d old, filed 2026-02-06)
  - P/E vs own history: 35th pctile · 2y — share of its daily P/Es from 2024-11-11 to 2026-11-09 at or below today's (the prices held); five years not used — a share-basis change (stock split) falls inside the window — prices are split-adjusted but the older annual EPS is as-filed, so a trailing range would divide the two bases against each other. The current P/E stands; its percentile cannot be built (filer restated its own comparatives by ~20.01x)
  - Revisions (3m): +7.0% · 14↑ 1↓ — FY 2027 EPS Normalized consensus over the 3 months to the CIQ export (on or after 2026-11-01; the fund's dossier assembled 2026-11-03): 10.18 → 10.89; 14 analyst(s) revised up and 1 down, of 33
- Microsoft [MSFT] — close 530.61 (2026-11-06)
  - vs 200-day avg: +20.6% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −4.5% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (555.80 on 2026-11-04)
  - 3m vs SPY: +9.7 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −2.8 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 29.6× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2026-06-30 (132d old, filed 2026-07-29)
  - P/E vs own history: 24th pctile · 5y — share of its daily P/Es from 2021-11-10 to 2026-11-09 at or below today's (Tiingo split-adjusted closes 2021-11-03 to 2024-11-08, rebased onto Polygon's over 95 overlapping days (ratio 1.0000); Polygon from 2024-11-11)
  - Revisions (3m): not held — no CIQ consensus held for MSFT (the fund holds CIQ exports for its dossier names only)
- Intel [INTC] — close 56.28 (2026-11-06)
  - vs 200-day avg: −35.3% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −60.1% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (140.94 on 2026-06-22)
  - 3m vs SPY: −37.4 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: +38.0 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: not held — the last positive annual EPS is older than one filing cycle — a more recent annual figure exists and is negative, so valuing on the older one prices a business that no longer reports those earnings
  - P/E vs own history: not held — the last positive annual EPS is older than one filing cycle — a more recent annual figure exists and is negative, so valuing on the older one prices a business that no longer reports those earnings; five years not used — the last positive annual EPS is older than one filing cycle — a more recent annual figure exists and is negative, so valuing on the older one prices a business that no longer reports those earnings
  - Revisions (3m): not held — no CIQ consensus held for INTC (the fund holds CIQ exports for its dossier names only)
- Meta [META] — close 610.09 (2026-11-07)
  - vs 200-day avg: −3.4% — close 2026-11-07 against the average of the 200 daily closes 2026-01-26 to 2026-11-07
  - From 52-wk high: −21.5% — close 2026-11-07 against the highest close of the 52 weeks to 2026-11-09 (777.59 on 2026-09-24)
  - 3m vs SPY: +7.4 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-07, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −11.4 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-07, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 26.0× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2025-12-31 (313d old, filed 2026-01-29)
  - P/E vs own history: 35th pctile · 5y — share of its daily P/Es from 2021-11-10 to 2026-11-09 at or below today's (Tiingo split-adjusted closes 2021-11-03 to 2024-11-08, rebased onto Polygon's over 95 overlapping days (ratio 1.0000); Polygon from 2024-11-11)
  - Revisions (3m): not held — no CIQ consensus held for META (the fund holds CIQ exports for its dossier names only)
- Oracle [ORCL] — close 116.10 (2026-11-06)
  - vs 200-day avg: −25.3% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −53.2% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (248.15 on 2026-06-01)
  - 3m vs SPY: −18.3 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −61.1 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 19.9× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2026-05-31 (162d old, filed 2026-06-22)
  - P/E vs own history: 11th pctile · 5y — share of its daily P/Es from 2021-11-10 to 2026-11-09 at or below today's (Tiingo split-adjusted closes 2021-11-03 to 2024-11-08, rebased onto Polygon's over 95 overlapping days (ratio 1.0000); Polygon from 2024-11-11)
  - Revisions (3m): not held — no CIQ consensus held for ORCL (the fund holds CIQ exports for its dossier names only)
- **Companies the thesis implies — EXTERNAL HYPOTHESIS, not named by the source; never counted:**
- Marvell Technology [MRVL] — close 141.17 (2026-11-07)
  - vs 200-day avg: −23.8% — close 2026-11-07 against the average of the 200 daily closes 2026-01-26 to 2026-11-07
  - From 52-wk high: −55.4% — close 2026-11-07 against the highest close of the 52 weeks to 2026-11-09 (316.43 on 2026-06-04)
  - 3m vs SPY: −27.4 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-07, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: +45.7 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-07, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 46.0× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2026-01-31 (282d old, filed 2026-03-11)
  - P/E vs own history: not held — history below the floor — too short to judge a trailing range: only 169 P/E points (< 450); five years not used — history below the floor — too short to judge a trailing range: only 169 P/E points (< 450)
  - Revisions (3m): not held — no CIQ consensus held for MRVL (the fund holds CIQ exports for its dossier names only)
- Broadcom [AVGO] — close 293.69 (2026-11-06)
  - vs 200-day avg: −20.0% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −39.0% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (481.57 on 2026-06-02)
  - 3m vs SPY: −25.6 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −25.5 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 61.6× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2025-11-02 (372d old, filed 2025-12-18)
  - P/E vs own history: not held — the per-share basis changes inside the window — the year ending 2023-10-29: EPS 32.98 as first filed, 3.3 as filed 2025-12-18 (×10.0) (and 1 more); five years not used — a share-basis change (stock split) falls inside the window — prices are split-adjusted but the older annual EPS is as-filed, so a trailing range would divide the two bases against each other. The current P/E stands; its percentile cannot be built (filer restated its own comparatives by ~10x)
  - Revisions (3m): not held — no CIQ consensus held for AVGO (the fund holds CIQ exports for its dossier names only)
- Alphabet [GOOGL] — close 284.78 (2026-11-06)
  - vs 200-day avg: −16.1% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −29.3% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (402.62 on 2026-05-13)
  - 3m vs SPY: −15.5 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −7.5 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 26.3× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2025-12-31 (313d old, filed 2026-02-05)
  - P/E vs own history: 30th pctile · 2y — share of its daily P/Es from 2024-11-11 to 2026-11-09 at or below today's (the prices held); five years not used — a share-basis change (stock split) falls inside the window — prices are split-adjusted but the older annual EPS is as-filed, so a trailing range would divide the two bases against each other. The current P/E stands; its percentile cannot be built (filer restated its own comparatives by ~20x)
  - Revisions (3m): +2.6% · 11↑ 7↓ — FY 2027 EPS Normalized consensus over the 3 months to the CIQ export (on or after 2026-11-01; the fund's dossier assembled 2026-11-03): 14.8 → 15.19; 11 analyst(s) revised up and 7 down, of 31
- Credo Technology [CRDO] — close 120.51 (2026-11-06)
  - vs 200-day avg: −33.3% — close 2026-11-06 against the average of the 200 daily closes 2026-01-23 to 2026-11-06
  - From 52-wk high: −60.2% — close 2026-11-06 against the highest close of the 52 weeks to 2026-11-09 (302.52 on 2026-06-22)
  - 3m vs SPY: −44.9 pp — window 2026-08-10→2026-11-06 spans 88d over 64 bars (target 91d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - 12m vs SPY: −35.9 pp — window 2025-11-07→2026-11-06 spans 364d over 251 bars (target 365d; common last bar; name frontier 2026-11-06, benchmark frontier 2026-11-06; 3d short of the 2026-11-09 reference)
  - P/E: 48.0× — price 2026-11-09 ÷ annual diluted EPS for the period ending 2026-05-02 (191d old, filed 2026-06-15)
  - P/E vs own history: not held — history below the floor — too short to judge a trailing range: only 341 P/E points (< 450); five years not held — not fetched this run — Tiingo's free plan allows 50 requests an hour; a later run fetches it
  - Revisions (3m): not held — no CIQ consensus held for CRDO (the fund holds CIQ exports for its dossier names only)
- Revisions: the next fiscal year's EPS consensus over 3 months, and the analysts who revised it up and down — from the fund's CIQ dossiers (its dossier names only), when the export is on or before the date and at most a month old.

## 07 WHAT COULD GO WRONG?
**Counter-evidence:**
- **MEASURED OBSERVATION:** gpt-oss training run had compilation time of 27 minutes 17 seconds. [C-ead98710d7a634]
- **SOURCE OPINION:** The Trainium stack is nowhere near CUDA ecosystem maturity, but heading in the right direction. [C-f41ae4588179e6]
- **SOURCE OPINION:** Trainium Torch will not support TorchAO MXFP8 at launch, prioritizing BF16 training first. [C-61e0ae0df73695]
- **SOURCE OPINION:** MoE combine and dispatch operations account for 60-70% of communication volume in MoE training/inference. ⟨cited figures: approximate⟩ [C-3709dfeba3a7e2] ⚠ **UNRESOLVED REVIEW — The cited span says MoE combine/dispatch take 60-70% of communication volume but does not specify 'training/inference' scope; the card adds that scope unsupported. Also labelled MEASURED OBSERVATION with approximate=True, which matches.**
- **SOURCE OPINION:** All 7 failed FlexAttention cases on Trainium3 occurred at large batch/sequence length and were due to compilation timeouts, not numerical errors. [C-d7fb27d367ba02]
- **SOURCE OPINION:** It took over 9 months of pushing AMD leadership to get engineers enough stable nodes to reach 93% parity on gating test groups. ⟨cited figures: approximate⟩ [C-47cf21c7bf0774]
- **SOURCE OPINION:** At one unnamed hardware vendor, CI numbers shown to leadership were 99.99% while actual gating parity was below 5%. [C-42218bf8c5f870] ⚠ **UNRESOLVED REVIEW — Cited span supports 99.99% CI vs below 5% actual gating parity, but does not identify this as 'one unnamed hardware vendor'; the vendor framing is added, though not contradicted.**
- **SOURCE OPINION:** Trainium does not yet support PyTorch's TokenSwitch MoE API; AWS has committed to collaborate with Meta's PyTorch team to add support. [C-60b12eb4e73294]
- **MEASURED OBSERVATION:** x86 segment accounted for nearly 90% of server CPU market in 2025 ⟨cited figures: approximate⟩ [C-040ac638d8dbbf]
- **FORECAST:** AMD's server CPU market share estimated to increase to approximately 27% in 2026 ⟨cited figures: forecast; approximate⟩ [C-6c2c4ac5a74a70]
- **SOURCE OPINION:** NVIDIA NVFP4 still beats TPUv7 FP8 on GLM-5.2, but with accuracy/quality loss. [C-25c082eebb3cd6] ⚠ **UNRESOLVED REVIEW — Cited span supports 'NVIDIA NVFP4 still beats TPUv7 FP8, but with accuracy/quality loss.' The 'on GLM-5.2' model scope is added and not in the cited span.**
- **SOURCE OPINION:** On GLM-5.3 at 100 tok/s/user, GB300 FP4 delivers 3.6x the tokens per dollar of TPUv7. [C-7d400bfcc93a1a] ⚠ **UNRESOLVED REVIEW — The 3.6x GB300 FP4 vs TPUv7 at 100 tok/s/user is supported, but the 'GLM-5.3' model scope is not present in the cited span.**
- **SOURCE OPINION:** On GLM-5.3 at 100 tok/s/user, GB200 FP4 delivers 3.5x the tokens per dollar of TPUv7. [C-b54c975a0db1ce] ⚠ **UNRESOLVED REVIEW — 3.5x GB200 FP4 at 100 tok/s/user supported, but 'GLM-5.3' model scope is not in the cited span.**
- **SOURCE OPINION:** After four NVIDIA refreshes, GB300 FP4 now leads TPUv7 by 1.5x to 2.6x on Kimi K3. [C-4d9a6581f5a9b8] ⚠ **UNRESOLVED REVIEW — 'GB300 FP4 now leads by 1.5x to 2.6x after four NVIDIA refreshes' is supported; the 'on Kimi K3' model scope is not in the cited span.**
- **SOURCE OPINION:** VR200 delivers 4.3x to 5.6x the tokens per dollar of TPUv7 on Kimi K3. [C-ca979b9d2149b4] ⚠ **UNRESOLVED REVIEW — 'VR200 delivers 4.3x to 5.6x TPUv7' supported; 'on Kimi K3' model scope not in cited span.**
- **SOURCE OPINION:** In a comparison SemiAnalysis calls unfair, Rubin NVL72 is up to 6x better perf per dollar than TPUv7. [C-974463c6db4ad5] ⚠ **UNRESOLVED REVIEW — 'Rubin NVL72 up to 6x better perf per dollar than TPUv7' is supported, but the 'comparison SemiAnalysis calls unfair' qualifier is not in the cited span.**
**Alternative mechanisms / competing hypotheses:**
- **WITHHELD — failed source verification:** NUMBER_NOT_IN_CITED_CLAIMS — s07.16 prints '100', which none of its cited claims carry: 'The stack still has real friction (long compile times, missing TokenSwitch/MXFP8 support, <100% QA p'
- **MODEL INFERENCE:** Registry link — 8 other theses in the same broader area (ai_infrastructure) — context only, never evidence; the desk lists them
- **FORECAST:** AMD is still gaining x86 share and is projected to maintain stable shipments with new 1H 2027 launches, so the x86 segment is not uniformly losing. [C-6c2c4ac5a74a70, C-98c8f03b45a9ca]
- **MEASURED OBSERVATION:** FP4 GPUs (GB300/GB200) still deliver more tokens per dollar at most speeds, TPUv7 lacks native FP4 until Q1 2027, and next-gen Rubin/VR200 lead by multiples; NVIDIA counter-submissions can narrow or reverse FP4 gaps. [C-7d400bfcc93a1a, C-b54c975a0db1ce, C-4d9a6581f5a9b8, C-ca979b9d2149b4, C-974463c6db4ad5]
**Market-level risks:**
- **SOURCE OPINION:** SemiAnalysis identifies NVIDIA's internal bureaucracy (e.g. driver features stuck in legal review for months, stingy OSS cluster contributions) as one of the biggest risks to its software ecosystem moat. (scope: Risk to NVIDIA's competitive moat specifically, per SemiAnalysis opinion; not quantified as a revenue or earnings impact.) [C-cf964f66949928, C-8690214eaae524] ⚠ **UNRESOLVED REVIEW — Cited spans support 'one of the biggest risks to NVIDIA's moat' and that NVIDIA is slower to external input. But 'driver features stuck in legal review for months' is not in the cited spans (that is C-7f25f24b1cd88b in the pool).**
- **SOURCE OPINION:** Benchmark comparisons rely on contested cost bases, mixed precision formats (FP8 vs FP4/NVFP4 with accuracy tradeoffs), and preview-only Rubin submissions not independently reproduced, so headline perf-per-dollar leads may not reflect like-for-like production economics. (scope: Methodological limitation of the AgentX/InferenceX comparisons presented; affects interpretation of all TPU-vs-GPU claims.) [C-25c082eebb3cd6, C-974463c6db4ad5, C-7bf6aaf2c1e36e]
**Disconfirming signals:**
- TorchNeuron compile-time reduction fails to ship or underdelivers
- Major labs continue training exclusively on Nvidia/CUDA despite TorchNeuron
- QA/parity pass rates stall below CUDA-grade reliability
- Arm server CPU share stalling below 20% in 2026
- x86 suppliers retaining share into 2027
- Delays in NVIDIA Vera or hyperscaler Arm CPU ramps
- NVIDIA FP4/Rubin submissions that restore perf-per-dollar lead across the full curve at equal quality
- TPU external customers reducing orders or reverting to GPUs
- TPUv8 FP4 slipping beyond Q1 2027
**Unknowns:**
- Whether broader Trainium training adoption translates into measurable AWS revenue, share gains or margin benefit
- Whether listed AMZN/NVDA valuations reflect any Trainium training share shift
- Whether the publisher's single-model benchmarks generalize across production training workloads (association, not demonstrated commercial traction)
- Whether the forecast share gains translate into revenue or earnings for named Arm CPU designers or hyperscalers
- Whether in-house hyperscaler silicon benefits merchant suppliers like Arm or displaces them
- Consensus expectations versus these forecasts
- Whether benchmark perf-per-dollar wins translate into TPU volume share gains and quantified Alphabet revenue/NVIDIA revenue erosion
- Whether TPUv7 FP8 advantage survives NVIDIA FP4 refreshes and Rubin at equivalent generations
- The actual cost basis assumptions underlying 'tokens per dollar' external-customer claims

## 08 DECISION & NEXT TRIGGER
**WATCH** — research attention only; never a purchase or sale.
- **MODEL INFERENCE:** Examine SemiAnalysis Accelerator Model TPUv7/v8 shipment estimates and cost-basis assumptions to test whether benchmark wins convert into material external TPU volume share versus NVIDIA.
**Would raise priority:**
- TorchNeuron ships the ~2-orders-of-magnitude compile-time reduction with named lab adoption
- A Tier-1 lab commits to Trainium for a frontier training run
- NVIDIA Vera CPU volume guidance confirms substantial 2027 ramp
- Hyperscalers disclose larger in-house Arm CPU deployment
- TPUv8 ships with FP4 on schedule and matches GPU perf-per-dollar
- Additional hyperscalers announce large TPU purchase commitments
**Would lower priority:**
- Compile-time and QA gaps persist
- No new training customers adopt Trainium3 despite the software push
- Intel or AMD x86 roadmaps regain share
- Arm CPU ramps slip into 2028
- NVIDIA FP4/Rubin reclaims clear perf-per-dollar lead at equal quality across the curve
- TPU external customer additions stall
**Investment readiness:** NOT_ASSESSED — the registry holds no consensus, market-expectation or valuation data; an opportunity here is not valuation proof
**Decision trace (audit):**
- WATCH (RESEARCH NOW unmet: retrieval PARTIAL)

## 09 SOURCES & CHANGE HISTORY
- [Amazon’s Trainium Takes a Strike at the Training King](https://newsletter.semianalysis.com/p/amazons-trainium-takes-a-strike-at) — Kimbo Chen; Dylan Patel — SemiAnalysis — article date 2026-10-23 — independent_research — retrieval PARTIAL — origins: Tristan Hume on Twitter, publisher's own analysis — novelty_unverified (30 claim refs; A-9fadab568080)
- [Server CPU Shipments Projected to Grow Over 40% YoY in 2027, with Arm-Based Products Continuing to Gain Market Share, Says TrendForce](https://www.trendforce.com/presscenter/news/20261022-13279.html) — TrendForce (organization (as stated)) — TrendForce — article date 2026-10-22 — industry_data_report — retrieval FULL — origins: publisher's own analysis — contradictory (9 claim refs; A-a7f0f66d2b3b)
- [The Iron(wood) Throne: Google's TPU Stakes Its Claim on Inference](https://newsletter.semianalysis.com/p/tpu-strikes-the-king) — Bryan Shan; Alec Ibarra; Cam Quilici; Kimbo Chen; Wenyao Gao; Dylan Patel; Myron Xie — SemiAnalysis — article date 2026-11-05 — independent_research — retrieval PARTIAL — origins: AMD, Meta, not attributed by the source, publisher's own analysis — contradictory (33 claim refs; A-866829df2ed0)
**Version history:**
- v1 as of 2026-10-30 — WATCH — evidence NEW — Initial record — created from A-9fadab568080 (initial assessment — WATCH (RESEARCH NOW unmet: no verified dislocation or catalyst; retrieval PARTIAL))
- v2 as of 2026-10-30 — WATCH — evidence MIXED — A-a7f0f66d2b3b: contradictory ×2, new ×7 (no change in action (F1_source_reliability medium→high; F2_material_evidence 14→21; F3_independent_origins 2→3; F4_profit_transmission inferred→source-shown; F6_recognizable_exposures 1 listed · 0 sector · 0 instrument→3 listed · 2 sector · 0 instrument; F8_counterevidence 7→9; F11_retrieval PARTIAL→FULL))
  - s04_key_evidence: new — Alibaba is introducing new Yitian 720/730 server CPUs, cited as a 2027 Arm-based growth driver.: 720/730
  - s04_key_evidence: new — Arm server CPU market share: 10%
  - s04_key_evidence: new — Arm server CPU market share: above 20%
  - s04_key_evidence: new — Arm server CPU market share: approximately 30%
  - s04_key_evidence: new — Google Axion CPUs in high-volume shipment; Microsoft Cobalt 100 and Arm AGI processors in mass production/shipment:
  - s04_key_evidence: new — Arm server CPU growth in 2027 driven primarily by ramp-up in NVIDIA Vera CPU shipments:
  - s04_key_evidence: new — AMD's server CPU market share expected to increase further with new product launches in 1H 2027:
  - s07_what_could_go_wrong.counter_evidence: contradictory — x86 segment accounted for nearly 90% of server CPU market in 2025 ⟨cited figures: approximate⟩
  - s07_what_could_go_wrong.counter_evidence: contradictory — AMD's server CPU market share estimated to increase to approximately 27% in 2026 ⟨cited figures: forecast; approximate⟩
  - s06_why_now.catalyst_window: new — First half of 2027 and 2027 production ramps [MODEL INFERENCE] — the source names no dated catalyst or earnings window
  - s05_affected.companies: new — Arm (potential_beneficiary)
  - s05_affected.companies: new — Google (potential_beneficiary)
  - s05_affected.companies: new — Microsoft (potential_beneficiary)
  - s05_affected.companies: new — Alibaba (potential_beneficiary)
  - s05_affected.companies: new — Intel (potentially_harmed)
  - s05_affected.sector_exposures: new — Arm-based processors (positive)
  - s05_affected.sector_exposures: new — x86 segment (negative)
  - s01_bottom_line: new — ⟨update 2026-10-22 · TrendForce⟩ Arm-based server CPUs are forecast to grow faster than x86, rising from above 20% share in 2026 to approximately 30% in 2027, a… [+147 chars — full text in the JSON export]
- v3 as of 2026-11-09 — WATCH — evidence MIXED — A-866829df2ed0: contradictory ×6, new ×27 (no change in action (F1_source_reliability high→medium; F2_material_evidence 21→40; F3_independent_origins 3→5; F6_recognizable_exposures 3 listed · 2 sector · 0 instrument→5 listed · 3 sector · 0 instrument; F7_dislocation_or_catalyst absent→present; F8_counterevidence 9→15; F11_retrieval FULL→PARTIAL))
  - s04_key_evidence: new — performance per dollar advantage: up to 50%
  - s04_key_evidence: new — context length: 1M tokens
  - s04_key_evidence: new — relative throughput: >2x
  - s04_key_evidence: new — tokens per dollar ratio: 1.15x to 2.5x
  - s04_key_evidence: new — tokens per dollar ratio: 1.2x to 2.7x
  - s04_key_evidence: new — model parameters: 816B parameters
  - s04_key_evidence: new — On Google's internal cost basis, TPUv7 beat GB300 at 100 and 200 tok/s/user for Kimi K3: 100 tok/s/user
  - s04_key_evidence: new — performance per dollar ratio: 1.64x
  - s04_key_evidence: new — tokens per dollar ratio: 4.4x
  - s04_key_evidence: new — systolic array padded: 25%
  - s04_key_evidence: new — performance per dollar ratio: 1.67x
  - s04_key_evidence: new — megakernel speedup: 2.31x
  - s04_key_evidence: new — Qwen3.5 397B was the first model Google submitted to AgentX, two weeks before this article: Two weeks
  - s04_key_evidence: new — Long-context, multi-turn agentic serving is where inference spend is heading, which is why customers want AgentX results:
  - s04_key_evidence: new — The Kimi K3 TPU result was built by the vLLM ecosystem (Inferact, founded by vLLM's creators) with Google, open source on vLLM TorchTPU:
  - s04_key_evidence: new — Current and potential TPU customers are asking Google for AgentX results because the benchmark closely matches their real inference workloads:
  - s04_key_evidence: new — Meta is an early TPU adopter already deploying TPUv7 in production using SGLang-TorchTPU.:
  - s04_key_evidence: new — NVIDIA is now slower moving than AMD, Google and Amazon on external suggestions, git commits and feedback.:
  - s04_key_evidence: new — relative performance:
  - s04_key_evidence: new — Oracle, OpenAI, Anthropic and Meta have all become customers of Google TPUs.:
  - s04_key_evidence: new — NVIDIA's FP4 counter submission beats TPUv7 FP8 on decode but overtuned at expense of prefill, so TPUv7 FP8 still beats GB300 NVL72 FP4 on end-to-end performanc… [+2 chars — full text in the JSON export]
  - s04_key_evidence: new — Major hyperscalers/AI labs use Qwen3.5 397B and scaled versions as proxy models for hardware purchasing and capacity planning decisions:
  - s04_key_evidence: new — AMD is giving upstream OSS maintainers liberal cluster access and rapidly increasing its CI fleet with minimal bureaucracy:
  - s04_key_evidence: new — TPUv8 with native FP4 support is expected in Q1 2027.:
  - s07_what_could_go_wrong.counter_evidence: contradictory — NVIDIA NVFP4 still beats TPUv7 FP8 on GLM-5.2, but with accuracy/quality loss.
  - s07_what_could_go_wrong.counter_evidence: contradictory — On GLM-5.3 at 100 tok/s/user, GB300 FP4 delivers 3.6x the tokens per dollar of TPUv7.
  - s07_what_could_go_wrong.counter_evidence: contradictory — On GLM-5.3 at 100 tok/s/user, GB200 FP4 delivers 3.5x the tokens per dollar of TPUv7.
  - s07_what_could_go_wrong.counter_evidence: contradictory — After four NVIDIA refreshes, GB300 FP4 now leads TPUv7 by 1.5x to 2.6x on Kimi K3.
  - s07_what_could_go_wrong.counter_evidence: contradictory — VR200 delivers 4.3x to 5.6x the tokens per dollar of TPUv7 on Kimi K3.
  - s07_what_could_go_wrong.counter_evidence: contradictory — In a comparison SemiAnalysis calls unfair, Rubin NVL72 is up to 6x better perf per dollar than TPUv7.
  - s06_why_now.catalyst_window: new — Q1 2027 TPUv8 with FP4 support [MEASURED OBSERVATION]
  - s05_affected.companies: new — Meta (spending_customer)
  - s05_affected.companies: new — Oracle (spending_customer)
  - s05_affected.sector_exposures: new — TPU (positive)
  - s01_bottom_line: new — ⟨update 2026-11-05 · SemiAnalysis⟩ SemiAnalysis's own AgentX benchmarks show TPUv7 Ironwood delivering competitive or superior tokens-per-dollar versus NVIDIA G… [+132 chars — full text in the JSON export]

_Generated 2026-11-09 15:21 UTC from the registry (ti-engine-5; run R-20261109T145909Z-market, extract ti-extract-6, review ti-review-4, model claude-opus-4-8)._
