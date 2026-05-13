#library(lme4)
library(lmerTest)
library(simr)
library(dplyr)
library(tidyr)

set.seed(1)

make_design <- function(n_participants,
                        n_vignettes = 47) {
  
  expand_grid(
    participant_id = factor(seq_len(n_participants)),
    vignette_id    = factor(seq_len(n_vignettes))
  ) |>
    mutate(
      agent_gender = sample(c("female", "male"), n(), replace = TRUE),
      relationship = sample(c("friend", "stranger", "authority"), n(), replace = TRUE),
      setting      = sample(c("private", "public"), n(), replace = TRUE),
      stakes       = sample(c("low", "high"), n(), replace = TRUE)
    )
}

## more conservative hyperparams
simulate_data <- function(n_participants,
                          beta_stakes = 0.05,
                          sd_participant = 1.0,
                          sd_vignette = 0.8,
                          sd_error = 1.5) {
  
  dat <- make_design(n_participants)
  
  participant_effects <- rnorm(n_participants, 0, sd_participant)
  vignette_effects    <- rnorm(47, 0, sd_vignette)
  
  dat <- dat |>
    mutate(
      stakes_num = ifelse(stakes == "high", 0.5, -0.5),
      
      eta =
        3 +
        beta_stakes * stakes_num +
        participant_effects[participant_id] +
        vignette_effects[vignette_id],
      
      rating =
        pmin(5, pmax(1,
                     round(rnorm(n(), eta, sd_error))
        ))
    )
  
  dat
}

dat <- simulate_data(n_participants = 100)

m <- lmer(
  rating ~ stakes + agent_gender + relationship + setting +
    (1 | participant_id) +
    (1 | vignette_id),
  data = dat
)

summary(m)

# Then estimate power across participant numbers:

power_for_n <- function(n_participants, nsim = 200) {
  
  pvals <- replicate(nsim, {
    dat <- simulate_data(n_participants)
    
    m <- lmer(
      rating ~ stakes + agent_gender + relationship + setting +
        (1 | participant_id) +
        (1 | vignette_id),
      data = dat
    )
    coef(summary(m))["stakeslow", "Pr(>|t|)"] 
    #coef(summary(m))["stakeslow", "t value"]
  })
  
  mean(pvals < 0.05, na.rm = TRUE)
}

#Ns <- seq(25, 400, by = 25)
Ns <- seq(500, 1100, by =100)

power_curve <- data.frame(
  N = Ns,
  power = sapply(Ns, power_for_n, nsim = 200)
)

power_curve


plot(power_curve$N, power_curve$power, type = "b",
     xlab = "Number of participants",
     ylab = "Estimated power")
abline(h = 0.80, lty = 2)
