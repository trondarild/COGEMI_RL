# statistics/power-analysis/power_sim_dirichlet.R
#
# Dirichlet-multinomial power analysis for the COGEMI v2 survey.
#
# The pipeline's per-item output is a trinomial distribution over {−, 0, +}.
# Power is defined as the correct classification rate for each of five qualitative
# norm patterns — not NHST p < 0.05. This is the right criterion because the RL
# pipeline needs to identify *which region of the 2-simplex* the true distribution
# falls in, not whether a linear coefficient is non-zero.
#
# Five patterns (rows of the simplex triangle):
#   mostly_negative  — norm violation     (.65, .25, .10)
#   mostly_positive  — norm endorsed      (.10, .25, .65)
#   mostly_neutral   — no strong norm     (.15, .70, .15)
#   polarized        — contested norm     (.40, .15, .40)
#   flat             — indifference/noise (.33, .33, .33)
#
# Method:
#   1. Draw true (p−, p0, p+) from a Dirichlet prior for the target pattern.
#   2. Simulate N trinomial responses (= N participants rating one item).
#   3. Conjugate posterior update: Dirichlet(1,1,1) + counts.
#   4. Classify posterior by which region holds > threshold of posterior mass.
#   5. Power = proportion of simulations correctly classified.
#
# Run from project root:
#   Rscript statistics/power-analysis/power_sim_dirichlet.R
#
# Required packages:
#   install.packages(c("gtools","dplyr","tidyr","purrr","ggplot2","scales"))

suppressPackageStartupMessages({
  library(gtools)   # rdirichlet
  library(dplyr)
  library(tidyr)
  library(purrr)
  library(ggplot2)
  library(scales)
})

set.seed(2025)

OUT_DIR    <- "./"
N_SIM      <- 1000L
N_POST     <- 2000L   # posterior samples per simulation
POWER_MIN  <- 0.80
THRESHOLD  <- 0.85    # minimum posterior mass required for unambiguous classification

# ── 1. Norm pattern priors (Dirichlet concentration params) ───────────────────
# Order: (negative, neutral, positive)
# These encode the qualitative shape; higher sum = more concentrated prior.

PATTERNS <- list(
  mostly_negative = c(6, 2, 1),
  mostly_positive = c(1, 2, 6),
  mostly_neutral  = c(1, 6, 1),
  polarized       = c(4, 1, 4),
  flat            = c(2, 2, 2)
)

# Hard boundary pairs: midpoint alphas between neighboring patterns.
# These are the worst-case inputs; power here sets the binding minimum N.
BOUNDARY_PAIRS <- list(
  flat_vs_neutral    = (PATTERNS$flat       + PATTERNS$mostly_neutral) / 2,
  flat_vs_polarized  = (PATTERNS$flat       + PATTERNS$polarized)      / 2,
  neg_vs_polarized   = (PATTERNS$mostly_negative + PATTERNS$polarized) / 2
)

# ── 2. Pattern classifier ──────────────────────────────────────────────────────
# Returns the classified label or "ambiguous" / "flat".
# post_samples: matrix [N_POST × 3], columns = (p−, p0, p+)

classify_pattern <- function(post_samples, threshold = THRESHOLD) {
  p_neg <- mean(post_samples[, 1] > 0.45)
  p_pos <- mean(post_samples[, 3] > 0.45)
  p_neu <- mean(post_samples[, 2] > 0.45)
  # polarized: neutral suppressed AND both directional categories substantial
  # drops the |p- - p+| < 0.15 balance requirement — too restrictive for Dirichlet(4,1,4)
  p_pol <- mean(post_samples[, 2] < 0.25 &
                  post_samples[, 1] > 0.30 &
                  post_samples[, 3] > 0.30)
  # flat: neutral is present but NOT dominant (0.20 < p0 < 0.45), neither extreme dominates
  # upper bound p0 < 0.45 prevents capturing the mostly_neutral region
  # lower bound p0 > 0.20 prevents capturing the polarized region (where p0 < 0.25)
  p_flat <- mean(post_samples[, 2] > 0.20 &
                   post_samples[, 2] < 0.45 &
                   post_samples[, 1] < 0.50 &
                   post_samples[, 3] < 0.50)

  probs <- c(
    mostly_negative = p_neg,
    mostly_positive = p_pos,
    mostly_neutral  = p_neu,
    polarized       = p_pol,
    flat            = p_flat
  )

  if (max(probs) >= threshold) names(which.max(probs))
  else "ambiguous"
}

# ── 3. Single replication ──────────────────────────────────────────────────────

run_sim <- function(true_alpha, n, n_post = N_POST) {
  # Draw true p from Dirichlet prior, generate trinomial data, update posterior
  true_p     <- rdirichlet(1, true_alpha)
  counts     <- as.vector(rmultinom(1, size = n, prob = true_p))
  post_alpha <- c(1, 1, 1) + counts
  post_samp  <- rdirichlet(n_post, post_alpha)
  classify_pattern(post_samp)
}

# ── 4. Power sweep over patterns ───────────────────────────────────────────────

N_GRID <- c(20L, 30L, 40L, 50L, 60L, 75L, 100L, 150L, 200L)

message("Running pattern-classification power simulation …")
message("  ", length(PATTERNS), " patterns × ", length(N_GRID),
        " N values × ", N_SIM, " reps = ",
        length(PATTERNS) * length(N_GRID) * N_SIM, " simulations")

pattern_results <- expand_grid(
  pattern = names(PATTERNS),
  n       = N_GRID
) |>
  mutate(
    sims = map2(pattern, n, function(pat, n) {
      message("  ", pat, " N=", n, appendLF = FALSE)
      res <- replicate(N_SIM, run_sim(PATTERNS[[pat]], n))
      message("  done")
      res
    }),
    power       = map2_dbl(sims, pattern, ~ mean(.x == .y)),
    ambig_rate  = map_dbl(sims, ~ mean(.x == "ambiguous"))
  ) |>
  select(-sims)

# ── 5. Boundary-pair power sweep ───────────────────────────────────────────────
# For each boundary, the "target" label is the intended pattern; we test whether
# the classifier correctly identifies it even at the boundary.
# Target pattern = the first-named member of the pair (closest true alpha).

boundary_targets <- list(
  flat_vs_neutral   = "mostly_neutral",
  flat_vs_polarized = "polarized",
  neg_vs_polarized  = "mostly_negative"
)

message("\nRunning boundary-pair simulations …")

boundary_results <- expand_grid(
  pair = names(BOUNDARY_PAIRS),
  n    = N_GRID
) |>
  mutate(
    pattern     = map_chr(pair, ~ boundary_targets[[.x]]),
    sims        = map2(pair, n, function(pr, n) {
      message("  boundary: ", pr, " N=", n, appendLF = FALSE)
      res <- replicate(N_SIM, run_sim(BOUNDARY_PAIRS[[pr]], n))
      message("  done")
      res
    }),
    power      = map2_dbl(sims, pattern, ~ mean(.x == .y)),
    ambig_rate = map_dbl(sims, ~ mean(.x == "ambiguous"))
  ) |>
  select(-sims)

# ── 6. Save results ────────────────────────────────────────────────────────────

# write.csv(pattern_results,  file.path(OUT_DIR, "dirichlet_pattern_power.csv"),  row.names = FALSE)
# write.csv(boundary_results, file.path(OUT_DIR, "dirichlet_boundary_power.csv"), row.names = FALSE)

write.csv(pattern_results,  "dirichlet_pattern_power.csv",  row.names = FALSE)
write.csv(boundary_results, "dirichlet_boundary_power.csv", row.names = FALSE)
message("\nResults saved.")

# ── 7. Minimum-N recommendation ────────────────────────────────────────────────

min_n_for <- function(df) {
  df |>
    group_by(pattern) |>
    summarise(
      min_n = {
        rows <- cur_data()[cur_data()$power >= POWER_MIN, ]
        if (nrow(rows) == 0L) NA_integer_ else min(rows$n)
      },
      .groups = "drop"
    )
}

min_n_patterns  <- min_n_for(pattern_results)
min_n_boundary  <- min_n_for(boundary_results)

binding_patterns <- max(min_n_patterns$min_n,  na.rm = TRUE)
binding_boundary <- max(min_n_boundary$min_n,  na.rm = TRUE)
binding_overall  <- max(binding_patterns, binding_boundary)

message("\n── Min N per standard pattern (80% correct classification) ────────")
print(as.data.frame(min_n_patterns))

message("\n── Min N per boundary pair (80% correct classification) ───────────")
print(as.data.frame(min_n_boundary))

message("\nBinding N (standard patterns): ", binding_patterns)
message("Binding N (boundary cases):    ", binding_boundary)
message("Overall binding minimum N:     ", binding_overall)
message("Prolific cost @ £3.00/participant: £", binding_overall * 3.00)

# ── 8. Power curves — standard patterns ────────────────────────────────────────

p_patterns <- ggplot(pattern_results,
                     aes(x = n, y = power, colour = pattern)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2) +
  geom_hline(yintercept = POWER_MIN, linetype = "longdash",
             colour = "grey35", linewidth = 0.45) +
  annotate("text", x = min(N_GRID) + 1, y = POWER_MIN + 0.04,
           label = "80%", colour = "grey35", size = 3, hjust = 0) +
  scale_y_continuous(limits = c(0, 1), labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = N_GRID) +
  labs(
    title    = "Norm-pattern classification power — COGEMI v2",
    subtitle = paste0(N_SIM, " reps/N; Dirichlet-multinomial; threshold = ",
                      THRESHOLD),
    x        = "Participants per item (N)",
    y        = "Correct classification rate",
    colour   = "Norm pattern"
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom")

ggsave(file.path(OUT_DIR, "pattern_classification_power.pdf"),
       p_patterns, width = 8, height = 5)

# ── 9. Power curves — boundary pairs ───────────────────────────────────────────

p_boundary <- ggplot(boundary_results,
                     aes(x = n, y = power, colour = pair)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2) +
  geom_hline(yintercept = POWER_MIN, linetype = "longdash",
             colour = "grey35", linewidth = 0.45) +
  annotate("text", x = min(N_GRID) + 1, y = POWER_MIN + 0.04,
           label = "80%", colour = "grey35", size = 3, hjust = 0) +
  scale_y_continuous(limits = c(0, 1), labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = N_GRID) +
  labs(
    title    = "Boundary-case classification power — COGEMI v2",
    subtitle = "Worst-case: true alpha at midpoint between adjacent patterns",
    x        = "Participants per item (N)",
    y        = "Correct classification rate",
    colour   = "Boundary pair"
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom")

ggsave(file.path(OUT_DIR, "boundary_classification_power.pdf"),
       p_boundary, width = 8, height = 5)

# ── 10. Ambiguity rate plot ────────────────────────────────────────────────────

ambig_data <- bind_rows(
  mutate(pattern_results, source = "standard"),
  mutate(boundary_results, source = "boundary")
)

p_ambig <- ggplot(ambig_data, aes(x = n, y = ambig_rate,
                                   colour = pattern, linetype = source)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 1.8) +
  scale_y_continuous(limits = c(0, 1), labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = N_GRID) +
  labs(
    title    = "Ambiguity rate — COGEMI v2",
    subtitle = "Items landing in no clear region; useful as a per-item quality flag",
    x        = "Participants per item (N)",
    y        = "Ambiguity rate",
    colour   = "Pattern",
    linetype = "Case"
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom")

ggsave(file.path(OUT_DIR, "ambiguity_rate.pdf"),
       p_ambig, width = 8, height = 5)

message("\nSaved: pattern_classification_power.pdf, boundary_classification_power.pdf,",
        " ambiguity_rate.pdf")
message("Done.  Overall binding minimum N = ", binding_overall)
