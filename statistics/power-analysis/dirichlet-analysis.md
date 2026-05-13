This is a much more structured problem than generic ordinal power analysis — you're essentially doing **pattern classification over a discrete probability simplex**, and your evidence criterion should reflect that.

---

### What you actually have

After collapsing, each survey item produces a **trinomial distribution** over {−, 0, +}. Your RL pipeline doesn't just need a point estimate — it needs to distinguish five qualitatively different **probability patterns** (your norm signatures):

| Pattern | Character | Example (p−, p0, p+) |
|---|---|---|
| Mostly negative | Norm violation feels bad | (.65, .25, .10) |
| Mostly positive | Norm endorsed | (.10, .25, .65) |
| Mostly neutral | No strong norm | (.15, .70, .15) |
| Polarized (neg ≈ pos, low neutral) | Contested norm | (.40, .15, .40) |
| Flat | Indifference / noise | (.33, .33, .33) |

These are regions in the **2-simplex** (since p− + p0 + p+ = 1, the space is a triangle). Your power analysis problem is really: *at sample size N, can I reliably identify which region of the simplex the true distribution falls in?*

---

### Implications for the evidence criterion

The ROPE recommendation still holds but needs to be **redefined on the simplex**, not on a mean difference. Concretely:

**Primary criterion: Posterior pattern separability**

For each item, you fit a Dirichlet-multinomial model to the collapsed trinomial counts. The posterior is a Dirichlet over (p−, p0, p+). Power is the probability that the posterior is **concentrated enough within one region** of the simplex to unambiguously classify the pattern.

This means defining your five regions geometrically — essentially a Voronoi partition of the simplex — and then asking: does > X% of posterior mass fall within a single region?

**Secondary criterion for the standalone paper**

You still want communicable claims. The natural ones are:

- **Probability of direction**: P(p+ > p−) or P(p− > p+) — is the norm directional?
- **Neutrality test**: is the majority of mass near the centroid (flat/neutral)?
- **Polarization index**: P(p0 < min(p−, p+)) — does the middle category "dip"?

These are all computable directly from the Dirichlet posterior and are reportable in a social norms paper without requiring readers to know what a simplex is.

---

### The five patterns as Dirichlet priors

You also now have a natural way to set your **simulation priors** — one per pattern — which makes the power analysis a **worst-case distinguishability analysis**:

```r
# Dirichlet concentration parameters (alpha) for each pattern
# Order: (negative, neutral, positive)
patterns <- list(
  mostly_negative  = c(6, 2, 1),
  mostly_positive  = c(1, 2, 6),
  mostly_neutral   = c(1, 6, 1),
  polarized        = c(4, 1, 4),
  flat             = c(2, 2, 2)
)
```

The **hardest discrimination pairs** — where you need the most power — are:
- **flat vs. neutral**: both have low tails, but neutral has a higher p0
- **polarized vs. flat**: polarized has suppressed neutral, flat does not
- **mostly_negative vs. polarized**: both have high p−, differ in p+

Your power analysis should focus on these boundary cases, not the easy ones (mostly_negative vs. mostly_positive is trivial to distinguish).

---

### Revised power analysis sketch in R

```r
library(DirichletReg)  # or use MCMCpack / gtools for rdirichlet
library(tidyverse)

# Simulate posterior from trinomial counts using conjugate Dirichlet update
# Prior: Dirichlet(1,1,1) — uninformative
# Posterior: Dirichlet(1 + counts)

classify_pattern <- function(post_samples, threshold = 0.85) {
  # Regions defined by which category dominates, or polarization
  p_neg  <- mean(post_samples[,1] > 0.45)
  p_pos  <- mean(post_samples[,3] > 0.45)
  p_neu  <- mean(post_samples[,2] > 0.45)
  p_pol  <- mean(post_samples[,2] < 0.25 & 
                 abs(post_samples[,1] - post_samples[,3]) < 0.15)
  
  probs <- c(mostly_negative=p_neg, mostly_positive=p_pos,
             mostly_neutral=p_neu, polarized=p_pol)
  
  if (max(probs) > threshold) names(which.max(probs))
  else "ambiguous"
}

run_sim <- function(true_alpha, n, n_post_samples = 2000, threshold = 0.85) {
  # 1. Draw true p from prior
  true_p <- gtools::rdirichlet(1, true_alpha)
  
  # 2. Generate trinomial responses
  counts <- as.vector(rmultinom(1, size = n, prob = true_p))
  
  # 3. Conjugate posterior update
  post_alpha <- c(1,1,1) + counts
  post_samples <- gtools::rdirichlet(n_post_samples, post_alpha)
  
  # 4. Classify
  classify_pattern(post_samples, threshold)
}

# Power for each pattern at N = 60
n_sim <- 1000
ns    <- c(30, 60, 100, 150, 200)

results <- expand_grid(
  pattern = names(patterns),
  n = ns
) |>
  mutate(power = map2_dbl(pattern, n, function(pat, n) {
    true_alpha <- patterns[[pat]]
    sims <- replicate(n_sim, run_sim(true_alpha, n))
    mean(sims == pat)   # correct classification rate
  }))

results |>
  ggplot(aes(n, power, colour = pattern)) +
  geom_line() + geom_point() +
  geom_hline(yintercept = 0.8, linetype = "dashed") +
  labs(title = "Pattern classification power by N",
       x = "N respondents per item", y = "Correct classification rate")
```

---

### Key design decisions this surfaces

1. **Your threshold parameters** (e.g., "dominance > 0.45", "polarization gap < 0.15") are your ROPE equivalents — they should be set from theory about what constitutes a meaningful social norm, not from data.

2. **N is per item, not per person** — since this is within-subject, one participant contributes one response *per item*, so the effective N for each item's trinomial is your participant count. This is actually favorable: you don't need to worry about the multilevel structure for the per-item classification, only for any cross-item comparisons.

3. **The "ambiguous" category is informative** — items that repeatedly land as ambiguous across simulations are genuinely uninformative about norms and arguably shouldn't feed into the RL pipeline with strong weight. You can report the ambiguity rate as a quality metric for each item.

4. **For the RL pipeline**, the natural output is the full posterior Dirichlet parameters per item — not the collapsed classification. The classification is for human readers; the RL agent can work directly with the (p−, p0, p+) posterior.