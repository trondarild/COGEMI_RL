# statistics/power-analysis/power-analysis-visualisation.R
#
# Four-panel Nature-style figure summarising the COGEMI v2 survey power analysis.
# Reads actual simulation output; no re-simulation needed.
#
# Run from project root:
#   Rscript statistics/power-analysis/power-analysis-visualisation.R
#
# Requires: ggplot2, dplyr, tidyr, patchwork, ggtext, grid

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(patchwork)
  library(ggtext)   # element_markdown for italic axis labels
  library(grid)     # unit()
})

OUT_DIR <- "statistics/power-analysis"

# ── Palette (Nature-style muted) ──────────────────────────────────────────────
COL <- list(
  teal   = "#1b7a6e",
  amber  = "#d9692a",
  blue   = "#3a5e9e",
  grey   = "#8a8a8a",
  lgrey  = "#d4d4d4",
  black  = "#1a1a1a",
  bg     = "#ffffff",
  hilite = "#e8f4f2"   # faint teal for table highlight rows
)

BASE_THEME <- theme_classic(base_size = 9, base_family = "Helvetica") +
  theme(
    plot.background   = element_rect(fill = COL$bg, colour = NA),
    panel.background  = element_rect(fill = COL$bg, colour = NA),
    axis.line         = element_line(colour = COL$black, linewidth = 0.35),
    axis.ticks        = element_line(colour = COL$black, linewidth = 0.35),
    axis.ticks.length = unit(2.5, "pt"),
    axis.text         = element_text(colour = COL$black, size = 7.5),
    axis.title        = element_text(colour = COL$black, size = 8.5),
    plot.title        = element_text(face = "bold", size = 9, colour = COL$black,
                                     margin = margin(b = 4)),
    plot.tag          = element_text(face = "bold", size = 10, colour = COL$black),
    legend.background = element_rect(fill = NA, colour = NA),
    legend.key        = element_rect(fill = NA, colour = NA),
    legend.text       = element_text(size = 7.5),
    legend.key.size   = unit(10, "pt"),
    panel.grid        = element_blank()
  )

# ── Data ──────────────────────────────────────────────────────────────────────

vpc_file  <- file.path(OUT_DIR, "contextual_power_by_nvignettes.csv")
sim_file  <- file.path(OUT_DIR, "power_sim_results.csv")

vpc  <- read.csv(vpc_file)
sim  <- read.csv(sim_file)

# ── Panel A: Design hierarchy (schematic via geom_rect / geom_segment) ────────

make_panel_a <- function() {

  # Tier boxes: xmin, xmax, ymin, ymax, fill, label, sublabel
  boxes <- tibble(
    xmin  = c(0.05, 0.05, 0.05, 0.55),
    xmax  = c(0.95, 0.95, 0.48, 0.95),
    ymin  = c(0.68, 0.35, 0.03, 0.03),
    ymax  = c(0.97, 0.64, 0.30, 0.30),
    fill  = c(COL$teal, COL$amber, COL$blue, COL$grey),
    alpha = c(0.15, 0.15, 0.15, 0.12)
  )

  tier_labels <- tibble(
    x     = c(0.50, 0.50, 0.265, 0.755),
    y     = c(0.925, 0.595, 0.270, 0.270),
    label = c(
      "Vignette pool  (120 total)",
      "Participant session  (42 vignettes/person)",
      "Agent identity variants",
      "Role perspective arms"
    ),
    col   = c(COL$teal, COL$amber, COL$blue, COL$grey),
    bold  = c(TRUE, TRUE, TRUE, TRUE)
  )

  sub_labels <- tibble(
    x     = c(0.50, 0.50, 0.265, 0.755),
    y     = c(0.855, 0.505, 0.175, 0.155),
    label = c(
      "12 structural cells: Setting x Relationship x Stakes  (2x3x2)",
      "Random 42-item subset per participant -- incomplete block design\n~21 ratings/vignette at N = 60",
      "Gender x Role -- text swap\nwithin vignette; no new vignettes",
      "Agent / Target / Observer\n3 Prolific arms x 60 participants = 180 total"
    ),
    col   = c(COL$black, COL$black, COL$black, COL$black)
  )

  # Arrow segments between tiers
  arrows <- tibble(
    x    = c(0.50, 0.265, 0.755),
    xend = c(0.50, 0.265, 0.755),
    y    = c(0.68, 0.35,  0.35),
    yend = c(0.645, 0.305, 0.305)
  )

  arrow_labels <- tibble(
    x     = c(0.62, 0.42),
    y     = c(0.662, 0.328),
    label = c("random 42-item block", "between-participant assignment"),
    col   = COL$grey
  )

  # 12-cell mini-grid inside Tier 1
  cell_grid <- expand.grid(gx = 1:4, gy = 1:3) %>%
    mutate(
      cx = 0.58 + (gx - 1) * 0.065,
      cy = 0.73 + (gy - 1) * 0.033
    )

  p <- ggplot() +
    # Tier boxes
    geom_rect(data = boxes,
              aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax,
                  fill = fill, alpha = alpha),
              colour = NA, show.legend = FALSE) +
    scale_fill_identity() +
    scale_alpha_identity() +
    # Tier border outlines
    geom_rect(data = boxes,
              aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
              fill = NA,
              colour = c(COL$teal, COL$amber, COL$blue, COL$grey),
              linewidth = 0.5) +
    # Cell grid dots
    geom_point(data = cell_grid,
               aes(x = cx, y = cy),
               colour = COL$teal, size = 1.2, shape = 15) +
    # Arrows
    geom_segment(data = arrows,
                 aes(x = x, xend = xend, y = y, yend = yend),
                 arrow = arrow(length = unit(4, "pt"), type = "closed"),
                 colour = COL$grey, linewidth = 0.4) +
    # Arrow labels
    geom_text(data = arrow_labels,
              aes(x = x, y = y, label = label),
              colour = COL$grey, size = 2.2, hjust = 0) +
    # Tier titles
    geom_text(data = tier_labels,
              aes(x = x, y = y, label = label, colour = col),
              fontface = "bold", size = 2.8, hjust = 0.5,
              show.legend = FALSE) +
    scale_colour_identity() +
    # Sub-labels
    geom_text(data = sub_labels,
              aes(x = x, y = y, label = label),
              colour = COL$black, size = 2.2, hjust = 0.5, lineheight = 1.2) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), clip = "off") +
    labs(title = "Survey design hierarchy", tag = "A") +
    BASE_THEME +
    theme(
      axis.line   = element_blank(),
      axis.text   = element_blank(),
      axis.ticks  = element_blank(),
      axis.title  = element_blank(),
      plot.margin = margin(6, 6, 6, 6)
    )

  p
}

# ── Panel B: Vignettes-per-cell power curves ──────────────────────────────────

make_panel_b <- function() {

  long <- vpc %>%
    pivot_longer(-vpc, names_to = "effect", values_to = "power") %>%
    mutate(effect = recode(effect,
      power_setting   = "Setting (d~0.40)",
      power_rel_friend = "Rel: friend (d~0.50)",
      power_rel_auth  = "Rel: authority (d~0.30)",
      power_stakes    = "Stakes (d~0.30)"
    ),
    effect = factor(effect, levels = c(
      "Setting (d~0.40)",
      "Rel: friend (d~0.50)",
      "Rel: authority (d~0.30)",
      "Stakes (d~0.30)"
    )))

  shapes <- c(16, 15, 17, 18)
  cols   <- c(COL$teal, COL$amber, COL$blue, COL$grey)

  ggplot(long, aes(x = vpc, y = power, colour = effect, shape = effect)) +
    # Reference lines
    geom_hline(yintercept = 0.80, linetype = "dashed",
               colour = COL$grey, linewidth = 0.4) +
    annotate("text", x = 20.4, y = 0.82, label = "80%",
             colour = COL$grey, size = 2.5, hjust = 0) +
    geom_vline(xintercept = 10, linetype = "dashed",
               colour = COL$teal, linewidth = 0.35, alpha = 0.7) +
    annotate("text", x = 10.3, y = 0.10, label = "10 vpc\n120 vignettes",
             colour = COL$teal, size = 2.1, hjust = 0, lineheight = 1.2) +
    geom_vline(xintercept = 20, linetype = "dashed",
               colour = COL$amber, linewidth = 0.35, alpha = 0.7) +
    annotate("text", x = 20.3, y = 0.10, label = "20 vpc\n240 vignettes",
             colour = COL$amber, size = 2.1, hjust = 0, lineheight = 1.2) +
    # Smooth lines + points
    geom_line(linewidth = 0.7) +
    geom_point(size = 2.2, stroke = 0.4) +
    scale_x_continuous(breaks = c(3, 5, 7, 10, 15, 20), expand = expansion(mult = c(0.02, 0.18))) +
    scale_y_continuous(limits = c(0, 1.02), breaks = seq(0, 1, 0.2),
                       labels = scales::percent_format(accuracy = 1),
                       expand = expansion(mult = c(0.01, 0.02))) +
    scale_colour_manual(values = cols, name = NULL) +
    scale_shape_manual(values = shapes, name = NULL) +
    labs(
      title = "Contextual power by vignettes per cell",
      x     = "Vignettes per structural cell (vpc)",
      y     = "Power (1 - beta)",
      tag   = "B"
    ) +
    BASE_THEME +
    theme(
      legend.position  = c(0.03, 0.97),
      legend.justification = c(0, 1),
      legend.spacing.y = unit(1, "pt"),
      plot.margin      = margin(6, 8, 6, 6)
    )
}

# ── Panel C: Participant-level effects bar chart ───────────────────────────────

make_panel_c <- function() {

  # Take median across N values for medium scenario
  med <- sim %>%
    filter(scenario == "medium") %>%
    summarise(
      q1q2  = mean(power_q1q2),
      retest = mean(median_r_retest),
      icc   = mean(median_icc_reword)
    )

  bars <- tibble(
    effect = factor(
      c("Q1-Q2 norm\ndivergence",
        "Test-retest\nreliability (r)",
        "Intra-item\nICC"),
      levels = c("Intra-item\nICC",
                 "Test-retest\nreliability (r)",
                 "Q1-Q2 norm\ndivergence")
    ),
    value = c(med$q1q2, med$retest, med$icc),
    label = c(
      sprintf("%.2f  (N = 20+)", med$q1q2),
      sprintf("median r = %.2f", med$retest),
      sprintf("observable ICC = %.2f", med$icc)
    )
  )

  ggplot(bars, aes(x = value, y = effect)) +
    # Shaded region for "adequate" zone
    annotate("rect", xmin = 0.80, xmax = 1.02, ymin = 0.5, ymax = 3.5,
             fill = COL$teal, alpha = 0.07) +
    # Bars
    geom_col(fill = COL$teal, alpha = 0.85, width = 0.55) +
    # 80% power threshold
    geom_vline(xintercept = 0.80, linetype = "dashed",
               colour = COL$grey, linewidth = 0.4) +
    annotate("text", x = 0.815, y = 3.45, label = "target\n80%",
             colour = COL$grey, size = 2.2, hjust = 0, lineheight = 1.1) +
    # Adjusted ICC threshold
    geom_vline(xintercept = 0.65, linetype = "dotted",
               colour = COL$blue, linewidth = 0.4) +
    annotate("text", x = 0.655, y = 0.68, label = "adjusted ICC\nthreshold (0.65)\n5-pt scale",
             colour = COL$blue, size = 2.0, hjust = 0, lineheight = 1.1) +
    # Value labels on bars
    geom_text(aes(label = label, x = 0.03),
              hjust = 0, size = 2.5, colour = COL$bg) +
    scale_x_continuous(limits = c(0, 1.1),
                       breaks = c(0, 0.2, 0.4, 0.6, 0.8, 1.0),
                       labels = scales::number_format(accuracy = 0.1),
                       expand = expansion(mult = c(0, 0.01))) +
    labs(
      title = "Participant-level effects (N = 20-100)",
      x     = "Power / observed statistic",
      y     = NULL,
      tag   = "C"
    ) +
    BASE_THEME +
    theme(
      axis.line.y  = element_blank(),
      axis.ticks.y = element_blank(),
      plot.margin  = margin(6, 8, 6, 6)
    )
}

# ── Panel D: Recommended sample size table ────────────────────────────────────

make_panel_d <- function() {

  rows <- tibble(
    criterion = c(
      "Dirichlet pattern classification",
      "Q1-Q2 norm divergence",
      "Agent identity (gender x role)",
      "Vignette pool -- main effects (10 vpc)",
      "Vignette pool -- full factorial (20 vpc)",
      "Role perspective arms (x3)",
      "Recommended -- single arm",
      "Recommended -- all three arms"
    ),
    n_label = c(
      "50", "20", "60",
      "120 vignettes", "240 vignettes", "x3 arms",
      "60", "180"
    ),
    source = c(
      "Dirichlet sim", "lmerTest sim", "lmerTest sensitivity",
      "vpc sweep", "vpc sweep", "between-participant",
      "binding", "binding x 3"
    ),
    highlight = c(FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE),
    row_y    = rev(seq_len(8))
  )

  col_x <- c(criterion = 0.01, n_label = 0.68, source = 0.80)

  label_df <- rows %>%
    pivot_longer(c(criterion, n_label, source), names_to = "col", values_to = "text") %>%
    mutate(
      x    = col_x[col],
      hjust = ifelse(col == "criterion", 0, ifelse(col == "n_label", 0, 0)),
      bold  = highlight & col == "n_label",
      fontface = ifelse(bold, "bold", "plain"),
      size  = ifelse(highlight, 2.7, 2.5),
      col_c = ifelse(highlight, COL$teal, COL$black)
    )

  # Header row
  header <- tibble(
    x = c(col_x["criterion"], col_x["n_label"], col_x["source"]),
    text = c("Criterion", "N", "Source"),
    hjust = c(0, 0, 0)
  )

  # Highlight bands
  hi_rows <- rows %>% filter(highlight)

  # Divider lines
  n_rows  <- nrow(rows)
  div_y   <- c(n_rows + 0.5,    # top of header
               n_rows - 0.5,    # below header
               2.5)             # above recommended rows

  ggplot() +
    # Highlight bands
    geom_rect(data = hi_rows,
              aes(xmin = -0.01, xmax = 1.01, ymin = row_y - 0.48, ymax = row_y + 0.48),
              fill = COL$hilite, colour = NA) +
    # Dividers
    geom_segment(data = tibble(y = div_y),
                 aes(x = -0.01, xend = 1.01, y = y, yend = y),
                 colour = COL$lgrey, linewidth = 0.4) +
    # Header labels
    geom_text(data = header,
              aes(x = x, y = n_rows + 1, label = text, hjust = hjust),
              fontface = "bold", size = 2.6, colour = COL$black) +
    # Data labels
    geom_text(data = label_df,
              aes(x = x, y = row_y, label = text,
                  hjust = hjust, size = size,
                  fontface = fontface, colour = col_c),
              lineheight = 1.0, show.legend = FALSE) +
    scale_size_identity() +
    scale_colour_identity() +
    coord_cartesian(xlim = c(0, 1), ylim = c(0.3, n_rows + 1.5), clip = "off") +
    labs(title = "Recommended sample sizes", tag = "D") +
    BASE_THEME +
    theme(
      axis.line   = element_blank(),
      axis.text   = element_blank(),
      axis.ticks  = element_blank(),
      axis.title  = element_blank(),
      plot.margin = margin(6, 6, 6, 6)
    )
}

# ── Compose and save ──────────────────────────────────────────────────────────

pa <- make_panel_a()
pb <- make_panel_b()
pc <- make_panel_c()
pd <- make_panel_d()

fig <- (pa | pb) / (pc | pd) +
  plot_annotation(
    caption = paste0(
      "Power simulation: lmerTest (Satterthwaite df); 500 reps/N; ",
      "alpha = 0.05 (two-sided). DGM: SD_participant = 0.6, SD_vignette = 0.8, SD_residual = 0.7 (total SD ~1.22). ",
      "Contextual effects: medium d = 0.30-0.50. ",
      "Dirichlet simulation: 1000 reps/N. ",
      "All participant counts are per role-perspective arm (agent/target/observer)."
    ),
    theme = theme(
      plot.caption = element_text(size = 6.5, colour = COL$grey,
                                  hjust = 0, lineheight = 1.3,
                                  margin = margin(t = 6))
    )
  ) &
  theme(plot.background = element_rect(fill = COL$bg, colour = NA))

out_path <- file.path(OUT_DIR, "power_analysis_figure.pdf")
ggsave(out_path, fig, width = 170, height = 150, units = "mm", device = "pdf")
message("Saved ", out_path)

out_png <- file.path(OUT_DIR, "power_analysis_figure.png")
ggsave(out_png, fig, width = 170, height = 150, units = "mm", dpi = 300)
message("Saved ", out_png)
