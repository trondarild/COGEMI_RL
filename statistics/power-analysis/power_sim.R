# statistics/power-analysis/power_sim.R
#
# Minimum-N power simulation for the COGEMI v2 appropriateness survey.
#
# Survey structure modelled here:
#   - 42 main vignettes + 5 test-retest vignettes (= 47 total per participant)
#   - Per vignette: Q1 personal appropriateness, Q2 injunctive norm,
#     Q3 realism/frequency, Q4 certainty, Q5 perceived disagreement (all 1–5)
#   - Intra-item consistency block: 5 rewordings of one Q1 item
#   - Contextual factorial: setting × relationship × stakes (randomised across vignettes)
#
# Goal: find the smallest N where key effects reach 80% power.
#
# Run from project root:
#   Rscript statistics/power-analysis/power_sim.R
#
# Required packages:
#   install.packages(c("lme4","lmerTest","performance","dplyr","tidyr","purrr","ggplot2","scales"))

suppressPackageStartupMessages({
  library(lme4)
  library(lmerTest)    # Satterthwaite p-values for lmer
  library(performance) # ICC
  library(dplyr)
  library(tidyr)
  library(purrr)
  library(ggplot2)
  library(scales)
})

set.seed(2025)

OUT_DIR   <- "statistics/power-analysis"
N_SIMS    <- 500L    # reps per N; gives ±4.5% CI on power at p=0.80
ALPHA     <- 0.05
N_GRID    <- c(20L, 30L, 40L, 50L, 60L, 75L, 100L)
POWER_MIN <- 0.80

# ── 1. DGM parameters ──────────────────────────────────────────────────────────

N_MAIN   <- 42L
N_RETEST <- 5L
N_REWORD <- 5L

SD_P   <- 0.6    # between-participant random intercept SD
SD_V   <- 0.8    # between-vignette random intercept SD
SD_E   <- 0.7    # within-cell residual SD
SD_TOT <- sqrt(SD_P^2 + SD_V^2 + SD_E^2)  # ≈ 1.22; used to express d in Likert units

# Medium effect sizes (Cohen's d ≈ 0.30–0.50), typical for norm/context research
BETA_MED <- list(
  setting_public = 0.40 * SD_TOT,   # public vs private (reference level)
  rel_friend     = 0.50 * SD_TOT,   # friend    vs stranger (reference)
  rel_auth       = -0.30 * SD_TOT,  # authority vs stranger
  stakes_high    = 0.30 * SD_TOT,   # high vs low stakes (reference)
  q1_q2_offset   = -0.30            # perceived injunctive norm pulled below personal
)

# Intra-item SD: derived from target ICC = sigma_P^2 / (sigma_P^2 + sigma_reword^2)
ICC_REWORD_TARGET <- 0.80
SD_REWORD_NOISE   <- SD_P * sqrt((1 - ICC_REWORD_TARGET) / ICC_REWORD_TARGET)

# ── 2. Vignette design ─────────────────────────────────────────────────────────

make_vd <- function(n = N_MAIN) {
  cells <- expand.grid(
    setting      = c("private", "public"),
    relationship = c("stranger", "friend", "authority"),
    stakes       = c("low", "high"),
    stringsAsFactors = FALSE
  )
  idx <- rep_len(seq_len(nrow(cells)), n)
  vd  <- cells[idx, , drop = FALSE]
  vd$vignette_id <- paste0("v", seq_len(n))
  rownames(vd) <- NULL
  vd
}

# ── 3. Data simulation ─────────────────────────────────────────────────────────

clip5 <- function(x) pmin(5L, pmax(1L, as.integer(round(x))))

simulate_survey <- function(n_p, vd, beta) {
  n_v <- nrow(vd)
  u_p <- rnorm(n_p, 0, SD_P)
  u_v <- rnorm(n_v, 0, SD_V)

  # Latent mean per vignette (fixed effects)
  fe <- 3 +
        beta$setting_public * (vd$setting      == "public") +
        beta$rel_friend     * (vd$relationship == "friend") +
        beta$rel_auth       * (vd$relationship == "authority") +
        beta$stakes_high    * (vd$stakes       == "high")

  n_obs <- n_p * n_v
  pi    <- rep(seq_len(n_p), each  = n_v)
  vi    <- rep(seq_len(n_v), times = n_p)

  lat <- fe[vi] + u_p[pi] + u_v[vi] + rnorm(n_obs, 0, SD_E)

  tibble(
    participant_id = pi,
    vignette_id    = vd$vignette_id[vi],
    setting        = factor(vd$setting[vi],      levels = c("private",  "public")),
    relationship   = factor(vd$relationship[vi], levels = c("stranger", "friend", "authority")),
    stakes         = factor(vd$stakes[vi],       levels = c("low",      "high")),
    # Q1: personal appropriateness
    q1 = clip5(lat),
    # Q2: injunctive norm — offset varies by vignette (realistic: some vignettes
    # show larger personal-vs-injunctive gap than others); constant offset would
    # make this trivially detectable by averaging over 42 vignettes
    q2 = clip5(lat + rnorm(n_v, beta$q1_q2_offset, abs(beta$q1_q2_offset))[vi] +
                 rnorm(n_obs, 0, 0.4)),
    # Q3: realism / frequency — independently distributed
    q3 = clip5(rnorm(n_obs, 3, 1)),
    # Q4: certainty — increases with extremity of Q1
    q4 = clip5(3 + 0.4 * abs(lat - 3) + rnorm(n_obs, 0, 0.5)),
    # Q5: perceived disagreement — decreases with extremity of Q1
    q5 = clip5(3 - 0.3 * abs(lat - 3) + rnorm(n_obs, 0, 0.6))
  )
}

simulate_retest <- function(main_data) {
  # Same 5 vignettes re-rated at end of session; small additional noise
  main_data |>
    filter(vignette_id %in% paste0("v", seq_len(N_RETEST))) |>
    mutate(q1 = clip5(q1 + rnorm(n(), 0, SD_E * 0.5)))
}

simulate_reword <- function(n_p) {
  # N_REWORD paraphrases of one Q1 item per participant
  u_p <- rnorm(n_p, 0, SD_P)
  expand.grid(participant_id = seq_len(n_p), reword = seq_len(N_REWORD)) |>
    as_tibble() |>
    mutate(q1_reword = clip5(3 + u_p[participant_id] + rnorm(n(), 0, SD_REWORD_NOISE)))
}

# ── 4. Statistical analysis per dataset ────────────────────────────────────────

# Returns p-values for the four main contextual fixed effects (Q1 ~ lmer)
extract_context_pvals <- function(main_data) {
  fit <- tryCatch(
    lmer(q1 ~ setting + relationship + stakes +
           (1 | participant_id) + (1 | vignette_id),
         data = main_data, REML = FALSE,
         control = lmerControl(optimizer = "bobyqa")),
    error = function(e) NULL
  )
  if (is.null(fit)) return(setNames(rep(NA_real_, 4L),
    c("p_setting", "p_rel_friend", "p_rel_auth", "p_stakes")))

  cs <- tryCatch(coef(summary(fit)), error = function(e) NULL)
  if (is.null(cs)) return(setNames(rep(NA_real_, 4L),
    c("p_setting", "p_rel_friend", "p_rel_auth", "p_stakes")))

  p <- cs[, "Pr(>|t|)"]
  c(
    p_setting    = unname(p[grep("settingpublic",      names(p))[1]]),
    p_rel_friend = unname(p[grep("friend",             names(p))[1]]),
    p_rel_auth   = unname(p[grep("authority",          names(p))[1]]),
    p_stakes     = unname(p[grep("stakeshigh",         names(p))[1]])
  )
}

# Mixed model intercept test on (Q1 - Q2): accounts for participant and vignette
# random effects; more conservative than paired t-test because vignette-level
# variation in the offset is now modelled explicitly
q1q2_pval <- function(main_data) {
  tryCatch({
    fit <- lmer(I(q1 - q2) ~ 1 + (1 | participant_id) + (1 | vignette_id),
                data = main_data, REML = FALSE,
                control = lmerControl(optimizer = "bobyqa"))
    coef(summary(fit))["(Intercept)", "Pr(>|t|)"]
  }, error = function(e) NA_real_)
}

# Pearson r between first and retest ratings of the same 5 vignettes
retest_r <- function(main_data, retest_data) {
  tryCatch({
    a <- main_data |>
      filter(vignette_id %in% paste0("v", seq_len(N_RETEST))) |>
      select(participant_id, vignette_id, q1a = q1)
    b <- retest_data |> select(participant_id, vignette_id, q1b = q1)
    cor(inner_join(a, b, by = c("participant_id", "vignette_id"))$q1a,
        inner_join(a, b, by = c("participant_id", "vignette_id"))$q1b)
  }, error = function(e) NA_real_)
}

# ICC from variance components (VarCorr) — avoids performance::icc() which
# behaves unexpectedly when clip5 truncation biases variance estimates with large N
reword_icc_val <- function(reword_data) {
  tryCatch({
    fit  <- lmer(q1_reword ~ 1 + (1 | participant_id), data = reword_data,
                 control = lmerControl(optimizer = "bobyqa"))
    vc   <- as.data.frame(VarCorr(fit))
    vp   <- vc[vc$grp == "participant_id", "vcov"]
    vr   <- vc[vc$grp == "Residual",       "vcov"]
    vp / (vp + vr)
  }, error = function(e) NA_real_)
}

# ── 5. One simulation replication ──────────────────────────────────────────────

one_rep <- function(n_p, vd, beta) {
  main   <- simulate_survey(n_p, vd, beta)
  retest <- simulate_retest(main)
  reword <- simulate_reword(n_p)
  pv     <- extract_context_pvals(main)

  tibble(
    n            = n_p,
    p_setting    = pv["p_setting"],
    p_rel_friend = pv["p_rel_friend"],
    p_rel_auth   = pv["p_rel_auth"],
    p_stakes     = pv["p_stakes"],
    p_q1q2       = q1q2_pval(main),
    r_retest     = retest_r(main, retest),
    icc_reword   = reword_icc_val(reword)
  )
}

# ── 6. Power sweep ─────────────────────────────────────────────────────────────

run_sweep <- function(beta, label, vd) {
  message("\n── Scenario: ", label, " ──")
  map_dfr(N_GRID, function(n) {
    message("  N = ", n, appendLF = FALSE)
    res <- map_dfr(seq_len(N_SIMS), \(i) one_rep(n, vd, beta))
    message("  done")
    mutate(res, scenario = label)
  })
}

scale_beta <- function(beta, s) {
  lapply(beta, `*`, s)
}

BETA_SMALL <- scale_beta(BETA_MED, 0.5)   # d ≈ 0.15–0.25
BETA_LARGE <- scale_beta(BETA_MED, 1.5)   # d ≈ 0.45–0.75

vd_fixed <- make_vd()  # one design reused across all scenarios

message("Starting power simulation: ",
        length(N_GRID), " N values × 3 scenarios × ", N_SIMS, " reps")
message("Approx. total model fits: ", length(N_GRID) * 3L * N_SIMS)

all_raw <- bind_rows(
  run_sweep(BETA_MED,   "medium", vd_fixed),
  run_sweep(BETA_SMALL, "small",  vd_fixed),
  run_sweep(BETA_LARGE, "large",  vd_fixed)
)

write.csv(all_raw, file.path(OUT_DIR, "power_sim_results_raw.csv"), row.names = FALSE)
message("\nRaw results saved.")

# ── 7. Summary table ───────────────────────────────────────────────────────────

power_summary <- all_raw |>
  group_by(n, scenario) |>
  summarise(
    power_setting    = mean(p_setting    < ALPHA, na.rm = TRUE),
    power_rel_friend = mean(p_rel_friend < ALPHA, na.rm = TRUE),
    power_rel_auth   = mean(p_rel_auth   < ALPHA, na.rm = TRUE),
    power_stakes     = mean(p_stakes     < ALPHA, na.rm = TRUE),
    power_q1q2       = mean(p_q1q2       < ALPHA, na.rm = TRUE),
    median_r_retest   = median(r_retest,   na.rm = TRUE),
    pct_retest_ok     = mean(r_retest    >= 0.70, na.rm = TRUE),
    median_icc_reword = median(icc_reword, na.rm = TRUE),
    pct_reword_ok     = mean(icc_reword  >= 0.70, na.rm = TRUE),
    .groups = "drop"
  )

write.csv(power_summary, file.path(OUT_DIR, "power_sim_results.csv"), row.names = FALSE)

message("\n── Power summary (medium scenario) ────────────────────────────────")
print(as.data.frame(filter(power_summary, scenario == "medium")), digits = 2)

# ── 8. Minimum-N recommendation ────────────────────────────────────────────────

med <- filter(power_summary, scenario == "medium")
effect_cols <- c("power_setting", "power_rel_friend", "power_rel_auth",
                 "power_stakes",  "power_q1q2")
effect_names <- c("Setting (public/private)", "Relationship: friend",
                  "Relationship: authority",  "Stakes (low/high)",
                  "Q1–Q2 divergence")

min_n_tbl <- tibble(
  effect  = effect_names,
  min_n   = map_int(effect_cols, function(col) {
    rows <- med[med[[col]] >= POWER_MIN, ]
    if (nrow(rows) == 0L) return(NA_integer_)
    min(rows$n)
  })
)

binding_n <- max(min_n_tbl$min_n, na.rm = TRUE)

message("\n── Minimum N per effect (80% power, medium effects) ───────────────")
print(as.data.frame(min_n_tbl))
message("\nBinding minimum N: ", binding_n)
message("Estimated Prolific cost @ £3.00/participant: £", binding_n * 3.00)
message("
NOTE — between-vignette design:
Setting, relationship, and stakes are vignette-level predictors. Their power
ceiling is determined by N_vignettes per condition (~21 per setting level,
~14 per relationship level), NOT by N_participants. Adding participants beyond
N=30 does not increase power for these effects. To reach 80% power for
contextual effects you need more vignettes per cell (see section 11 below).")

# ── 9. Power curves ─────────────────────────────────────────────────────────────

label_map <- setNames(effect_names, effect_cols)

plot_power <- power_summary |>
  select(n, scenario, all_of(effect_cols)) |>
  pivot_longer(all_of(effect_cols), names_to = "effect", values_to = "power") |>
  mutate(
    effect   = recode(effect, !!!label_map),
    scenario = factor(scenario, levels = c("small", "medium", "large"),
                      labels = c("Small (d≈0.15–0.25)",
                                 "Medium (d≈0.30–0.50)",
                                 "Large (d≈0.45–0.75)"))
  )

p_power <- ggplot(plot_power, aes(x = n, y = power, colour = effect)) +
  geom_line(linewidth = 0.85) +
  geom_point(size = 1.8) +
  geom_hline(yintercept = POWER_MIN, linetype = "longdash",
             colour = "grey35", linewidth = 0.45) +
  annotate("text", x = min(N_GRID) + 1, y = POWER_MIN + 0.04,
           label = "80%", colour = "grey35", size = 3, hjust = 0) +
  scale_y_continuous(limits = c(0, 1), labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = N_GRID) +
  facet_wrap(~scenario) +
  labs(
    title    = "Power curves — COGEMI v2 survey",
    subtitle = paste0("47 vignettes; ", N_SIMS, " reps/N; α = ", ALPHA,
                      "; lmerTest (Satterthwaite df); Q1 treated as continuous"),
    x        = "Participants (N)",
    y        = "Statistical power",
    colour   = NULL
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position  = "bottom",
        legend.key.width = unit(1.5, "cm"),
        strip.text       = element_text(face = "bold"))

ggsave(file.path(OUT_DIR, "power_curves.pdf"), p_power, width = 11, height = 5.5)
message("Saved power_curves.pdf")

# ── 10. Reliability curves (medium scenario only) ──────────────────────────────

plot_rel <- filter(power_summary, scenario == "medium") |>
  select(n, median_r_retest, pct_retest_ok, median_icc_reword, pct_reword_ok) |>
  pivot_longer(-n, names_to = "metric", values_to = "value") |>
  mutate(metric = recode(metric,
    "median_r_retest"   = "Median retest r (5 vignettes)",
    "pct_retest_ok"     = "Pr(retest r ≥ 0.70)",
    "median_icc_reword" = "Median ICC (5 rewordings)",
    "pct_reword_ok"     = "Pr(reword ICC ≥ 0.70)"
  ))

p_rel <- ggplot(plot_rel, aes(x = n, y = value, colour = metric)) +
  geom_line(linewidth = 0.85) +
  geom_point(size = 1.8) +
  geom_hline(yintercept = 0.70, linetype = "longdash",
             colour = "grey35", linewidth = 0.45) +
  annotate("text", x = min(N_GRID) + 1, y = 0.72,
           label = "r / ICC = 0.70", colour = "grey35", size = 3, hjust = 0) +
  scale_y_continuous(limits = c(0, 1)) +
  scale_x_continuous(breaks = N_GRID) +
  labs(
    title    = "Reliability as a function of N — COGEMI v2",
    subtitle = paste0("Medium effects; ", N_SIMS, " reps/N"),
    x        = "Participants (N)",
    y        = "Value",
    colour   = NULL
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom")

ggsave(file.path(OUT_DIR, "reliability_curves.pdf"), p_rel, width = 7, height = 5)
message("Saved reliability_curves.pdf")

# ── 11. Vignettes-per-cell sweep (N_participants fixed) ────────────────────────
# Contextual effects are between-vignette: power scales with N_vignettes per
# condition, not N_participants. This sweep shows the vignette requirement.

VPC_GRID  <- c(3L, 5L, 7L, 10L, 15L, 20L)   # vignettes per cell
N_P_FIXED <- 50L                              # held at Dirichlet recommendation
N_CELLS   <- 12L                              # 2×3×2 factorial

message("\n── Vignettes-per-cell sweep (N_participants = ", N_P_FIXED, " fixed) ──")

vpc_raw <- map_dfr(VPC_GRID, function(vpc) {
  vd_vpc <- make_vd(n = vpc * N_CELLS)
  message("  vpc = ", vpc, appendLF = FALSE)
  res <- map_dfr(seq_len(N_SIMS), function(i) {
    main <- simulate_survey(N_P_FIXED, vd_vpc, BETA_MED)
    pv   <- extract_context_pvals(main)
    tibble(vpc = vpc,
           p_setting    = pv["p_setting"],
           p_rel_friend = pv["p_rel_friend"],
           p_rel_auth   = pv["p_rel_auth"],
           p_stakes     = pv["p_stakes"])
  })
  message("  done")
  res
})

vpc_summary <- vpc_raw |>
  group_by(vpc) |>
  summarise(
    power_setting    = mean(p_setting    < ALPHA, na.rm = TRUE),
    power_rel_friend = mean(p_rel_friend < ALPHA, na.rm = TRUE),
    power_rel_auth   = mean(p_rel_auth   < ALPHA, na.rm = TRUE),
    power_stakes     = mean(p_stakes     < ALPHA, na.rm = TRUE),
    .groups = "drop"
  )

write.csv(vpc_summary, file.path(OUT_DIR, "contextual_power_by_nvignettes.csv"),
          row.names = FALSE)

message("\n── Contextual effects: min vignettes/cell for 80% power ───────────")
vpc_effects <- c("power_setting", "power_rel_friend", "power_rel_auth", "power_stakes")
vpc_names   <- c("Setting", "Rel: friend", "Rel: authority", "Stakes")
min_vpc_tbl <- tibble(
  effect    = vpc_names,
  min_vpc   = map_int(vpc_effects, function(col) {
    rows <- vpc_summary[vpc_summary[[col]] >= POWER_MIN, ]
    if (nrow(rows) == 0L) return(NA_integer_)
    min(rows$vpc)
  })
)
print(as.data.frame(min_vpc_tbl))
message("(Current survey has ~3.5 vignettes/cell with 42 vignettes in 12 cells)")

plot_vpc <- vpc_summary |>
  pivot_longer(all_of(vpc_effects), names_to = "effect", values_to = "power") |>
  mutate(effect = recode(effect, !!!setNames(vpc_names, vpc_effects)))

p_vpc <- ggplot(plot_vpc, aes(x = vpc, y = power, colour = effect)) +
  geom_line(linewidth = 0.85) +
  geom_point(size = 1.8) +
  geom_hline(yintercept = POWER_MIN, linetype = "longdash",
             colour = "grey35", linewidth = 0.45) +
  annotate("text", x = min(VPC_GRID) + 0.2, y = POWER_MIN + 0.04,
           label = "80%", colour = "grey35", size = 3, hjust = 0) +
  scale_y_continuous(limits = c(0, 1), labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = VPC_GRID) +
  labs(
    title    = "Contextual-effect power by vignettes per cell",
    subtitle = paste0("N_participants = ", N_P_FIXED, " fixed; medium effects; ",
                      N_SIMS, " reps; vertical axis: power for between-vignette contrast"),
    x        = "Vignettes per contextual cell",
    y        = "Statistical power",
    colour   = NULL
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom")

ggsave(file.path(OUT_DIR, "contextual_power_by_nvignettes.pdf"),
       p_vpc, width = 7, height = 5)
message("Saved contextual_power_by_nvignettes.pdf")
message("\nDone. Binding participant N = ", binding_n,
        "; contextual effects need ~", max(min_vpc_tbl$min_vpc, na.rm = TRUE),
        " vignettes/cell for 80% power.")
