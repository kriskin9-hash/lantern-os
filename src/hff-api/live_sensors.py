#!/usr/bin/env python3
"""
Live sensors that connect to real public APIs.

These sensors poll open data sources — no API keys required — and convert
responses into Measurement objects the world model can ingest. Each sensor
is honest about what it measures, what it misses, and how uncertain it is.

Data sources:
  - World Bank Open Data API (indicators.worldbank.org)
    License: CC BY 4.0. Attribution: World Bank, World Development Indicators.
  - WHO Global Health Observatory (GHO) API
    License: CC BY-NC-SA 3.0 IGO. Attribution: World Health Organization.

Limitations:
  - API availability is not guaranteed. Sensors return empty on failure.
  - Values are normalized to 0-1 for the world model. The normalization
    functions embed assumptions (e.g., "100 years is the max life expectancy").
    These assumptions are documented per indicator.
  - Country-level data is aggregated to global estimates using simple
    averages. Population-weighted averages would be more accurate but
    require a separate population dataset.
  - Data lag: most indicators are 1-3 years behind the current date.
    The temporal_range field reflects this honestly.
"""

import requests
import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from sensors import Sensor, Measurement, SensorRegistry
from live_observation_telemetry import (
    LiveObservationTelemetry,
    summarize_belief_activity,
)


def _patch_world_model_status_for_live_telemetry() -> None:
    """Expose live observation telemetry through WorldModel.status().

    app.py already serves `/api/world/status` from `world_model.status()`.
    Patching the model status method here keeps the runtime integration local to
    the live sensor subsystem and avoids duplicating Flask route logic.
    """
    try:
        from world_model import WorldModel
    except Exception:
        return

    if getattr(WorldModel, "_live_observation_status_patched", False):
        return

    original_status = WorldModel.status

    def status_with_live_observation(self):
        status = original_status(self)
        telemetry = getattr(self, "live_observation_telemetry", None)
        if telemetry is None:
            telemetry = LiveObservationTelemetry(
                enabled=False,
                sensor_count=getattr(getattr(self, "sensors", None), "sensor_count", 0),
            )

        live_updated_entities = getattr(self, "live_updated_entities", set())
        belief_activity = summarize_belief_activity(
            getattr(self, "beliefs", {}),
            live_updated_entities=live_updated_entities,
        )
        belief_activity["corrections_count"] = len(getattr(self, "correction_log", []))

        status["live_observation_status"] = telemetry.to_dict()
        status["belief_activity"] = belief_activity
        return status

    WorldModel.status = status_with_live_observation
    WorldModel._live_observation_status_patched = True


_patch_world_model_status_for_live_telemetry()


# ---------------------------------------------------------------------------
# World Bank API helpers
# ---------------------------------------------------------------------------

WORLD_BANK_BASE = "https://api.worldbank.org/v2"

# Countries to query for indicators that don't have world-level aggregates.
# These 20 countries cover ~60% of world population and span all income levels.
# Missing: most of Africa, Central Asia, Pacific islands, Caribbean.
REPRESENTATIVE_COUNTRIES = [
    "USA", "CHN", "IND", "BRA", "IDN",   # large population
    "DEU", "GBR", "FRA", "JPN", "KOR",   # high income
    "NGA", "ETH", "ZAF", "KEN", "EGY",   # Africa
    "MEX", "COL", "ARG",                  # Latin America
    "BGD", "PAK",                          # South Asia
]


def _fetch_world_bank_indicator(
    indicator: str,
    country: str = "WLD",
    date_range: str = "2018:2024",
    per_page: int = 10,
) -> Optional[List[Dict[str, Any]]]:
    """Fetch indicator data from World Bank API.

    Returns list of records or None on failure. Each record has:
      indicator, country, countryiso3code, date, value, ...
    """
    url = (
        f"{WORLD_BANK_BASE}/country/{country}/indicator/{indicator}"
        f"?format=json&date={date_range}&per_page={per_page}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # World Bank returns [metadata, records]
        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return data[1]
        return None
    except Exception:
        return None


def _latest_value(records: Optional[List[Dict]]) -> Optional[Tuple[float, str]]:
    """Extract the most recent non-null value and its year from WB records."""
    if not records:
        return None
    for rec in records:
        val = rec.get("value")
        if val is not None:
            return (float(val), str(rec.get("date", "unknown")))
    return None


def _aggregate_countries(
    indicator: str,
    countries: List[str],
    date_range: str = "2018:2024",
) -> Tuple[Optional[float], Optional[float], int, str, str]:
    """Fetch an indicator for multiple countries and return (mean, std, n, min_year, max_year).

    Returns (None, None, 0, "", "") if no data is available.
    """
    values = []
    years = []
    for iso3 in countries:
        records = _fetch_world_bank_indicator(indicator, iso3, date_range, per_page=5)
        result = _latest_value(records)
        if result:
            values.append(result[0])
            years.append(result[1])
    if not values:
        return None, None, 0, "", ""
    mean = sum(values) / len(values)
    if len(values) > 1:
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        std = math.sqrt(variance)
    else:
        std = None
    return mean, std, len(values), min(years), max(years)


# ---------------------------------------------------------------------------
# Normalization functions
# ---------------------------------------------------------------------------
# Each function maps a raw indicator value to [0, 1] where 1 = best outcome
# for flourishing. The mapping assumptions are documented in comments.


def _normalize_life_expectancy(years: float) -> float:
    """Map life expectancy (0-100 years) to 0-1. Assumes 100y ceiling."""
    return max(0.0, min(1.0, years / 100.0))


def _normalize_gdp_per_capita(usd: float) -> float:
    """Map GDP/capita to 0-1 using log scale. $100=0.0, $100k=1.0.

    Log scale because the relationship between income and wellbeing
    is logarithmic (Kahneman & Deaton 2010, Stevenson & Wolfers 2013).
    """
    if usd <= 0:
        return 0.0
    # log10(100) = 2, log10(100000) = 5. Map [2,5] -> [0,1]
    log_val = math.log10(max(usd, 100))
    return max(0.0, min(1.0, (log_val - 2.0) / 3.0))


def _normalize_gini(gini: float) -> float:
    """Map Gini index (0-100) to 0-1 where 1 = most equal.

    Gini 0 = perfect equality, 100 = perfect inequality.
    We invert because lower inequality = more flourishing.
    """
    return max(0.0, min(1.0, 1.0 - gini / 100.0))


def _normalize_literacy(pct: float) -> float:
    """Map adult literacy rate (0-100%) to 0-1."""
    return max(0.0, min(1.0, pct / 100.0))


def _normalize_maternal_mortality(ratio: float) -> float:
    """Map maternal mortality ratio (per 100k live births) to 0-1.

    0 deaths = 1.0, 1000+ deaths = 0.0. Inverse relationship.
    """
    return max(0.0, min(1.0, 1.0 - ratio / 1000.0))


def _normalize_co2_inverted(tonnes: float) -> float:
    """Map CO2 per capita (metric tons) to 0-1 where 1 = lowest emissions.

    0 tonnes = 1.0, 20+ tonnes = 0.0. For ecosystem stability,
    lower emissions correlate with less climate forcing.
    """
    return max(0.0, min(1.0, 1.0 - tonnes / 20.0))


def _normalize_forest_area(pct: float) -> float:
    """Map forest area as % of land area to 0-1."""
    return max(0.0, min(1.0, pct / 100.0))


def _normalize_protected_areas(pct: float) -> float:
    """Map terrestrial protected areas (% of total land area) to 0-1.

    30% is the Kunming-Montreal target (COP15 2022). We normalize
    against 50% as a theoretical ceiling.
    """
    return max(0.0, min(1.0, pct / 50.0))


def _normalize_infant_mortality(per_1000: float) -> float:
    """Map infant mortality rate (per 1000 live births) to 0-1.

    0 deaths = 1.0, 100+ deaths = 0.0.
    """
    return max(0.0, min(1.0, 1.0 - per_1000 / 100.0))


def _normalize_school_enrollment(pct: float) -> float:
    """Map school enrollment (gross %) to 0-1. Can exceed 100% (grade repeaters)."""
    return max(0.0, min(1.0, pct / 120.0))


# ---------------------------------------------------------------------------
# WorldBankSensor — polls one indicator
# ---------------------------------------------------------------------------


class WorldBankSensor(Sensor):
    """Sensor that polls a single World Bank indicator.

    Fetches the most recent value for a country or world aggregate,
    normalizes it to [0, 1], and wraps it in a Measurement with
    honest uncertainty and provenance.

    Limitations:
    - Data lag of 1-3 years for most indicators.
    - "WLD" (world) aggregates are not available for all indicators.
      Falls back to multi-country averaging when WLD returns null.
    - Normalization functions embed value judgments about what range
      of the indicator maps to 0 vs 1.
    """

    def __init__(
        self,
        sensor_id: str,
        indicator: str,
        scope: str,
        domain: str,
        normalize_fn,
        indicator_name: str = "",
        country: str = "WLD",
        fallback_countries: bool = True,
    ):
        """
        Parameters
        ----------
        indicator : str
            World Bank indicator code (e.g., 'SP.DYN.LE00.IN').
        scope : str
            Flourishing scope this maps to (e.g., 'humans:health').
        domain : str
            Domain label (e.g., 'healthcare', 'economic', 'ecology').
        normalize_fn : callable
            Function mapping raw indicator value to [0, 1].
        indicator_name : str
            Human-readable name for the indicator.
        country : str
            ISO3 country code or 'WLD' for world aggregate.
        fallback_countries : bool
            If True and WLD returns null, query REPRESENTATIVE_COUNTRIES
            and average.
        """
        super().__init__(sensor_id, domain, scope)
        self.indicator = indicator
        self.normalize_fn = normalize_fn
        self.indicator_name = indicator_name or indicator
        self.country = country
        self.fallback_countries = fallback_countries

    def observe(self) -> List[Measurement]:
        """Fetch indicator from World Bank API and produce a Measurement."""
        try:
            records = _fetch_world_bank_indicator(
                self.indicator, self.country, "2018:2024", per_page=10
            )
            result = _latest_value(records)

            raw_value = None
            year = "unknown"
            sample_note = f"world_aggregate_{self.country}"
            n_countries = 1
            std = None

            if result:
                raw_value, year = result
            elif self.fallback_countries:
                # WLD returned null — aggregate from representative countries
                mean, std_val, n, min_yr, max_yr = _aggregate_countries(
                    self.indicator, REPRESENTATIVE_COUNTRIES
                )
                if mean is not None:
                    raw_value = mean
                    std = std_val
                    year = max_yr
                    n_countries = n
                    sample_note = f"mean_of_{n}_countries"

            if raw_value is None:
                self._error_count += 1
                self._last_error = f"no data for {self.indicator}"
                return []

            normalized = self.normalize_fn(raw_value)

            # Uncertainty: base 0.15 for world aggregates, higher for averages
            if n_countries == 1:
                uncertainty = 0.15  # direct measurement, relatively reliable
            else:
                # More countries observed -> lower uncertainty, but never below 0.2
                coverage_penalty = max(0.0, 0.3 - n_countries * 0.01)
                uncertainty = 0.20 + coverage_penalty

            # If we have std from multi-country, incorporate disagreement
            if std is not None and raw_value != 0:
                cv = std / abs(raw_value)  # coefficient of variation
                uncertainty = min(uncertainty + cv * 0.1, 0.6)

            ci_half = uncertainty * 0.5
            ci = (
                round(max(0.0, normalized - ci_half), 4),
                round(min(1.0, normalized + ci_half), 4),
            )

            m = Measurement(
                value=round(normalized, 4),
                uncertainty=round(uncertainty, 4),
                confidence_interval=ci,
                sample_size=n_countries if n_countries > 1 else None,
                confounders=[
                    "normalization_function_embeds_value_judgments",
                    "data_lag_1_to_3_years",
                    "aggregation_not_population_weighted"
                    if n_countries > 1
                    else "single_aggregate_hides_within_group_variation",
                ],
                missing=[
                    f"excludes_countries_without_data"
                    if n_countries > 1
                    else "within_country_inequality_hidden",
                    "subnational_variation_invisible",
                ],
                source=(
                    f"https://data.worldbank.org/indicator/{self.indicator}"
                ),
                methodology=(
                    f"world_bank_api:{self.indicator}:{sample_note}"
                    f":raw={raw_value:.2f}:normalized={normalized:.4f}"
                ),
                temporal_range=(year, year),
                scope=self.scope,
            )

            self._last_observation = datetime.now(timezone.utc)
            self._observation_count += 1
            return [m]

        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            return []


# ---------------------------------------------------------------------------
# WHO Global Health Observatory sensor
# ---------------------------------------------------------------------------

WHO_GHO_BASE = "https://ghoapi.azureedge.net/api"


class WHOSensor(Sensor):
    """Sensor that polls the WHO Global Health Observatory API.

    The GHO API provides health indicators by country and year.
    No API key required. Data is CC BY-NC-SA 3.0 IGO.

    Limitations:
    - Not all indicators have global aggregates.
    - Temporal coverage varies by indicator and country.
    - Some indicators report modeled estimates, not direct observations.
    """

    def __init__(
        self,
        sensor_id: str,
        indicator_code: str,
        scope: str,
        domain: str,
        normalize_fn,
        indicator_name: str = "",
    ):
        super().__init__(sensor_id, domain, scope)
        self.indicator_code = indicator_code
        self.normalize_fn = normalize_fn
        self.indicator_name = indicator_name or indicator_code

    def observe(self) -> List[Measurement]:
        """Fetch indicator from WHO GHO API and produce a Measurement."""
        try:
            # Query for the most recent global value
            url = (
                f"{WHO_GHO_BASE}/{self.indicator_code}"
                f"?$filter=SpatialDim eq 'GLOBAL'"
                f"&$orderby=TimeDim desc&$top=5"
            )
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            records = data.get("value", [])
            if not records:
                # Try without spatial filter — some indicators use different codes
                url_alt = (
                    f"{WHO_GHO_BASE}/{self.indicator_code}"
                    f"?$filter=SpatialDim eq 'WORLD'"
                    f"&$orderby=TimeDim desc&$top=5"
                )
                resp_alt = requests.get(url_alt, timeout=15)
                resp_alt.raise_for_status()
                data_alt = resp_alt.json()
                records = data_alt.get("value", [])

            if not records:
                self._error_count += 1
                self._last_error = f"no global data for {self.indicator_code}"
                return []

            # Find first record with a numeric value
            raw_value = None
            year = "unknown"
            for rec in records:
                val = rec.get("NumericValue")
                if val is not None:
                    raw_value = float(val)
                    year = str(rec.get("TimeDim", "unknown"))
                    break

            if raw_value is None:
                self._error_count += 1
                self._last_error = f"no numeric value for {self.indicator_code}"
                return []

            normalized = self.normalize_fn(raw_value)
            uncertainty = 0.20  # WHO modeled estimates carry moderate uncertainty

            ci_half = uncertainty * 0.5
            ci = (
                round(max(0.0, normalized - ci_half), 4),
                round(min(1.0, normalized + ci_half), 4),
            )

            m = Measurement(
                value=round(normalized, 4),
                uncertainty=round(uncertainty, 4),
                confidence_interval=ci,
                confounders=[
                    "who_modeled_estimates_not_direct_measurement",
                    "normalization_function_embeds_value_judgments",
                ],
                missing=[
                    "country_level_variation_hidden",
                    "some_countries_missing_from_aggregates",
                ],
                source=(
                    f"https://www.who.int/data/gho/data/indicators/"
                    f"indicator-details/GHO/{self.indicator_code}"
                ),
                methodology=(
                    f"who_gho_api:{self.indicator_code}"
                    f":raw={raw_value:.2f}:normalized={normalized:.4f}"
                ),
                temporal_range=(year, year),
                scope=self.scope,
            )

            self._last_observation = datetime.now(timezone.utc)
            self._observation_count += 1
            return [m]

        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            return []


# ---------------------------------------------------------------------------
# Sensor definitions — what we actually poll
# ---------------------------------------------------------------------------

def create_live_sensors() -> List[Sensor]:
    """Create all live sensor instances.

    Returns a list of sensors ready to register with a SensorRegistry.
    Each sensor polls one indicator from one public API.

    Current coverage:
      Humans (6 indicators):
        - Life expectancy at birth (World Bank SP.DYN.LE00.IN)
        - GDP per capita (World Bank NY.GDP.PCAP.CD)
        - Gini index (World Bank SI.POV.GINI, country-level)
        - Adult literacy rate (World Bank SE.ADT.LITR.ZS)
        - Maternal mortality ratio (World Bank SH.STA.MMRT)
        - Infant mortality rate (World Bank SP.DYN.IMRT.IN)

      Ecosystems (3 indicators):
        - CO2 emissions per capita (World Bank EN.ATM.CO2E.PC)
        - Forest area % of land (World Bank AG.LND.FRST.ZS)
        - Terrestrial protected areas % (World Bank ER.PTD.TOTL.ZS)

      Animals:
        - No open API with global animal welfare indicators found yet.
          Animal welfare data remains static from seed_data.py research.
          This is a known gap.
    """
    sensors = []

    # --- HUMANS: HEALTH ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-life-expectancy",
        indicator="SP.DYN.LE00.IN",
        scope="humans:health",
        domain="healthcare",
        normalize_fn=_normalize_life_expectancy,
        indicator_name="Life expectancy at birth (years)",
        country="WLD",
    ))

    sensors.append(WorldBankSensor(
        sensor_id="wb-infant-mortality",
        indicator="SP.DYN.IMRT.IN",
        scope="humans:health",
        domain="healthcare",
        normalize_fn=_normalize_infant_mortality,
        indicator_name="Infant mortality rate (per 1,000 live births)",
        country="WLD",
    ))

    sensors.append(WorldBankSensor(
        sensor_id="wb-maternal-mortality",
        indicator="SH.STA.MMRT",
        scope="humans:health",
        domain="healthcare",
        normalize_fn=_normalize_maternal_mortality,
        indicator_name="Maternal mortality ratio (per 100,000 live births)",
        country="WLD",
    ))

    # --- HUMANS: OPPORTUNITY ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-gdp-per-capita",
        indicator="NY.GDP.PCAP.CD",
        scope="humans:opportunity",
        domain="economic",
        normalize_fn=_normalize_gdp_per_capita,
        indicator_name="GDP per capita (current US$)",
        country="WLD",
    ))

    # --- HUMANS: FAIRNESS ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-gini-index",
        indicator="SI.POV.GINI",
        scope="humans:fairness",
        domain="economic",
        normalize_fn=_normalize_gini,
        indicator_name="Gini index (World Bank estimate)",
        country="WLD",
        fallback_countries=True,  # WLD usually returns null for Gini
    ))

    # --- HUMANS: AUTONOMY ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-adult-literacy",
        indicator="SE.ADT.LITR.ZS",
        scope="humans:autonomy",
        domain="education",
        normalize_fn=_normalize_literacy,
        indicator_name="Adult literacy rate (% ages 15+)",
        country="WLD",
        fallback_countries=True,
    ))

    # --- ECOSYSTEMS: STABILITY ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-co2-per-capita",
        indicator="EN.ATM.CO2E.PC",
        scope="ecosystems:stability",
        domain="ecology",
        normalize_fn=_normalize_co2_inverted,
        indicator_name="CO2 emissions (metric tons per capita)",
        country="WLD",
    ))

    # --- ECOSYSTEMS: BIODIVERSITY ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-forest-area",
        indicator="AG.LND.FRST.ZS",
        scope="ecosystems:biodiversity",
        domain="ecology",
        normalize_fn=_normalize_forest_area,
        indicator_name="Forest area (% of land area)",
        country="WLD",
    ))

    # --- ECOSYSTEMS: RESILIENCE ---
    sensors.append(WorldBankSensor(
        sensor_id="wb-protected-areas",
        indicator="ER.PTD.TOTL.ZS",
        scope="ecosystems:resilience",
        domain="ecology",
        normalize_fn=_normalize_protected_areas,
        indicator_name="Terrestrial protected areas (% of total land area)",
        country="WLD",
    ))

    return sensors


# ---------------------------------------------------------------------------
# Background observation loop
# ---------------------------------------------------------------------------

def _ensure_live_observation_telemetry(registry: SensorRegistry, world_model):
    telemetry = getattr(world_model, "live_observation_telemetry", None)
    if telemetry is None:
        telemetry = LiveObservationTelemetry()
        world_model.live_observation_telemetry = telemetry

    telemetry.mark_enabled(registry.sensor_count)

    if not hasattr(world_model, "live_updated_entities"):
        world_model.live_updated_entities = set()

    return telemetry


def run_observation_loop(
    registry: SensorRegistry,
    world_model,
    interval_seconds: int = 3600,
    stop_event=None,
    telemetry: Optional[LiveObservationTelemetry] = None,
):
    """Continuously observe and update the world model.

    Runs registry.observe_all() -> world_model.update() on a timer.
    Designed to run in a daemon thread.

    Parameters
    ----------
    registry : SensorRegistry
        Registry containing all live sensors.
    world_model : WorldModel
        The Bayesian world model to update with observations.
    interval_seconds : int
        Seconds between observation cycles. Default 3600 (1 hour).
        World Bank data updates daily at most, so hourly is sufficient.
    stop_event : threading.Event, optional
        If provided, the loop exits when this event is set.
    telemetry : LiveObservationTelemetry, optional
        Runtime telemetry object exposed through `world_model.status()`.
    """
    import threading

    if stop_event is None:
        stop_event = threading.Event()

    if telemetry is None:
        telemetry = _ensure_live_observation_telemetry(registry, world_model)
    else:
        world_model.live_observation_telemetry = telemetry
        telemetry.mark_enabled(registry.sensor_count)
        if not hasattr(world_model, "live_updated_entities"):
            world_model.live_updated_entities = set()

    while not stop_event.is_set():
        telemetry.start_observation()
        corrections_before = len(getattr(world_model, "correction_log", []))
        try:
            measurements = registry.observe_all()
            updates = []
            if measurements:
                updates = world_model.update(measurements)
                for u in updates:
                    entity = u.get("entity")
                    if entity:
                        world_model.live_updated_entities.add(entity)
                now = datetime.now(timezone.utc).isoformat()
                correction_delta = max(
                    0,
                    len(getattr(world_model, "correction_log", [])) - corrections_before,
                )
                telemetry.finish_observation(
                    measurement_count=len(measurements),
                    update_count=len(updates),
                    correction_count=correction_delta,
                )
                print(
                    f"[LIVE SENSOR] {now} - Observed {len(measurements)} "
                    f"measurements, updated {len(updates)} beliefs"
                )
                for u in updates:
                    print(
                        f"  - {u['entity']}: posterior={u['posterior']:.3f}, "
                        f"uncertainty={u['uncertainty']:.3f}"
                    )
            else:
                now = datetime.now(timezone.utc).isoformat()
                telemetry.finish_observation(
                    measurement_count=0,
                    update_count=0,
                    correction_count=0,
                )
                print(f"[LIVE SENSOR] {now} - No measurements returned (APIs may be unavailable)")
        except Exception as e:
            now = datetime.now(timezone.utc).isoformat()
            telemetry.record_failure(e)
            print(f"[LIVE SENSOR] {now} - Observation error: {e}")

        # Wait for the interval or until stop is requested
        stop_event.wait(timeout=interval_seconds)


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Testing live sensors...")
    print()

    sensors = create_live_sensors()
    print(f"Created {len(sensors)} live sensors:")
    for s in sensors:
        print(f"  - {s.sensor_id}: {s.scope} ({s.domain})")
    print()

    # Test one sensor
    print("Testing wb-life-expectancy (World Bank API)...")
    le_sensor = sensors[0]
    measurements = le_sensor.observe()
    if measurements:
        m = measurements[0]
        print(f"  Value (normalized): {m.value}")
        print(f"  Uncertainty: {m.uncertainty}")
        print(f"  CI: {m.confidence_interval}")
        print(f"  Source: {m.source}")
        print(f"  Temporal: {m.temporal_range}")
        print(f"  Methodology: {m.methodology}")
        print("[OK] Live sensor returned real data")
    else:
        print(f"  Error: {le_sensor._last_error}")
        print("[WARN] Sensor returned no data (API may be unreachable)")
    print()

    # Test GDP sensor
    print("Testing wb-gdp-per-capita (World Bank API)...")
    gdp_sensor = sensors[3]
    measurements = gdp_sensor.observe()
    if measurements:
        m = measurements[0]
        print(f"  Value (normalized): {m.value}")
        print(f"  Uncertainty: {m.uncertainty}")
        print(f"  Methodology: {m.methodology}")
        print("[OK] GDP sensor returned real data")
    else:
        print(f"  Error: {gdp_sensor._last_error}")
    print()

    print("Testing wb-gini-index (multi-country fallback)...")
    gini_sensor = sensors[4]
    measurements = gini_sensor.observe()
    if measurements:
        m = measurements[0]
        print(f"  Value (normalized): {m.value}")
        print(f"  Uncertainty: {m.uncertainty}")
        print(f"  Sample size: {m.sample_size}")
        print(f"  Methodology: {m.methodology}")
        print("[OK] Gini sensor returned aggregated data")
    else:
        print(f"  Error: {gini_sensor._last_error}")
