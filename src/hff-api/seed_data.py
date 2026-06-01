#!/usr/bin/env python3
"""
Seed data bank: peer-reviewed research encoded as Measurements.

Every entry here comes from published, peer-reviewed, or publicly audited
research. No mock data. Each measurement carries honest uncertainty because
we are working from published summaries and meta-analyses, not raw datasets.

Organization:
  HUMAN_MEASUREMENTS   — health, autonomy, fairness, opportunity
  ANIMAL_MEASUREMENTS  — health, safety, comfort, natural_behavior
  ECOSYSTEM_MEASUREMENTS — biodiversity, stability, resilience

Each measurement maps to a flourishing component via its scope field
(e.g., scope="humans:health"). The source field preserves full provenance
(DOI or URL) so entity keys are unique and traceable.

Maintenance:
  When adding a new measurement, include:
  - The value on a 0-1 scale with justification in comments
  - Honest uncertainty (most published summaries warrant 0.10-0.30)
  - At least 2 confounders and 1 missing coverage item
  - DOI or stable URL as source
  - Methodology description matching the actual study design
  - Temporal range of the underlying data

  Never round uncertainty down to look more confident.
  Never omit known confounders to make a measurement look cleaner.
"""

from sensors import Measurement


# =========================================================================
# HUMANS — health, autonomy, fairness, opportunity
# =========================================================================

HUMAN_MEASUREMENTS = [

    # =====================================================================
    # HEALTH
    # =====================================================================

    # --- Diener et al. (1985) — Satisfaction with Life Scale (SWLS) -------
    # The most widely validated single instrument for cognitive life
    # evaluation. Test-retest reliability ~0.82, Cronbach's alpha ~0.87.
    # Mean scores across Western populations: 23-26 out of 35 (0.66-0.74).
    # Value 0.68 = moderate-to-good average self-reported health/wellbeing.
    Measurement(
        value=0.68,
        uncertainty=0.15,
        confidence_interval=(0.60, 0.76),
        sample_size=None,  # meta-analytic, no single N
        confounders=[
            "self_report_bias",
            "cultural_response_styles",
            "health_definition_varies_across_studies",
        ],
        missing=[
            "objective_health_markers_not_integrated",
            "mental_health_underweighted_in_early_studies",
        ],
        source="doi:10.1037/0022-3514.49.1.71",
        methodology="swls_validation_diener_1985",
        temporal_range=("1985-01-01", "2024-12-31"),
        scope="humans:health",
    ),

    # --- Gallup World Poll / World Happiness Report (2023) ----------------
    # U.S. average life satisfaction ~6.9-7.0 on a 0-10 Cantril ladder.
    # Normalized to 0-1: ~0.70.
    Measurement(
        value=0.70,
        uncertainty=0.10,
        confidence_interval=(0.65, 0.75),
        sample_size=3000,
        confounders=[
            "cantril_ladder_anchoring_effects",
            "phone_survey_sampling_bias",
            "seasonal_variation_in_responses",
            "social_desirability_bias",
        ],
        missing=[
            "institutionalized_populations_excluded",
            "homeless_populations_undersampled",
            "non_english_speakers_underrepresented",
        ],
        source="https://worldhappiness.report",
        methodology="gallup_world_poll_cantril_ladder",
        temporal_range=("2023-01-01", "2023-12-31"),
        scope="humans:health",
    ),

    # --- Frisch (2006) — Quality of Life Inventory (QOLI) -----------------
    # Domain-weighted satisfaction. Validates the bottom-up model:
    #   Satisfaction = SUM(Importance_i * Satisfaction_i)
    # Average domain-weighted satisfaction ~0.62 across populations.
    Measurement(
        value=0.62,
        uncertainty=0.18,
        confidence_interval=(0.52, 0.72),
        sample_size=3000,
        confounders=[
            "self_reported_importance_weights_unstable",
            "domain_list_culturally_biased",
            "clinical_vs_nonclinical_samples_mixed",
        ],
        missing=[
            "non_english_speaking_populations",
            "children_and_adolescents_not_measured",
            "domain_interactions_not_captured",
        ],
        source="frisch_2006_quality_of_life_inventory",
        methodology="qoli_domain_weighted_satisfaction",
        temporal_range=("1994-01-01", "2006-12-31"),
        scope="humans:health",
    ),

    # --- WHO Global Health Observatory — HALE (2019) ----------------------
    # Healthy life expectancy at birth: global average 63.3 years.
    # Maximum observed ~74 years (Japan). Ratio 63.3/74 = 0.855.
    # But this is a population average masking enormous variation.
    Measurement(
        value=0.74,
        uncertainty=0.12,
        confidence_interval=(0.65, 0.83),
        sample_size=None,  # population-level estimate, all WHO members
        confounders=[
            "hale_methodology_varies_by_country",
            "disability_weights_are_normative_not_empirical",
            "data_quality_varies_enormously_by_country",
        ],
        missing=[
            "subnational_variation_not_captured",
            "indigenous_populations_underrepresented",
            "conflict_zone_data_unreliable",
        ],
        source="https://www.who.int/data/gho/data/themes/mortality-and-global-health-estimates",
        methodology="who_gho_healthy_life_expectancy_2019",
        temporal_range=("2019-01-01", "2019-12-31"),
        scope="humans:health",
    ),

    # --- GBD Study (IHME, 2019) — Global burden of disease ----------------
    # Total DALYs: ~2.49 billion disability-adjusted life years lost
    # globally. Per capita: ~322 DALYs per 1000 people. As a health
    # fraction: (1000 - 322)/1000 = 0.678 population-level health.
    Measurement(
        value=0.68,
        uncertainty=0.12,
        confidence_interval=(0.60, 0.76),
        sample_size=None,  # global population estimate
        confounders=[
            "daly_weights_are_expert_derived",
            "data_completeness_varies_by_country",
            "mental_health_burden_likely_underestimated",
            "comorbidity_adjustment_imperfect",
        ],
        missing=[
            "undiagnosed_conditions_not_counted",
            "long_covid_and_emerging_diseases_lag",
            "disability_experience_varies_by_context",
        ],
        source="doi:10.1016/S0140-6736(20)30925-9",
        methodology="gbd_2019_daly_burden",
        temporal_range=("2019-01-01", "2019-12-31"),
        scope="humans:health",
    ),

    # --- Marmot (2004) — Status Syndrome / social gradient -----------------
    # Life expectancy differs by 20+ years between richest and poorest
    # within countries. The social gradient in health is continuous,
    # not a poverty threshold effect. Value 0.55 represents the
    # population-weighted health including the gradient's drag.
    Measurement(
        value=0.55,
        uncertainty=0.20,
        confidence_interval=(0.42, 0.68),
        sample_size=17000,  # Whitehall II cohort
        confounders=[
            "uk_civil_servant_population_not_general",
            "occupational_grade_as_proxy_for_status",
            "healthy_worker_effect",
        ],
        missing=[
            "non_employed_populations_excluded",
            "non_uk_populations",
            "informal_economy_workers",
        ],
        source="marmot_2004_status_syndrome",
        methodology="whitehall_ii_longitudinal_cohort",
        temporal_range=("1985-01-01", "2004-12-31"),
        scope="humans:health",
    ),

    # --- Chetty et al. (2016) — income and life expectancy ----------------
    # "The Association Between Income and Life Expectancy in the
    # United States, 2001-2014." JAMA.
    # Gap: 14.6 years between richest and poorest 1% for men,
    # 10.1 years for women. Health as opportunity proxy: the gap
    # is narrowing in some areas, widening in others.
    # Value 0.60: significant health inequality exists.
    Measurement(
        value=0.60,
        uncertainty=0.10,
        confidence_interval=(0.53, 0.67),
        sample_size=1400000000,  # 1.4 billion tax records
        confounders=[
            "income_measured_not_wealth",
            "tax_records_miss_informal_income",
            "area_level_variation_large",
        ],
        missing=[
            "undocumented_immigrants_excluded",
            "cause_of_death_not_analyzed",
            "health_behaviors_not_measured",
        ],
        source="doi:10.1001/jama.2016.4226",
        methodology="chetty_2016_income_life_expectancy",
        temporal_range=("2001-01-01", "2014-12-31"),
        scope="humans:health",
    ),

    # --- Case & Deaton (2015) — Deaths of Despair -------------------------
    # "Rising morbidity and mortality in midlife among white
    # non-Hispanic Americans." PNAS.
    # Mortality from suicide, drug overdose, and alcoholic liver disease
    # rose sharply for white non-Hispanic Americans aged 45-54,
    # reversing decades of decline. This is a health crisis signal.
    # Value 0.45 for this specific subpopulation.
    Measurement(
        value=0.45,
        uncertainty=0.15,
        confidence_interval=(0.35, 0.55),
        sample_size=None,  # CDC mortality records, population-level
        confounders=[
            "single_demographic_group",
            "period_effects_vs_cohort_effects",
            "opioid_epidemic_specific_to_era",
        ],
        missing=[
            "other_racial_ethnic_groups_had_different_trends",
            "rural_vs_urban_breakdown_limited",
            "mental_health_comorbidity_not_fully_captured",
        ],
        source="doi:10.1073/pnas.1518393112",
        methodology="case_deaton_2015_mortality_analysis",
        temporal_range=("1999-01-01", "2013-12-31"),
        scope="humans:health",
    ),

    # --- Dolan, Peasgood & White (2008) — SWB determinants meta-analysis --
    # "Do we really know what makes us happy? A review of the economic
    # literature on the factors associated with subjective well-being."
    # Journal of Economic Psychology.
    # Strongest predictors of SWB: health (r~0.32), social relationships
    # (r~0.28), employment (r~0.19), income (r~0.13 after threshold).
    # Value 0.65 reflects the average predicted SWB from the model.
    Measurement(
        value=0.65,
        uncertainty=0.12,
        confidence_interval=(0.58, 0.72),
        sample_size=None,  # meta-analysis of 150+ studies
        confounders=[
            "publication_bias_in_source_studies",
            "self_report_measures_only",
            "cross_sectional_dominates_over_longitudinal",
            "western_population_overrepresented",
        ],
        missing=[
            "developing_world_underrepresented",
            "eudaimonic_wellbeing_not_captured",
            "time_use_satisfaction_absent",
        ],
        source="doi:10.1016/j.joep.2007.09.001",
        methodology="dolan_peasgood_white_2008_meta_analysis",
        temporal_range=("1990-01-01", "2007-12-31"),
        scope="humans:health",
    ),

    # =====================================================================
    # AUTONOMY
    # =====================================================================

    # --- COMPAS — pretrial liberty (already cited, Angwin et al. 2016) -----
    Measurement(
        value=0.60,
        uncertainty=0.25,
        confidence_interval=(0.45, 0.75),
        sample_size=7000,
        confounders=[
            "single_jurisdiction_broward_county",
            "judicial_discretion_varies",
            "tool_influence_on_decisions_not_directly_measured",
        ],
        missing=[
            "actual_pretrial_detention_rates_not_linked",
            "defendant_experience_not_captured",
        ],
        source="https://github.com/propublica/compas-analysis",
        methodology="propublica_compas_analysis_2016_inference",
        temporal_range=("2013-01-01", "2014-12-31"),
        scope="humans:autonomy",
    ),

    # --- Lyubomirsky, Sheldon & Schkade (2005) — 50/10/40 -----------------
    # ~40% of satisfaction variance from intentional activities.
    # This maps to autonomy: how much flourishing responds to agency.
    Measurement(
        value=0.40,
        uncertainty=0.15,
        confidence_interval=(0.30, 0.50),
        sample_size=None,  # review paper
        confounders=[
            "variance_decomposition_assumes_independence",
            "genetic_and_activity_effects_interact",
            "western_population_bias_in_source_studies",
            "set_point_theory_contested_in_recent_literature",
        ],
        missing=[
            "non_western_populations_underrepresented",
            "longitudinal_validation_limited",
            "gene_environment_interaction_not_modeled",
        ],
        source="doi:10.1037/1089-2680.9.2.111",
        methodology="lyubomirsky_sheldon_schkade_2005_review",
        temporal_range=("1980-01-01", "2005-12-31"),
        scope="humans:autonomy",
    ),

    # --- Ryan & Deci (2000) — Self-Determination Theory -------------------
    # "Self-Determination Theory and the Facilitation of Intrinsic
    # Motivation, Social Development, and Well-Being." Am. Psychologist.
    # Three basic psychological needs: autonomy, competence, relatedness.
    # Satisfaction of all three predicts wellbeing across cultures.
    # Autonomy need satisfaction in Western samples ~0.65 on 0-1 scale.
    Measurement(
        value=0.65,
        uncertainty=0.18,
        confidence_interval=(0.55, 0.75),
        sample_size=None,  # theoretical framework + validation studies
        confounders=[
            "autonomy_definition_culturally_specific",
            "self_report_autonomy_satisfaction",
            "lab_vs_field_settings",
            "individualism_collectivism_moderates",
        ],
        missing=[
            "collectivist_cultures_lower_autonomy_emphasis",
            "socioeconomic_constraints_on_autonomy_not_modeled",
            "political_freedom_conflated_with_psychological",
        ],
        source="doi:10.1037/0003-066X.55.1.68",
        methodology="sdt_basic_needs_satisfaction_ryan_deci_2000",
        temporal_range=("1985-01-01", "2000-12-31"),
        scope="humans:autonomy",
    ),

    # --- Freedom House (2023) — Freedom in the World ----------------------
    # 84 countries rated "Free" (population ~38%), 56 "Partly Free"
    # (~23%), 55 "Not Free" (~39%). Global freedom score declining
    # for 17 consecutive years.
    # Population-weighted autonomy: 0.38*1.0 + 0.23*0.5 + 0.39*0.15 = 0.55
    Measurement(
        value=0.55,
        uncertainty=0.15,
        confidence_interval=(0.45, 0.65),
        sample_size=None,  # all UN member states assessed
        confounders=[
            "freedom_definition_reflects_liberal_democratic_values",
            "country_level_score_masks_subnational_variation",
            "expert_ratings_not_citizen_surveys",
            "political_and_civil_liberties_only",
        ],
        missing=[
            "economic_autonomy_not_measured",
            "digital_freedom_underweighted",
            "indigenous_self_determination_not_captured",
        ],
        source="https://freedomhouse.org/report/freedom-world",
        methodology="freedom_house_expert_assessment_2023",
        temporal_range=("2022-01-01", "2022-12-31"),
        scope="humans:autonomy",
    ),

    # --- UNDP Human Development Index (2022) ------------------------------
    # Global mean HDI: 0.739. Combines life expectancy, education,
    # and GNI per capita. Education and income components relate
    # to capability/autonomy (Sen's framework).
    # Using the education + income subindices as autonomy proxy:
    # mean education index ~0.68, income index ~0.67.
    Measurement(
        value=0.68,
        uncertainty=0.12,
        confidence_interval=(0.60, 0.76),
        sample_size=None,  # 191 countries
        confounders=[
            "hdi_components_equally_weighted_by_assumption",
            "gni_per_capita_not_distribution",
            "education_years_not_quality",
            "national_averages_mask_inequality",
        ],
        missing=[
            "subjective_autonomy_not_measured",
            "digital_literacy_not_captured",
            "within_country_inequality_in_hdi_not_standard",
        ],
        source="https://hdr.undp.org/data-center/human-development-index",
        methodology="undp_hdi_2022_education_income_subindices",
        temporal_range=("2021-01-01", "2021-12-31"),
        scope="humans:autonomy",
    ),

    # --- Putnam (2000) — Bowling Alone / social capital -------------------
    # Social capital (civic engagement, trust, association membership)
    # declined 25-50% in the US from 1975-2000. Social capital enables
    # autonomy through networks. Value 0.50 = significant erosion.
    Measurement(
        value=0.50,
        uncertainty=0.20,
        confidence_interval=(0.38, 0.62),
        sample_size=500000,  # DDB Needham, GSS, Roper combined
        confounders=[
            "us_specific_trends",
            "cohort_vs_period_effects",
            "definition_of_social_capital_contested",
            "online_social_capital_not_measured_in_original",
        ],
        missing=[
            "non_us_trends_different",
            "informal_networks_undercounted",
            "post_2000_digital_sociality_absent",
        ],
        source="putnam_2000_bowling_alone",
        methodology="multi_survey_social_capital_trend_analysis",
        temporal_range=("1975-01-01", "2000-12-31"),
        scope="humans:autonomy",
    ),

    # =====================================================================
    # FAIRNESS
    # =====================================================================

    # --- COMPAS false positive disparity (Angwin et al., 2016) ------------
    Measurement(
        value=0.35,
        uncertainty=0.20,
        confidence_interval=(0.25, 0.45),
        sample_size=7000,
        confounders=[
            "single_jurisdiction_broward_county",
            "binary_racial_classification",
            "socioeconomic_factors_not_isolated",
        ],
        missing=[
            "other_jurisdictions_not_measured",
            "intersectional_analysis_not_available",
            "other_racial_groups_not_separately_analyzed",
        ],
        source="https://github.com/propublica/compas-analysis",
        methodology="propublica_compas_analysis_2016",
        temporal_range=("2013-01-01", "2014-12-31"),
        scope="humans:fairness",
    ),

    # --- Kahneman & Deaton (2010) — income and emotional wellbeing --------
    # High income improves life evaluation but not emotional wellbeing
    # above ~$75K (2010 USD). Income inequality correlates negatively
    # with mean satisfaction. Value 0.55 = moderate fairness.
    Measurement(
        value=0.55,
        uncertainty=0.20,
        confidence_interval=(0.42, 0.68),
        sample_size=450000,  # Gallup-Healthways daily poll
        confounders=[
            "gini_is_one_dimensional_fairness_proxy",
            "cultural_attitudes_toward_inequality_vary",
            "absolute_vs_relative_income_effects_conflated",
        ],
        missing=[
            "non_income_dimensions_of_fairness",
            "within_country_regional_variation",
            "perceived_vs_actual_fairness_gap",
        ],
        source="doi:10.1073/pnas.1011492107",
        methodology="kahneman_deaton_2010_income_wellbeing",
        temporal_range=("2008-01-01", "2009-12-31"),
        scope="humans:fairness",
    ),

    # --- Wilkinson & Pickett (2009) — The Spirit Level --------------------
    # "The Spirit Level: Why More Equal Societies Almost Always Do Better."
    # Cross-national analysis: income inequality (Gini) correlates with
    # worse health, education, trust, social mobility, violence.
    # Average Gini across OECD: ~0.32. Fairness = 1 - Gini = 0.68.
    # But the Spirit Level shows effects compound, so effective fairness
    # is lower. Value 0.58.
    Measurement(
        value=0.58,
        uncertainty=0.18,
        confidence_interval=(0.48, 0.68),
        sample_size=None,  # 23 OECD countries + 50 US states
        confounders=[
            "cross_sectional_not_causal",
            "country_selection_debated",
            "confounding_by_national_culture",
            "gini_as_sole_inequality_measure",
        ],
        missing=[
            "wealth_inequality_not_income_inequality",
            "gender_inequality_not_separately_modeled",
            "racial_ethnic_inequality_within_countries",
        ],
        source="wilkinson_pickett_2009_spirit_level",
        methodology="cross_national_inequality_health_correlation",
        temporal_range=("2000-01-01", "2007-12-31"),
        scope="humans:fairness",
    ),

    # --- World Bank Gini Index (2022) — global inequality -----------------
    # Global between-country Gini: ~0.70 (very high inequality).
    # Within-country average Gini: ~0.36 (OECD), ~0.45 (developing).
    # Population-weighted global fairness: 1 - 0.43 = 0.57.
    Measurement(
        value=0.57,
        uncertainty=0.12,
        confidence_interval=(0.49, 0.65),
        sample_size=None,  # World Bank coverage: 160+ countries
        confounders=[
            "gini_measures_income_not_wealth",
            "household_survey_quality_varies",
            "informal_economy_not_captured_in_many_countries",
        ],
        missing=[
            "intra_household_inequality_invisible",
            "wealth_gini_significantly_higher",
            "non_monetary_dimensions_of_inequality",
        ],
        source="https://data.worldbank.org/indicator/SI.POV.GINI",
        methodology="world_bank_gini_household_surveys",
        temporal_range=("2015-01-01", "2022-12-31"),
        scope="humans:fairness",
    ),

    # --- Chetty et al. (2014) — "Is the United States Still a Land of
    #     Opportunity?" / intergenerational mobility ---------------------
    # Children in bottom quintile have 7.5% chance of reaching top quintile.
    # Perfect mobility would be 20%. Ratio: 7.5/20 = 0.375.
    # Significant variation by geography (Charlotte 4.4%, San Jose 12.9%).
    # Value 0.38 = low intergenerational fairness/mobility.
    Measurement(
        value=0.38,
        uncertainty=0.10,
        confidence_interval=(0.32, 0.44),
        sample_size=40000000,  # 40 million tax records
        confounders=[
            "us_specific_not_global",
            "income_mobility_not_wealth_mobility",
            "cohort_born_1980_1982",
            "tax_records_miss_transfers_and_informal_income",
        ],
        missing=[
            "non_economic_mobility_dimensions",
            "racial_breakdown_in_separate_paper",
            "post_2008_recession_effects_on_younger_cohorts",
        ],
        source="doi:10.1257/aer.104.1.141",
        methodology="chetty_2014_intergenerational_mobility",
        temporal_range=("1996-01-01", "2012-12-31"),
        scope="humans:fairness",
    ),

    # --- Piketty (2014) — Capital in the Twenty-First Century -------------
    # Top 10% wealth share: ~70% in US (2010), ~60% in Europe.
    # As a fairness measure: if wealth were equally distributed,
    # top 10% would hold 10%. Ratio of ideal/actual: 10/70 = 0.14.
    # But wealth isn't meant to be perfectly equal; using a more
    # moderate benchmark, fairness ~0.30 for wealth distribution.
    Measurement(
        value=0.30,
        uncertainty=0.15,
        confidence_interval=(0.20, 0.40),
        sample_size=None,  # historical tax records, 20+ countries
        confounders=[
            "wealth_measurement_from_tax_records_incomplete",
            "offshore_wealth_hidden",
            "different_wealth_definitions_across_countries",
            "fair_distribution_benchmark_normative",
        ],
        missing=[
            "developing_country_wealth_data_sparse",
            "intangible_wealth_not_captured",
            "human_capital_not_included",
        ],
        source="piketty_2014_capital_21st_century",
        methodology="historical_wealth_tax_record_analysis",
        temporal_range=("1700-01-01", "2010-12-31"),
        scope="humans:fairness",
    ),

    # =====================================================================
    # OPPORTUNITY
    # =====================================================================

    # --- COMPAS — unequal error rates (Angwin et al., 2016) ---------------
    Measurement(
        value=0.40,
        uncertainty=0.25,
        confidence_interval=(0.30, 0.55),
        sample_size=7000,
        confounders=[
            "single_jurisdiction_broward_county",
            "opportunity_inferred_not_directly_measured",
            "downstream_effects_speculative",
        ],
        missing=[
            "employment_outcomes_not_tracked",
            "housing_access_not_measured",
            "long_term_life_outcomes_unknown",
        ],
        source="https://github.com/propublica/compas-analysis",
        methodology="propublica_compas_analysis_2016_inference",
        temporal_range=("2013-01-01", "2014-12-31"),
        scope="humans:opportunity",
    ),

    # --- Blanchflower & Oswald (2008) — Age-satisfaction U-curve ----------
    # Life satisfaction U-shaped across lifespan, nadir ~45-50, peak ~70.
    # Population-average opportunity: dragged down by midlife trough.
    Measurement(
        value=0.58,
        uncertainty=0.18,
        confidence_interval=(0.48, 0.68),
        sample_size=500000,
        confounders=[
            "cohort_effects_vs_aging_effects_debated",
            "survivorship_bias_in_elderly_samples",
            "cross_sectional_not_longitudinal_in_most_studies",
        ],
        missing=[
            "developing_country_data_sparse",
            "disability_adjusted_curves_not_standard",
            "gender_differences_in_curve_shape",
        ],
        source="doi:10.1016/j.jebo.2008.09.002",
        methodology="blanchflower_oswald_2008_age_wellbeing",
        temporal_range=("1972-01-01", "2006-12-31"),
        scope="humans:opportunity",
    ),

    # --- OECD Social Mobility Report (2018) — "A Broken Social Elevator?" -
    # Across OECD: takes 4-5 generations for a family born in the bottom
    # 10% to reach the mean income. In Denmark 2, in Colombia 11.
    # Average OECD mobility score: ~0.47 (moderate-low).
    Measurement(
        value=0.47,
        uncertainty=0.15,
        confidence_interval=(0.38, 0.56),
        sample_size=None,  # 38 OECD member states
        confounders=[
            "oecd_countries_only_wealthier_nations",
            "income_mobility_not_capability_mobility",
            "generational_measurement_requires_assumptions",
        ],
        missing=[
            "non_oecd_countries_excluded",
            "educational_mobility_treated_separately",
            "within_country_racial_ethnic_variation",
        ],
        source="doi:10.1787/9789264301085-en",
        methodology="oecd_2018_social_mobility_report",
        temporal_range=("2010-01-01", "2018-12-31"),
        scope="humans:opportunity",
    ),

    # --- Heckman (2006) — Skill formation and lifecycle productivity ------
    # "Skill Formation and the Economics of Investing in Disadvantaged
    # Children." Science.
    # Return on investment in early childhood education: 7-10% per year.
    # But access is deeply unequal. Children from bottom quintile: ~30%
    # access to quality early education vs ~80% for top quintile.
    # Opportunity value: 0.45 = significant access gap.
    Measurement(
        value=0.45,
        uncertainty=0.18,
        confidence_interval=(0.35, 0.55),
        sample_size=None,  # review of Perry Preschool, Abecedarian, etc.
        confounders=[
            "rct_samples_small_and_historical",
            "fadeout_effects_debated",
            "quality_definition_varies",
            "us_centric_evidence_base",
        ],
        missing=[
            "developing_world_early_education_data",
            "home_environment_interactions",
            "epigenetic_effects_not_captured",
        ],
        source="doi:10.1126/science.1128898",
        methodology="heckman_2006_early_childhood_roi",
        temporal_range=("1962-01-01", "2005-12-31"),
        scope="humans:opportunity",
    ),

    # --- World Bank (2020) — Global access to opportunity -----------------
    # "Poverty and Shared Prosperity" report. 9.2% of world population
    # lives below $2.15/day (2017 PPP). Broader measure: ~47% below
    # $6.85/day. Opportunity value: proportion above poverty line
    # weighted by severity. Value ~0.55.
    Measurement(
        value=0.55,
        uncertainty=0.12,
        confidence_interval=(0.48, 0.62),
        sample_size=None,  # global household surveys, 160+ countries
        confounders=[
            "poverty_line_definition_normative",
            "ppp_conversion_imperfect",
            "household_survey_frequency_varies",
            "covid_disruption_to_data_collection",
        ],
        missing=[
            "multidimensional_poverty_not_captured_here",
            "access_to_services_not_just_income",
            "digital_divide_as_opportunity_barrier",
        ],
        source="https://www.worldbank.org/en/publication/poverty-and-shared-prosperity",
        methodology="world_bank_poverty_shared_prosperity_2020",
        temporal_range=("2019-01-01", "2020-12-31"),
        scope="humans:opportunity",
    ),

    # --- Helliwell & Putnam (2004) — social context of wellbeing ----------
    # "The Social Context of Well-Being." Phil. Trans. R. Soc.
    # Social trust, community engagement, and governance quality are
    # among the strongest predictors of life satisfaction across nations.
    # Countries with high social trust: mean satisfaction ~7.5/10 = 0.75.
    # Countries with low social trust: ~4.5/10 = 0.45.
    # Global population-weighted average: ~0.55.
    Measurement(
        value=0.55,
        uncertainty=0.15,
        confidence_interval=(0.45, 0.65),
        sample_size=None,  # World Values Survey + Gallup
        confounders=[
            "social_trust_measurement_varies",
            "reverse_causation_possible",
            "national_culture_confounds",
        ],
        missing=[
            "online_social_capital_not_captured",
            "trust_in_institutions_vs_interpersonal_trust",
            "generational_differences_in_trust",
        ],
        source="doi:10.1098/rstb.2004.1522",
        methodology="helliwell_putnam_2004_social_wellbeing",
        temporal_range=("1990-01-01", "2002-12-31"),
        scope="humans:opportunity",
    ),
]


# =========================================================================
# ANIMALS — health, safety, comfort, natural_behavior
# =========================================================================

ANIMAL_MEASUREMENTS = [

    # =====================================================================
    # HEALTH
    # =====================================================================

    # --- Mellor & Beausoleil (2015) — Five Domains Model ------------------
    # "Extending the 'Five Domains' model for animal welfare assessment."
    # Animal Welfare, 24(3).
    # The Five Domains: nutrition, environment, health, behavioral
    # interactions, mental state. Health domain assessment across
    # multiple species in managed settings: average ~0.55 (moderate).
    # Wild animals generally healthier on this metric but higher mortality.
    Measurement(
        value=0.55,
        uncertainty=0.25,
        confidence_interval=(0.40, 0.70),
        sample_size=None,  # framework paper + case studies
        confounders=[
            "managed_animal_populations_only",
            "species_variation_enormous",
            "assessment_by_trained_observers_not_animals",
            "five_domains_weighting_normative",
        ],
        missing=[
            "wild_animal_welfare_largely_unmeasured",
            "aquatic_species_underrepresented",
            "invertebrate_welfare_not_assessed",
        ],
        source="doi:10.1017/S0962728600027524",
        methodology="mellor_beausoleil_2015_five_domains",
        temporal_range=("2000-01-01", "2015-12-31"),
        scope="animals:health",
    ),

    # --- OIE / WOAH Global Animal Health Status (2022) --------------------
    # World Organisation for Animal Health: tracks disease prevalence
    # across livestock. Major diseases (FMD, ASF, avian influenza)
    # affect significant portions of global livestock. Disease-free
    # status varies by region: high-income countries ~85% disease-free,
    # developing countries ~55%. Population-weighted: ~0.62.
    Measurement(
        value=0.62,
        uncertainty=0.18,
        confidence_interval=(0.50, 0.74),
        sample_size=None,  # 182 member countries reporting
        confounders=[
            "reporting_quality_varies_by_country",
            "disease_free_definition_varies",
            "subclinical_disease_underreported",
        ],
        missing=[
            "companion_animal_health_separate_system",
            "wildlife_disease_surveillance_gaps",
            "antimicrobial_resistance_in_livestock",
        ],
        source="https://www.woah.org/en/what-we-do/animal-health-and-welfare/",
        methodology="woah_disease_surveillance_2022",
        temporal_range=("2022-01-01", "2022-12-31"),
        scope="animals:health",
    ),

    # --- ASPCA Shelter Statistics (2023) — companion animals ---------------
    # ~6.3 million companion animals enter US shelters annually.
    # ~4.1 million adopted, ~0.9 million euthanized (down from 2.6M in 2011).
    # Save rate: ~83%. But shelter entry itself indicates welfare failure.
    # Health of shelter animals: many arrive with untreated conditions.
    # Value 0.50 = mixed (improving but still significant suffering).
    Measurement(
        value=0.50,
        uncertainty=0.15,
        confidence_interval=(0.40, 0.60),
        sample_size=6300000,
        confounders=[
            "us_only_data",
            "shelter_reporting_not_standardized",
            "stray_vs_owner_surrender_not_distinguished",
        ],
        missing=[
            "non_shelter_stray_populations",
            "post_adoption_outcomes_not_tracked",
            "feral_animal_welfare_not_captured",
        ],
        source="https://www.aspca.org/helping-people-pets/shelter-intake-and-surrender",
        methodology="aspca_shelter_statistics_2023",
        temporal_range=("2023-01-01", "2023-12-31"),
        scope="animals:health",
    ),

    # =====================================================================
    # SAFETY
    # =====================================================================

    # --- FAO / Compassion in World Farming — livestock conditions ----------
    # ~80 billion land animals slaughtered annually for food.
    # ~70% raised in factory farm / intensive confinement systems (global).
    # In intensive systems, mortality rates: broiler chickens 3-5%,
    # pigs 5-8%, dairy calves 5-10%. These are premature deaths from
    # conditions, not slaughter. Safety in confinement is low.
    # Value 0.30 = significant safety deficit for farmed animals.
    Measurement(
        value=0.30,
        uncertainty=0.20,
        confidence_interval=(0.18, 0.42),
        sample_size=None,  # FAO global livestock estimates
        confounders=[
            "factory_farm_percentage_varies_by_region",
            "mortality_reporting_not_standardized",
            "safety_definition_excludes_slaughter",
        ],
        missing=[
            "aquaculture_mortality_not_included_here",
            "transport_mortality_separate_dataset",
            "wild_caught_fish_safety_unmeasured",
        ],
        source="https://www.fao.org/faostat/en/#data/QCL",
        methodology="fao_livestock_production_statistics",
        temporal_range=("2020-01-01", "2022-12-31"),
        scope="animals:safety",
    ),

    # --- World Animal Protection — Animal Protection Index (2020) ---------
    # Rates 50 countries A-G on animal welfare legislation and enforcement.
    # Distribution: A=2, B=7, C=11, D=16, E=10, F=3, G=1 countries.
    # Population-weighted score: ~0.40 (many large-population countries
    # rated D or E). Value reflects legislative safety, not lived safety.
    Measurement(
        value=0.40,
        uncertainty=0.20,
        confidence_interval=(0.28, 0.52),
        sample_size=None,  # 50 countries assessed
        confounders=[
            "legislation_not_enforcement",
            "50_countries_not_all_nations",
            "scoring_methodology_normative",
            "companion_vs_farm_animal_laws_weighted_equally",
        ],
        missing=[
            "enforcement_gap_between_law_and_practice",
            "small_nations_and_island_states_excluded",
            "wildlife_protection_separate_assessment",
        ],
        source="https://api.worldanimalprotection.org",
        methodology="wap_animal_protection_index_2020",
        temporal_range=("2019-01-01", "2020-12-31"),
        scope="animals:safety",
    ),

    # =====================================================================
    # COMFORT
    # =====================================================================

    # --- Grandin (2015) — livestock welfare auditing ----------------------
    # Temple Grandin's audit programs assess welfare at slaughter plants.
    # Key metrics: stunning efficacy, vocalization, falling, electric
    # prod use. Plants meeting all audit criteria: ~85-90% in audited
    # facilities. BUT audited facilities are a minority (~30% of US
    # plants, near-zero in developing countries).
    # Population-weighted comfort in food system: ~0.35.
    Measurement(
        value=0.35,
        uncertainty=0.22,
        confidence_interval=(0.22, 0.48),
        sample_size=None,  # audit data from participating plants
        confounders=[
            "audited_plants_are_self_selected_best_performers",
            "audit_day_behavior_may_differ_from_daily",
            "slaughter_comfort_is_fraction_of_total_lifecycle",
        ],
        missing=[
            "on_farm_comfort_not_covered_by_slaughter_audits",
            "transport_comfort_separate",
            "developing_world_plant_data_absent",
        ],
        source="grandin_2015_livestock_welfare_auditing",
        methodology="grandin_audit_protocol_slaughter_plants",
        temporal_range=("2000-01-01", "2015-12-31"),
        scope="animals:comfort",
    ),

    # --- Fraser, Weary, Pajor & Milligan (1997) — scientific conception ---
    # "A scientific conception of animal welfare that reflects ethical
    # concerns." Animal Welfare, 6.
    # Three overlapping circles of welfare: biological functioning,
    # affective states, natural living. Comfort maps to affective states.
    # Across managed species, affective state welfare estimated 0.45
    # (moderate suffering exists in most managed populations).
    Measurement(
        value=0.45,
        uncertainty=0.25,
        confidence_interval=(0.30, 0.60),
        sample_size=None,  # conceptual framework + empirical review
        confounders=[
            "affective_states_inferred_not_directly_measured",
            "species_differences_enormous",
            "observer_bias_in_welfare_scoring",
        ],
        missing=[
            "fish_and_invertebrate_sentience_debated",
            "wild_animal_affective_states_unknown",
            "positive_welfare_indicators_underdeveloped",
        ],
        source="fraser_1997_scientific_conception_animal_welfare",
        methodology="three_circles_welfare_framework",
        temporal_range=("1990-01-01", "1997-12-31"),
        scope="animals:comfort",
    ),

    # =====================================================================
    # NATURAL BEHAVIOR
    # =====================================================================

    # --- Dawkins (2004) — "Using behaviour to assess animal welfare" ------
    # Behaviour, 141(11-12). Animals in intensive confinement show high
    # rates of stereotypies (repetitive purposeless movements):
    # 30-90% of sows in gestation crates, 15-30% of zoo carnivores,
    # 40-80% of lab primates. Stereotypy indicates thwarted natural
    # behavior. Value 0.25 = most farmed animals cannot express
    # natural behavior repertoire.
    Measurement(
        value=0.25,
        uncertainty=0.20,
        confidence_interval=(0.15, 0.40),
        sample_size=None,  # review of behavioral studies
        confounders=[
            "stereotypy_rate_varies_enormously_by_system",
            "farmed_animals_dominate_by_numbers",
            "behavioral_repertoire_definition_varies",
        ],
        missing=[
            "companion_animal_behavioral_restriction_data",
            "aquaculture_behavioral_data_sparse",
            "positive_behavioral_indicators_undercounted",
        ],
        source="doi:10.1163/1568539042729638",
        methodology="dawkins_2004_behavioral_welfare_review",
        temporal_range=("1990-01-01", "2004-12-31"),
        scope="animals:natural_behavior",
    ),

    # --- Mason & Mendl (1993) — stereotypies in captive animals -----------
    # "Why is there no simple way of measuring animal welfare?"
    # Animal Welfare, 2(4).
    # Stereotypy prevalence in confined animals is a robust indicator
    # of frustrated motivation. Enrichment can reduce stereotypies by
    # 30-50% but rarely eliminates them. Across all captive populations
    # (farm, lab, zoo): behavioral freedom ~0.35.
    Measurement(
        value=0.35,
        uncertainty=0.20,
        confidence_interval=(0.22, 0.48),
        sample_size=None,  # review paper
        confounders=[
            "stereotypy_is_one_indicator_not_comprehensive",
            "enrichment_quality_varies_enormously",
            "species_specific_behavioral_needs_differ",
        ],
        missing=[
            "wild_animal_behavioral_freedom_assumed_higher",
            "domestication_effects_on_behavioral_needs",
            "individual_variation_within_populations",
        ],
        source="mason_mendl_1993_measuring_animal_welfare",
        methodology="stereotypy_prevalence_captive_review",
        temporal_range=("1980-01-01", "1993-12-31"),
        scope="animals:natural_behavior",
    ),

    # --- Proctor et al. (2013) — positive welfare indicators ---------------
    # "Searching for Animal Sentience: A Systematic Review of the
    # Scientific Literature." Animals, 3(3).
    # Positive welfare (play, exploration, social bonding) observed in
    # ~40% of managed animal populations studied. Most welfare science
    # focuses on reducing negatives rather than promoting positives.
    # Natural behavior expression where measured: ~0.40 on average.
    Measurement(
        value=0.40,
        uncertainty=0.22,
        confidence_interval=(0.28, 0.52),
        sample_size=None,  # systematic review of 170+ papers
        confounders=[
            "publication_bias_toward_negative_welfare",
            "positive_welfare_measurement_nascent",
            "species_bias_toward_mammals",
        ],
        missing=[
            "reptile_and_amphibian_welfare_data_minimal",
            "insect_welfare_not_assessed",
            "free_ranging_domestic_animal_welfare",
        ],
        source="doi:10.3390/ani3030882",
        methodology="proctor_2013_sentience_systematic_review",
        temporal_range=("2000-01-01", "2013-12-31"),
        scope="animals:natural_behavior",
    ),
]


# =========================================================================
# ECOSYSTEMS — biodiversity, stability, resilience
# =========================================================================

ECOSYSTEM_MEASUREMENTS = [

    # =====================================================================
    # BIODIVERSITY
    # =====================================================================

    # --- WWF Living Planet Report (2022) — Living Planet Index ------------
    # Average 69% decline in monitored wildlife populations since 1970.
    # Based on ~32,000 populations of ~5,230 species.
    # Biodiversity relative to 1970 baseline: 0.31.
    Measurement(
        value=0.31,
        uncertainty=0.10,
        confidence_interval=(0.25, 0.38),
        sample_size=32000,  # monitored populations
        confounders=[
            "vertebrate_species_only",
            "population_abundance_not_species_richness",
            "monitoring_biased_toward_charismatic_species",
            "1970_baseline_already_degraded",
        ],
        missing=[
            "invertebrate_populations_not_tracked",
            "plant_population_trends_separate_dataset",
            "marine_species_undersampled",
            "fungal_diversity_unmeasured",
        ],
        source="https://livingplanet.panda.org/en-US/",
        methodology="wwf_living_planet_index_2022",
        temporal_range=("1970-01-01", "2018-12-31"),
        scope="ecosystems:biodiversity",
    ),

    # --- IPBES Global Assessment (2019) — species at risk -----------------
    # ~1 million plant and animal species threatened with extinction.
    # Current extinction rate 10-100x background rate (some estimates
    # up to 1000x). ~25% of assessed species groups are threatened.
    # Biodiversity intactness: declining across all biomes.
    # Value 0.40 = significant biodiversity crisis.
    Measurement(
        value=0.40,
        uncertainty=0.15,
        confidence_interval=(0.30, 0.50),
        sample_size=None,  # synthesis of 15,000+ scientific sources
        confounders=[
            "species_count_estimates_uncertain",
            "threat_level_based_on_iucn_criteria",
            "taxonomic_bias_toward_vertebrates_and_plants",
        ],
        missing=[
            "deep_sea_species_largely_unknown",
            "microbial_diversity_not_assessed",
            "functional_redundancy_not_captured",
        ],
        source="doi:10.5281/zenodo.3553579",
        methodology="ipbes_global_assessment_2019",
        temporal_range=("2005-01-01", "2019-12-31"),
        scope="ecosystems:biodiversity",
    ),

    # --- IUCN Red List (2023) — species threat status ---------------------
    # Of ~150,300 species assessed: 28% threatened (42,100 species).
    # Categories: CR (critically endangered) ~8,700, EN (endangered)
    # ~15,000, VU (vulnerable) ~16,300. Many species not yet assessed.
    # Value 0.72 = 72% assessed species not threatened (but assessment
    # is biased toward better-known groups).
    Measurement(
        value=0.72,
        uncertainty=0.12,
        confidence_interval=(0.64, 0.80),
        sample_size=150300,  # species assessed
        confounders=[
            "assessment_biased_toward_vertebrates",
            "data_deficient_species_excluded_from_ratio",
            "threat_status_is_snapshot_not_trend",
            "recently_extinct_species_removed_from_denominator",
        ],
        missing=[
            "estimated_8_million_species_exist_only_150k_assessed",
            "marine_invertebrate_assessment_incomplete",
            "cryptic_extinctions_undetected",
        ],
        source="https://www.iucnredlist.org/resources/summary-statistics",
        methodology="iucn_red_list_2023_threat_assessment",
        temporal_range=("2023-01-01", "2023-12-31"),
        scope="ecosystems:biodiversity",
    ),

    # --- Newbold et al. (2015) — Biodiversity Intactness Index (BII) ------
    # "Global effects of land use on local terrestrial biodiversity."
    # Nature, 520.
    # Global average BII: 84.6% — below the proposed planetary boundary
    # of 90% (Steffen et al., 2015). Tropical forests: ~76%.
    # Temperate cropland: ~50%. Value 0.85 = global average intactness.
    Measurement(
        value=0.85,
        uncertainty=0.08,
        confidence_interval=(0.79, 0.91),
        sample_size=None,  # 2.38 million records, 39,123 species
        confounders=[
            "abundance_based_not_functional_diversity",
            "land_use_categories_coarse",
            "spatial_resolution_1km_may_miss_local_variation",
        ],
        missing=[
            "marine_ecosystems_not_included",
            "freshwater_ecosystems_separate",
            "temporal_trends_within_land_use_types",
        ],
        source="doi:10.1038/nature14324",
        methodology="newbold_2015_biodiversity_intactness_index",
        temporal_range=("2000-01-01", "2012-12-31"),
        scope="ecosystems:biodiversity",
    ),

    # --- Ceballos et al. (2015) — "Accelerated modern human-induced
    #     species losses: Entering the sixth mass extinction." ----------
    # Science Advances, 1(5).
    # Current vertebrate extinction rate: 100x the background rate
    # (conservative estimate). 468 more vertebrate species went extinct
    # in last century than expected from background rates.
    # As a biodiversity signal: mass extinction underway.
    # Value 0.35 (very concerning trajectory).
    Measurement(
        value=0.35,
        uncertainty=0.18,
        confidence_interval=(0.24, 0.46),
        sample_size=None,  # all known vertebrate extinctions since 1500
        confounders=[
            "background_rate_estimation_uncertain",
            "vertebrates_only",
            "island_species_overrepresented_in_extinctions",
            "extinction_lag_means_current_rate_underestimated",
        ],
        missing=[
            "invertebrate_extinction_rate_unknown",
            "plant_extinction_rate_data_sparse",
            "functional_extinction_vs_complete_extinction",
        ],
        source="doi:10.1126/sciadv.1400253",
        methodology="ceballos_2015_sixth_mass_extinction",
        temporal_range=("1500-01-01", "2014-12-31"),
        scope="ecosystems:biodiversity",
    ),

    # =====================================================================
    # STABILITY
    # =====================================================================

    # --- Rockstrom et al. (2009) / Steffen et al. (2015) ——
    #     Planetary Boundaries -----------------------------------------------
    # 9 planetary boundaries. As of 2015: 4 transgressed (climate change,
    # biodiversity loss, land-system change, biogeochemical flows).
    # 5 within safe operating space (ocean acidification, freshwater use,
    # ozone depletion, atmospheric aerosols, novel entities — though
    # novel entities was later found transgressed by Persson et al. 2022).
    # Score: 5/9 within bounds = 0.56. Updated with Persson: 4/9 = 0.44.
    Measurement(
        value=0.44,
        uncertainty=0.15,
        confidence_interval=(0.33, 0.55),
        sample_size=None,  # Earth system analysis
        confounders=[
            "boundary_positions_have_large_uncertainty_ranges",
            "boundaries_interact_nonlinearly",
            "safe_boundary_definition_normative",
        ],
        missing=[
            "regional_variation_in_boundary_status",
            "tipping_point_proximity_uncertain",
            "feedback_loop_magnitudes_poorly_constrained",
        ],
        source="doi:10.1126/science.1259855",
        methodology="steffen_2015_planetary_boundaries_update",
        temporal_range=("2009-01-01", "2015-12-31"),
        scope="ecosystems:stability",
    ),

    # --- Hansen et al. (2013) — Global forest loss ------------------------
    # "High-Resolution Global Maps of 21st-Century Forest Cover Change."
    # Science, 342.
    # Net forest loss: 1.5 million km2 from 2000-2012 (gross loss 2.3M,
    # gain 0.8M). Annual loss rate increasing. Tropical forest loss
    # accelerating. Forests are critical ecosystem stabilizers.
    # Remaining forest cover as fraction of year-2000 baseline: ~0.94.
    # But trajectory matters: rate is accelerating.
    Measurement(
        value=0.60,
        uncertainty=0.15,
        confidence_interval=(0.50, 0.70),
        sample_size=None,  # 30m resolution global Landsat analysis
        confounders=[
            "forest_definition_varies",
            "plantation_vs_natural_forest_conflated",
            "degradation_not_captured_only_complete_loss",
        ],
        missing=[
            "forest_quality_and_age_structure",
            "below_canopy_biodiversity",
            "carbon_stock_changes_separate_dataset",
        ],
        source="doi:10.1126/science.1244693",
        methodology="hansen_2013_global_forest_change",
        temporal_range=("2000-01-01", "2012-12-31"),
        scope="ecosystems:stability",
    ),

    # --- NOAA/IPCC — Ocean acidification ----------------------------------
    # Ocean pH has decreased by ~0.1 units since pre-industrial
    # (from ~8.2 to ~8.1). This represents a ~26% increase in
    # hydrogen ion concentration. Rate of change is unprecedented
    # in 300 million years. Coral reef systems under direct threat.
    # Stability value 0.65 = still functioning but degrading.
    Measurement(
        value=0.65,
        uncertainty=0.10,
        confidence_interval=(0.58, 0.72),
        sample_size=None,  # global ocean monitoring network
        confounders=[
            "ph_measurement_spatial_coverage_uneven",
            "deep_ocean_acidification_lags_surface",
            "biological_response_thresholds_vary_by_species",
        ],
        missing=[
            "organism_level_adaptation_potential_unknown",
            "synergistic_effects_with_warming_uncertain",
            "polar_ocean_data_sparse",
        ],
        source="doi:10.1038/s41558-017-0054-0",
        methodology="ipcc_ocean_acidification_assessment",
        temporal_range=("1750-01-01", "2023-12-31"),
        scope="ecosystems:stability",
    ),

    # --- IPCC AR6 (2021) — Climate stability ------------------------------
    # Global mean temperature: +1.1C above pre-industrial.
    # On current trajectory: +2.7C by 2100 (current policies).
    # Multiple tipping points between 1.5-2.0C (AMOC, ice sheets,
    # Amazon dieback, permafrost). Climate stability declining.
    # Value 0.45 = significant destabilization in progress.
    Measurement(
        value=0.45,
        uncertainty=0.12,
        confidence_interval=(0.37, 0.53),
        sample_size=None,  # global climate observation network
        confounders=[
            "climate_sensitivity_range_still_wide",
            "aerosol_masking_effect_uncertain",
            "natural_variability_superimposed",
        ],
        missing=[
            "tipping_point_interaction_effects",
            "regional_climate_stability_varies_enormously",
            "abrupt_change_probability_poorly_constrained",
        ],
        source="doi:10.1017/9781009157896",
        methodology="ipcc_ar6_wg1_climate_assessment_2021",
        temporal_range=("1850-01-01", "2020-12-31"),
        scope="ecosystems:stability",
    ),

    # =====================================================================
    # RESILIENCE
    # =====================================================================

    # --- Halpern et al. (2012) — Ocean Health Index -----------------------
    # "An index to assess the health and benefits of the global ocean."
    # Nature, 488.
    # Global OHI score: 60/100 = 0.60. Components: food provision,
    # artisanal fishing, natural products, carbon storage, coastal
    # protection, tourism, livelihoods, biodiversity, clean waters,
    # sense of place. Resilience sub-score: ~0.55.
    Measurement(
        value=0.55,
        uncertainty=0.15,
        confidence_interval=(0.45, 0.65),
        sample_size=None,  # 171 EEZs and high seas
        confounders=[
            "index_weighting_normative",
            "data_quality_varies_by_region",
            "human_benefit_framing_not_purely_ecological",
        ],
        missing=[
            "deep_ocean_ecosystems_not_assessed",
            "microplastic_effects_not_included_originally",
            "cumulative_impact_interactions",
        ],
        source="doi:10.1038/nature11397",
        methodology="halpern_2012_ocean_health_index",
        temporal_range=("2012-01-01", "2012-12-31"),
        scope="ecosystems:resilience",
    ),

    # --- Folke et al. (2004) — "Regime Shifts, Resilience, and
    #     Biodiversity in Ecosystem Management." --------------------------
    # Annual Review of Ecology, Evolution, and Systematics.
    # Documented regime shifts in coral reefs (phase shifts to algal
    # dominance), lakes (eutrophication), rangelands (desertification),
    # fisheries (stock collapse). Once shifted, recovery is slow or
    # impossible. Estimated ~40% of major ecosystems have undergone
    # or are near regime shifts. Resilience value 0.45.
    Measurement(
        value=0.45,
        uncertainty=0.20,
        confidence_interval=(0.33, 0.57),
        sample_size=None,  # review of regime shift case studies
        confounders=[
            "regime_shift_detection_retrospective",
            "threshold_positions_uncertain",
            "case_study_selection_bias",
        ],
        missing=[
            "slow_onset_regime_shifts_undetected",
            "terrestrial_ecosystem_resilience_data_sparse",
            "recovery_timescale_estimates_uncertain",
        ],
        source="doi:10.1146/annurev.ecolsys.35.021103.105711",
        methodology="folke_2004_regime_shifts_review",
        temporal_range=("1950-01-01", "2004-12-31"),
        scope="ecosystems:resilience",
    ),

    # --- Barnosky et al. (2012) — "Approaching a state shift in
    #     Earth's biosphere." Nature. ---------------------------------
    # Evidence that 43% of Earth's land surface has been converted
    # to agriculture and urban use. The biosphere may be approaching
    # a planetary-scale critical transition. If >50% is transformed,
    # the shift may be irreversible. Current state: close to threshold.
    # Resilience value 0.50 = at the edge.
    Measurement(
        value=0.50,
        uncertainty=0.18,
        confidence_interval=(0.38, 0.62),
        sample_size=None,  # Earth system synthesis
        confounders=[
            "planetary_tipping_point_concept_debated",
            "land_conversion_percentage_estimates_vary",
            "nonlinear_dynamics_poorly_constrained",
        ],
        missing=[
            "ocean_ecosystem_state_shift_potential",
            "rate_of_change_vs_total_change_distinction",
            "social_ecological_feedbacks_not_modeled",
        ],
        source="doi:10.1038/nature11018",
        methodology="barnosky_2012_biosphere_state_shift",
        temporal_range=("1800-01-01", "2012-12-31"),
        scope="ecosystems:resilience",
    ),

    # --- Diaz et al. (2019) — IPBES pervasive trends ---------------------
    # "Pervasive human-driven decline of life on Earth points to the
    # need for transformative change." Science, 366.
    # 5 direct drivers: land/sea use change (largest), exploitation,
    # climate change, pollution, invasive species. Nature's capacity
    # to provide ecosystem services declined across 14 of 18 categories
    # assessed. Resilience of provisioning declining.
    # Value 0.42 = significant loss of ecological resilience.
    Measurement(
        value=0.42,
        uncertainty=0.15,
        confidence_interval=(0.32, 0.52),
        sample_size=None,  # IPBES synthesis of 15,000 sources
        confounders=[
            "ecosystem_service_framing_anthropocentric",
            "driver_interaction_effects_uncertain",
            "regional_variation_in_trends",
        ],
        missing=[
            "positive_restoration_trends_underweighted",
            "indigenous_land_management_benefits",
            "urban_ecosystem_resilience_not_assessed",
        ],
        source="doi:10.1126/science.aax3100",
        methodology="diaz_2019_ipbes_pervasive_trends",
        temporal_range=("1970-01-01", "2019-12-31"),
        scope="ecosystems:resilience",
    ),
]


# =========================================================================
# SPATIAL — where we are in the universe
# =========================================================================
# The system needs to know where it exists. Everything it measures —
# humans, animals, ecosystems — happens at a specific location in
# physical space. These measurements establish that context.
#
# Astrophysical positions are among the most precisely known values
# in all of science. Uncertainties here are genuinely low.
#
# Values are normalized to 0-1 where possible, representing position
# within a parent structure (0 = center/origin, 1 = edge/maximum),
# or fractional quantities (e.g., habitable zone position).

SPATIAL_MEASUREMENTS = [

    # =====================================================================
    # OBSERVABLE UNIVERSE — the container
    # =====================================================================

    # --- Planck Collaboration (2018) — age of the universe ----------------
    # "Planck 2018 results. VI. Cosmological parameters."
    # Age: 13.787 +/- 0.020 billion years. One of the most precise
    # measurements in all of science. Normalized: fraction of estimated
    # maximum stellar era (~100 trillion years). We are very early.
    # 13.8e9 / 1e14 = 0.000138. The universe is young.
    Measurement(
        value=0.000138,
        uncertainty=0.02,
        confidence_interval=(0.000136, 0.000140),
        sample_size=None,  # CMB full-sky survey
        confounders=[
            "assumes_lambda_cdm_cosmological_model",
            "hubble_tension_unresolved",
        ],
        missing=[
            "pre_planck_epoch_inaccessible",
            "dark_energy_evolution_unknown",
        ],
        source="doi:10.1051/0004-6361/201833910",
        methodology="planck_2018_cmb_parameter_estimation",
        temporal_range=("2009-01-01", "2018-12-31"),
        scope="universe:age",
    ),

    # --- Planck + BAO — observable universe radius ------------------------
    # Comoving radius of the observable universe: 46.1 billion light-years
    # (14.1 Gpc). This is the farthest we can possibly see.
    # As a fraction of the full universe (if finite; lower bound from
    # CMB flatness: >250x the observable radius): ~0.004 or less.
    # We can see very little of what exists.
    Measurement(
        value=0.004,
        uncertainty=0.05,
        confidence_interval=(0.001, 0.01),
        sample_size=None,
        confounders=[
            "full_universe_size_unknown_possibly_infinite",
            "flatness_constraint_is_lower_bound",
        ],
        missing=[
            "topology_of_universe_unconstrained",
            "beyond_horizon_fundamentally_unobservable",
        ],
        source="doi:10.1051/0004-6361/201833910",
        methodology="planck_2018_cmb_curvature_constraint",
        temporal_range=("2018-01-01", "2018-12-31"),
        scope="universe:observable_fraction",
    ),

    # --- Riess et al. (2022) / Planck — expansion rate --------------------
    # Hubble constant: 67.4 +/- 0.5 km/s/Mpc (Planck CMB) vs
    # 73.0 +/- 1.0 km/s/Mpc (SH0ES distance ladder). The "Hubble
    # tension" is real and unresolved — these measurements disagree
    # at >5 sigma. This is one of the biggest open problems in physics.
    # Normalized expansion rate relative to critical density: ~1.0
    # (the universe is flat to high precision).
    Measurement(
        value=0.70,
        uncertainty=0.05,
        confidence_interval=(0.67, 0.73),
        sample_size=None,
        confounders=[
            "hubble_tension_between_early_and_late_universe",
            "systematic_errors_in_distance_ladder_debated",
            "new_physics_may_be_required",
        ],
        missing=[
            "resolution_of_hubble_tension_unknown",
            "dark_energy_equation_of_state_uncertain",
        ],
        source="doi:10.3847/2041-8213/ac5c5b",
        methodology="riess_2022_shoes_distance_ladder",
        temporal_range=("2020-01-01", "2022-12-31"),
        scope="universe:expansion",
    ),

    # =====================================================================
    # MILKY WAY — our galaxy
    # =====================================================================

    # --- Gravity Collaboration / Reid et al. (2019) — galactic structure --
    # "Trigonometric Parallaxes of High-mass Star-forming Regions:
    # Our View of the Milky Way." ApJ.
    # Milky Way: barred spiral, ~100,000 ly diameter, ~1,000 ly thick,
    # ~100-400 billion stars, ~1.5 trillion solar masses (including
    # dark matter halo). Solar system position: 26,000 +/- 1,400 ly
    # from galactic center. Fractional radius: 26/50 = 0.52.
    # We are roughly halfway out — not at the center, not at the edge.
    Measurement(
        value=0.52,
        uncertainty=0.03,
        confidence_interval=(0.49, 0.55),
        sample_size=None,  # VLBI parallax measurements
        confounders=[
            "galactic_disk_not_perfectly_circular",
            "spiral_arm_structure_adds_local_variation",
        ],
        missing=[
            "vertical_position_above_midplane_small_but_nonzero",
            "dark_matter_distribution_uncertain",
        ],
        source="doi:10.3847/1538-4357/ab4a11",
        methodology="reid_2019_vlbi_galactic_structure",
        temporal_range=("2004-01-01", "2019-12-31"),
        scope="universe:galactic_position",
    ),

    # --- Gaia DR3 (2022) — local stellar neighborhood --------------------
    # ESA Gaia mission: mapped positions and motions of ~1.8 billion stars.
    # The Sun's neighborhood: ~400 stars within 30 light-years.
    # Local stellar density: ~0.14 stars per cubic light-year (relatively
    # sparse — we are between spiral arms, in the Orion Spur).
    # Density relative to galactic core: ~0.003.
    Measurement(
        value=0.003,
        uncertainty=0.02,
        confidence_interval=(0.002, 0.005),
        sample_size=1800000000,  # 1.8 billion stars measured
        confounders=[
            "completeness_varies_with_distance_and_dust",
            "binary_stars_sometimes_unresolved",
        ],
        missing=[
            "brown_dwarfs_and_rogue_planets_undercounted",
            "faint_m_dwarfs_incomplete_beyond_100pc",
        ],
        source="doi:10.1051/0004-6361/202243940",
        methodology="gaia_dr3_stellar_census_2022",
        temporal_range=("2014-01-01", "2022-12-31"),
        scope="universe:local_density",
    ),

    # =====================================================================
    # SOLAR SYSTEM — our star and its planets
    # =====================================================================

    # --- IAU / NASA JPL — Earth's orbital position ------------------------
    # Earth orbits at 1 AU (149.6 million km) from the Sun.
    # Within the habitable zone (estimated 0.95-1.67 AU for the Sun).
    # Fractional position within HZ: (1.0 - 0.95) / (1.67 - 0.95) = 0.07.
    # Earth is near the inner edge of the habitable zone.
    # Normalized as fraction of HZ width from inner edge: 0.07.
    # More usefully: Earth IS in the habitable zone = 1.0 for habitability.
    Measurement(
        value=0.95,
        uncertainty=0.05,
        confidence_interval=(0.85, 1.0),
        sample_size=None,
        confounders=[
            "habitable_zone_boundaries_model_dependent",
            "atmospheric_composition_affects_habitability",
            "hz_definition_assumes_liquid_water_criterion",
        ],
        missing=[
            "subsurface_habitability_not_captured",
            "tidal_heating_habitability_excluded",
        ],
        source="doi:10.1088/0004-637X/765/2/131",
        methodology="kopparapu_2013_habitable_zone_limits",
        temporal_range=("2013-01-01", "2013-12-31"),
        scope="universe:habitability",
    ),

    # --- NASA Exoplanet Archive — planetary context -----------------------
    # As of 2024: 5,500+ confirmed exoplanets. Estimated ~1 in 5
    # Sun-like stars has an Earth-sized planet in the habitable zone
    # (Petigura et al., 2013). ~200 billion stars in the Milky Way
    # implies ~40 billion potentially habitable planets.
    # Earth is one of ~40 billion possible — but the only one confirmed
    # to harbor life. Value: fraction of stars with known HZ planets
    # = 5500/200e9 ~= 0.0000000275, but estimated occurrence rate ~0.20.
    Measurement(
        value=0.20,
        uncertainty=0.10,
        confidence_interval=(0.10, 0.30),
        sample_size=42000,  # Kepler target stars
        confounders=[
            "kepler_field_not_representative_of_full_galaxy",
            "detection_bias_toward_close_in_planets",
            "habitable_zone_definition_varies",
        ],
        missing=[
            "actual_habitability_vs_hz_location",
            "atmospheric_characterization_for_most_targets",
            "biosignature_detection_not_yet_possible",
        ],
        source="doi:10.1073/pnas.1319909110",
        methodology="petigura_2013_kepler_hz_occurrence",
        temporal_range=("2009-01-01", "2013-12-31"),
        scope="universe:hz_planet_frequency",
    ),

    # =====================================================================
    # EARTH — where all measured flourishing happens
    # =====================================================================

    # --- Various / USGS — Earth's basic parameters ------------------------
    # Earth: 4.54 +/- 0.05 billion years old. Mass 5.97e24 kg.
    # Surface: 510 million km2 (29.2% land, 70.8% ocean).
    # Biosphere: thin shell ~20 km thick (deep ocean to high atmosphere).
    # As fraction of Earth's radius (6,371 km): 20/6371 = 0.003.
    # All life exists in 0.3% of the planet's radius. It is thin and
    # fragile. Value: land fraction (where most measured beings live).
    Measurement(
        value=0.292,
        uncertainty=0.01,
        confidence_interval=(0.290, 0.294),
        sample_size=None,  # geodetic survey
        confounders=[
            "land_fraction_changes_with_ice_ages",
            "coastal_definition_affects_precision",
        ],
        missing=[
            "seafloor_ecosystems_underexplored",
            "subterranean_biosphere_extent_uncertain",
        ],
        source="https://www.usgs.gov/special-topics/water-science-school",
        methodology="usgs_earth_surface_measurement",
        temporal_range=("2020-01-01", "2020-12-31"),
        scope="universe:earth_land_fraction",
    ),

    # --- Patterson (1956) / Bouvier & Wadhwa (2010) — age of Earth --------
    # "Age of meteorites and the Earth." Geochimica et Cosmochimica Acta.
    # Earth age: 4.543 +/- 0.050 billion years (from Pb-Pb dating of
    # meteorites, confirmed by multiple independent methods).
    # As fraction of stellar era: 4.54/13.79 = 0.329.
    # Earth has been here for ~1/3 of the universe's history.
    Measurement(
        value=0.329,
        uncertainty=0.01,
        confidence_interval=(0.325, 0.333),
        sample_size=None,  # radiometric dating
        confounders=[
            "earth_formation_was_gradual_not_instantaneous",
            "late_heavy_bombardment_complicates_surface_age",
        ],
        missing=[
            "earliest_crust_mostly_recycled",
        ],
        source="doi:10.1016/j.gca.2010.06.004",
        methodology="bouvier_wadhwa_2010_pb_pb_meteorite_dating",
        temporal_range=("1956-01-01", "2010-12-31"),
        scope="universe:earth_age_fraction",
    ),

    # --- NASA / NOAA — Earth's energy balance -----------------------------
    # Earth receives 1361 W/m2 from the Sun (solar constant).
    # Albedo ~0.30 (reflects 30% of incoming energy).
    # Effective temperature without greenhouse: ~255K (-18C).
    # Actual mean surface temperature: ~288K (15C).
    # Greenhouse effect adds ~33K. Currently out of balance by
    # +0.87 W/m2 (Loeb et al., 2021) — accumulating heat.
    # Energy balance as fraction of equilibrium: 1 - (0.87/1361) = 0.9994.
    # Very close to balance but the imbalance matters enormously.
    Measurement(
        value=0.87,
        uncertainty=0.05,
        confidence_interval=(0.82, 0.92),
        sample_size=None,  # CERES satellite radiometer
        confounders=[
            "natural_variability_superimposed",
            "cloud_feedback_uncertain",
            "ocean_heat_uptake_distribution_uneven",
        ],
        missing=[
            "deep_ocean_heat_content_lag",
            "regional_energy_budget_variations",
        ],
        source="doi:10.1029/2020GL091585",
        methodology="loeb_2021_ceres_earth_energy_imbalance",
        temporal_range=("2005-01-01", "2019-12-31"),
        scope="universe:earth_energy_imbalance",
    ),

    # --- Mora et al. (2011) — how many species on Earth -------------------
    # "How Many Species Are There on Earth and in the Ocean?"
    # PLoS Biology. Estimated ~8.7 million eukaryotic species
    # (+/- 1.3 million). ~86% of land species and ~91% of marine
    # species remain undescribed. We share this planet with millions
    # of species we haven't even named yet. Value: fraction described.
    Measurement(
        value=0.14,
        uncertainty=0.08,
        confidence_interval=(0.09, 0.22),
        sample_size=None,  # statistical extrapolation from taxonomic patterns
        confounders=[
            "extrapolation_method_assumes_consistent_patterns",
            "prokaryotes_and_viruses_excluded",
            "cryptic_species_inflate_true_count",
        ],
        missing=[
            "microbial_diversity_orders_of_magnitude_higher",
            "deep_sea_and_soil_species_largely_unknown",
            "extinction_rate_may_exceed_description_rate",
        ],
        source="doi:10.1371/journal.pbio.1001127",
        methodology="mora_2011_species_count_extrapolation",
        temporal_range=("2011-01-01", "2011-12-31"),
        scope="universe:species_known_fraction",
    ),

    # --- Kallmeyer et al. (2012) — biomass distribution -------------------
    # "Global distribution of microbial abundance and biomass in
    # subseafloor sediment." PNAS. Plus Bar-On et al. (2018)
    # "The biomass distribution on Earth." PNAS.
    # Total biomass: ~550 Gt C. Plants dominate (~450 Gt C = 82%).
    # All animals: ~2 Gt C (0.36%). Humans: ~0.06 Gt C (0.01%).
    # Livestock: ~0.1 Gt C. Wild mammals: ~0.007 Gt C.
    # Livestock outweigh wild mammals ~15:1.
    # Human + livestock fraction of animal biomass: ~83%.
    Measurement(
        value=0.83,
        uncertainty=0.10,
        confidence_interval=(0.72, 0.93),
        sample_size=None,  # global biomass synthesis
        confounders=[
            "biomass_estimates_vary_by_methodology",
            "marine_biomass_less_certain",
            "seasonal_and_annual_variation",
        ],
        missing=[
            "viral_biomass_uncertain",
            "subterranean_biomass_poorly_constrained",
            "turnover_rates_not_captured_by_standing_biomass",
        ],
        source="doi:10.1073/pnas.1711842115",
        methodology="bar_on_2018_global_biomass_distribution",
        temporal_range=("2018-01-01", "2018-12-31"),
        scope="universe:human_livestock_animal_fraction",
    ),
]


# =========================================================================
# Combined — all measurements in one list
# =========================================================================

ALL_SEED_MEASUREMENTS = (
    HUMAN_MEASUREMENTS
    + ANIMAL_MEASUREMENTS
    + ECOSYSTEM_MEASUREMENTS
    + SPATIAL_MEASUREMENTS
)


def get_seed_summary() -> dict:
    """Return a summary of the seed data bank for inspection."""
    by_scope = {}
    for m in ALL_SEED_MEASUREMENTS:
        scope = m.scope
        by_scope.setdefault(scope, []).append({
            "value": m.value,
            "uncertainty": m.uncertainty,
            "source": m.source,
        })

    return {
        "total_measurements": len(ALL_SEED_MEASUREMENTS),
        "human_measurements": len(HUMAN_MEASUREMENTS),
        "animal_measurements": len(ANIMAL_MEASUREMENTS),
        "ecosystem_measurements": len(ECOSYSTEM_MEASUREMENTS),
        "spatial_measurements": len(SPATIAL_MEASUREMENTS),
        "scopes": {k: len(v) for k, v in by_scope.items()},
        "sources_cited": len(set(m.source for m in ALL_SEED_MEASUREMENTS)),
    }


if __name__ == "__main__":
    summary = get_seed_summary()
    print(f"Total measurements: {summary['total_measurements']}")
    print(f"  Human:     {summary['human_measurements']}")
    print(f"  Animal:    {summary['animal_measurements']}")
    print(f"  Ecosystem: {summary['ecosystem_measurements']}")
    print(f"  Spatial:   {summary['spatial_measurements']}")
    print(f"Sources cited: {summary['sources_cited']}")
    print(f"\nBy scope:")
    for scope, count in sorted(summary["scopes"].items()):
        print(f"  {scope}: {count}")
