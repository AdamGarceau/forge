# Do synthetic audiences actually work? The evidence.

Forge asks ~1,000 simulated respondents about an idea before it gets built. Fair question: are those answers worth anything? Here is the honest research picture, with sources. Short version: **grounded synthetic audiences are a strong, cheap directional filter, not a replacement for real people spending real money.** The good uses and the failure modes are both well documented.

## What the peer-reviewed research shows

| Study | What it tested | Headline result |
|---|---|---|
| **Park, Zou, Shaw et al. (2024), Stanford + Google DeepMind**, ["Generative Agent Simulations of 1,000 People"](https://arxiv.org/abs/2411.10109) ([Stanford HAI summary](https://hai.stanford.edu/news/ai-agents-simulate-1052-individuals-personalities-with-impressive-accuracy)) | Agents built from 2-hour interviews of 1,052 real people, tested on GSS items, Big Five, economic games | Agents matched a person's own answers **85% as well as that person matched themselves two weeks later** (near test-retest reliability). Population effect sizes r ≈ 0.98. |
| **same paper, grounding comparison** | Same people simulated three ways: full interview vs. persona summary vs. bare demographics | GSS accuracy **0.85 (interview) → 0.70 (summary) → 0.71 (demographics)**; Big Five **0.80 → 0.75 → 0.55**. Subgroup bias was 36–62% worse for demographic-only agents. **Grounding in real data is the whole game.** |
| **Argyle et al. (2023), *Political Analysis***, ["Out of One, Many"](https://www.cambridge.org/core/journals/political-analysis/article/out-of-one-many-using-language-models-to-simulate-human-samples/035D7C8A55B237942FB6DBAD7CAA4E49) ([arXiv](https://arxiv.org/abs/2209.06899)) | "Silicon sampling": GPT conditioned on real survey backstories vs. human responses | Population distributions and cross-attitude correlation structure were preserved ("algorithmic fidelity"). The foundational paper for the idea. |
| **"LLMs Reproduce Human Purchase Intent" (2025)**, [arXiv 2510.08338](https://arxiv.org/abs/2510.08338) | A semantic-similarity method across 57 real consumer concept tests (9,300 humans) | **90% of human test-retest reliability**, distribution match 0.88. The naive "just ask GPT to rate 1-5" approach did far worse (distribution match 0.26–0.39). Method matters. |
| **Brand, Israeli, Ngwe (2023), HBS**, ["Using LLMs for Market Research"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4395751) | GPT estimating consumer willingness-to-pay | "Realistic and comparable to human studies"; grounding on prior real data improved alignment on new features too. |
| **Arora et al. (2025), *Journal of Marketing***, ["AI-Human Hybrids for Marketing Research"](https://journals.sagepub.com/doi/abs/10.1177/00222429241276529) | GPT-4 replicating a real Fortune-500 dog-food concept test (605 real people) | Means landed close (purchase likelihood 1.58 synthetic vs. 1.66 human). But variance was compressed; retrieval + memory helped partly. |

## Where it breaks (say this out loud, every time)

- **Sycophancy is the dangerous one.** Nielsen Norman Group ([synthetic users](https://www.nngroup.com/articles/synthetic-users/), [AI simulation studies](https://www.nngroup.com/articles/ai-simulations-studies/)) found synthetic users "praised concepts that real users went on to question or reject." It fails in the *flattering* direction, which is worse than random noise. This is exactly why Forge keeps a real-world field test as a hard gate.
- **Means look fine, inference does not.** Bisbee et al. (2024), ["Synthetic Replacements for Human Survey Data? The Perils of LLMs," *Political Analysis*](https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE): aggregate averages matched, but subgroup regression coefficients "often differ significantly," variance was artificially small, and results shifted when the same prompt was re-run months later. Their conclusion: not reliable for statistical inference.
- **Mode collapse (compressed variance)** is the single most-replicated failure across the literature: synthetic panels are less diverse than real ones.
- **Subgroups and minority populations** are consistently worse than the top-line number suggests (LLM training-data skew).
- **Vendor accuracy claims are marketing.** Qualtrics' "12x more accurate" and synthetic-users.com's "80–92%" are self-published, proprietary-methodology, non-peer-reviewed, and sold by the company being validated. Cite the papers above, not the vendors.

## The honest bottom line

Grounded synthetic audiences (built from real customer language, not demographic tags) reliably get you **directional signal, relative ranking, and objection-surfacing, for pennies and in minutes**. They do **not** replace real people voting with their wallets, and they must never be the sole basis for a high-stakes go/no-go. That is precisely how Forge uses them: a cheap filter up front, then real humans in the field as the only decisive test.

*A fuller internal review of ~15 studies (including the weaker results and the vendor-claim teardown) informs this summary; the sources above are the load-bearing, independently verifiable ones.*
