#!/usr/bin/env python3
"""
Sensor framework for observing outcomes across any domain.

A sensor is anything that produces a measurement: a dataset, an API,
a computed statistic, a satellite image analysis, a medical record aggregate.
Sensors do not judge. They measure, and report how confident they are.

Every measurement includes:
- What was observed (the value)
- How confident we are (uncertainty bounds)
- What's missing (known gaps in coverage)
- Where it came from (provenance chain)
- When it was observed (temporal bounds)
- What it applies to (scope: individuals, populations, ecosystems, etc.)

Limitations:
- Uncertainty estimates are self-reported by the sensor. A sensor can lie
  about how confident it is. Cross-validation via AggregateSensor helps,
  but cannot fully solve this.
- "Scope" is a free-text field. Two sensors claiming the same scope may
  actually be measuring different populations. Always check methodology.
- Sample sizes can be misleading. A large sample of the wrong population
  is worse than a small sample of the right one.
"""

import hashlib
import json
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Measurement — the atomic unit of observation
# ---------------------------------------------------------------------------


def _canonical_json(obj: Any) -> str:
    """Produce a deterministic JSON string for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _compute_measurement_hash(
    value: Any,
    source: str,
    methodology: str,
    temporal_range: Tuple[str, str],
    scope: str,
    recorded_at: datetime,
) -> str:
    """SHA-256 of a canonical representation for audit trail."""
    canonical = _canonical_json({
        "value": value,
        "source": source,
        "methodology": methodology,
        "temporal_range": temporal_range,
        "scope": scope,
        "recorded_at": recorded_at.isoformat(),
    })
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Measurement:
    """A single observation from a sensor.

    Every measurement is honest about what it does and does not know.
    The uncertainty field is not optional decoration -- it is the most
    important part of the measurement after the value itself. A measurement
    that claims zero uncertainty is almost certainly wrong about that claim.
    """

    value: Any
    """The observed quantity. Could be a number, a dict, a list -- whatever
    the sensor produces. Interpretation depends on the sensor's domain."""

    uncertainty: float
    """How uncertain this measurement is, on a 0-1 scale.
    0.0 = we are certain (almost never true in practice).
    1.0 = we have no idea (the measurement is noise).
    Most honest measurements land between 0.1 and 0.7."""

    confidence_interval: Tuple[float, float]
    """Lower and upper bounds of the plausible range for the value.
    For non-numeric values, this may be (0.0, 0.0) as a placeholder.
    The interval width should be consistent with the uncertainty field."""

    sample_size: Optional[int] = None
    """Number of observations this measurement is based on.
    None means the sensor did not report a sample size, which is itself
    a form of information (the sensor may not know, or may not want to say)."""

    confounders: List[str] = field(default_factory=list)
    """Known factors that were not controlled for. For example:
    'income_not_controlled', 'selection_bias_likely', 'seasonal_effects'.
    An empty list does NOT mean there are no confounders -- it means
    none were identified. There are always confounders."""

    missing: List[str] = field(default_factory=list)
    """Known gaps in coverage. For example:
    'excludes_patients_who_did_not_return', 'rural_areas_undersampled',
    'non_english_speakers_excluded'. Be specific."""

    source: str = "unknown"
    """Provenance -- where did this data come from? A URL, a dataset name,
    a methodology reference. 'unknown' is honest; a fabricated source is not."""

    methodology: str = "unspecified"
    """How was this value computed or collected? Free text, but be specific.
    'survey', 'administrative_records', 'satellite_imagery', 'model_output'."""

    temporal_range: Tuple[str, str] = ("unknown", "unknown")
    """(start_date, end_date) of the observation period.
    ISO-8601 date strings. 'unknown' is acceptable when the sensor
    genuinely does not know the time bounds."""

    scope: str = "unspecified"
    """What population or entity this measurement applies to.
    Examples: 'humans', 'felines', 'ecosystem:pacific_northwest',
    'hospital:xyz_diagnostic', 'global'. Be specific about boundaries."""

    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """When this measurement was recorded (not when the underlying data
    was collected -- that is temporal_range)."""

    measurement_hash: str = ""
    """SHA-256 of the canonical form of this measurement. Computed
    automatically if not provided. Used for audit trails and
    deduplication."""

    def __post_init__(self):
        """Compute the measurement hash if not already set."""
        if not self.measurement_hash:
            self.measurement_hash = _compute_measurement_hash(
                self.value,
                self.source,
                self.methodology,
                self.temporal_range,
                self.scope,
                self.recorded_at,
            )

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dictionary."""
        return {
            "value": self.value,
            "uncertainty": self.uncertainty,
            "confidence_interval": list(self.confidence_interval),
            "sample_size": self.sample_size,
            "confounders": self.confounders,
            "missing": self.missing,
            "source": self.source,
            "methodology": self.methodology,
            "temporal_range": list(self.temporal_range),
            "scope": self.scope,
            "recorded_at": self.recorded_at.isoformat(),
            "measurement_hash": self.measurement_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Measurement":
        """Deserialize from a dictionary."""
        recorded = d.get("recorded_at")
        if isinstance(recorded, str):
            recorded = datetime.fromisoformat(recorded)
        elif recorded is None:
            recorded = datetime.now(timezone.utc)

        return cls(
            value=d["value"],
            uncertainty=d["uncertainty"],
            confidence_interval=tuple(d.get("confidence_interval", (0.0, 0.0))),
            sample_size=d.get("sample_size"),
            confounders=d.get("confounders", []),
            missing=d.get("missing", []),
            source=d.get("source", "unknown"),
            methodology=d.get("methodology", "unspecified"),
            temporal_range=tuple(d.get("temporal_range", ("unknown", "unknown"))),
            scope=d.get("scope", "unspecified"),
            recorded_at=recorded,
            measurement_hash=d.get("measurement_hash", ""),
        )


# ---------------------------------------------------------------------------
# Sensor — base class for all observation sources
# ---------------------------------------------------------------------------


class Sensor(ABC):
    """Base class for anything that produces measurements.

    A sensor observes something about the world and reports what it saw,
    along with how confident it is. Sensors do not make judgments or
    recommendations -- that is the world model's job.

    Subclasses must implement observe() to produce measurements.
    """

    def __init__(self, sensor_id: str, domain: str, scope: str):
        """
        Parameters
        ----------
        sensor_id : str
            Unique identifier for this sensor instance.
        domain : str
            The domain this sensor operates in. Examples: 'healthcare',
            'criminal_justice', 'ecology', 'animal_welfare', 'education'.
        scope : str
            What population or system this sensor observes. Examples:
            'humans', 'shelter_cats:northeast_us', 'ecosystem:coral_reef'.
        """
        self.sensor_id = sensor_id
        self.domain = domain
        self.scope = scope
        self._last_observation: Optional[datetime] = None
        self._observation_count: int = 0
        self._error_count: int = 0
        self._last_error: Optional[str] = None

    @abstractmethod
    def observe(self) -> List[Measurement]:
        """Produce measurements from this sensor.

        Returns a list because a single observation event may produce
        multiple measurements (e.g., a dataset sensor might report
        accuracy, fairness, and coverage as separate measurements).

        Implementations should catch their own exceptions and return
        an empty list on failure, incrementing _error_count.
        """
        ...

    def validate(self, measurement: Measurement) -> bool:
        """Check internal consistency of a measurement.

        This is a basic sanity check, not a guarantee of correctness.
        A measurement can pass validation and still be wrong.

        Checks:
        - uncertainty is in [0, 1]
        - confidence interval lower <= upper (for numeric values)
        - sample_size is non-negative if provided
        - measurement_hash is non-empty
        """
        if not (0.0 <= measurement.uncertainty <= 1.0):
            return False

        lo, hi = measurement.confidence_interval
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            if lo > hi:
                return False

        if measurement.sample_size is not None and measurement.sample_size < 0:
            return False

        if not measurement.measurement_hash:
            return False

        return True

    def uncertainty_of(self, measurement: Measurement) -> float:
        """Compute combined uncertainty for a measurement.

        Combines the stated uncertainty with penalties for known gaps:
        - Each confounder adds a small penalty (the more confounders,
          the less we should trust the measurement).
        - Each missing coverage item adds a penalty.
        - Small sample sizes add uncertainty.

        The result is clamped to [0, 1].

        This is a heuristic, not a rigorous statistical method.
        It exists to make uncertainty visible, not to compute it precisely.
        """
        base = measurement.uncertainty

        # Penalty for confounders: each one adds 0.02, capped at 0.2
        confounder_penalty = min(len(measurement.confounders) * 0.02, 0.2)

        # Penalty for missing coverage: each gap adds 0.03, capped at 0.2
        missing_penalty = min(len(measurement.missing) * 0.03, 0.2)

        # Penalty for small sample size
        sample_penalty = 0.0
        if measurement.sample_size is not None:
            if measurement.sample_size < 30:
                sample_penalty = 0.3
            elif measurement.sample_size < 100:
                sample_penalty = 0.15
            elif measurement.sample_size < 1000:
                sample_penalty = 0.05

        combined = base + confounder_penalty + missing_penalty + sample_penalty
        return min(combined, 1.0)

    def health(self) -> dict:
        """Report the health status of this sensor."""
        return {
            "sensor_id": self.sensor_id,
            "domain": self.domain,
            "scope": self.scope,
            "last_observation": (
                self._last_observation.isoformat()
                if self._last_observation
                else None
            ),
            "observation_count": self._observation_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "status": "healthy" if self._error_count == 0 else "degraded",
        }


# ---------------------------------------------------------------------------
# PublicDatasetSensor — wraps data_sources.py
# ---------------------------------------------------------------------------


class PublicDatasetSensor(Sensor):
    """A sensor that pulls from public datasets via data_sources.py.

    This sensor wraps the data loading infrastructure in data_sources.py
    and converts raw dataset records into Measurements with proper
    uncertainty annotations.

    Limitations:
    - The underlying data_sources.load_data_source() is not yet implemented
      and returns mock data. This sensor will return mock measurements
      until that is fixed.
    - Public datasets have their own biases and gaps. This sensor reports
      what the dataset says, not what is true.
    """

    def __init__(
        self,
        sensor_id: str,
        domain: str,
        scope: str,
        data_source: Any,
        value_extractor: Optional[Callable] = None,
    ):
        """
        Parameters
        ----------
        data_source : DataSource
            A data_sources.DataSource instance to pull from.
        value_extractor : callable, optional
            A function that takes a list of raw records and returns
            (value, uncertainty, confidence_interval). If not provided,
            the sensor returns a count of records with high uncertainty.
        """
        super().__init__(sensor_id, domain, scope)
        self._data_source = data_source
        self._value_extractor = value_extractor

    def observe(self) -> List[Measurement]:
        """Pull data from the public dataset and produce measurements.

        Currently returns mock data because data_sources.load_data_source()
        is not yet implemented. The measurements are honest about this.
        """
        try:
            from data_sources import load_data_source

            records = load_data_source(self._data_source)

            if self._value_extractor:
                value, uncertainty, ci = self._value_extractor(records)
            else:
                value = len(records)
                uncertainty = 0.8  # high uncertainty for a raw count
                ci = (0.0, float(len(records) * 2))

            m = Measurement(
                value=value,
                uncertainty=uncertainty,
                confidence_interval=ci,
                sample_size=len(records),
                confounders=["dataset_selection_bias"],
                missing=["load_data_source_not_yet_implemented"]
                if self._data_source.is_mock
                else [],
                source=self._data_source.url,
                methodology=f"public_dataset:{self._data_source.name}",
                temporal_range=("unknown", "unknown"),
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
# ComputedSensor — runs a computation over other sensors' outputs
# ---------------------------------------------------------------------------


class ComputedSensor(Sensor):
    """A sensor that computes derived measurements from other sensors.

    For example: compute the accuracy gap between two demographic groups
    using raw outcome data from a PublicDatasetSensor.

    The computation function receives a list of measurements from the
    input sensors and must return a list of new measurements. The
    computed measurements should have higher uncertainty than their
    inputs (information is lost in aggregation, never gained).
    """

    def __init__(
        self,
        sensor_id: str,
        domain: str,
        scope: str,
        input_sensors: List[Sensor],
        compute_fn: Callable[[List[Measurement]], List[Measurement]],
    ):
        """
        Parameters
        ----------
        input_sensors : list[Sensor]
            The sensors whose outputs are fed into compute_fn.
        compute_fn : callable
            A function that takes a flat list of measurements from all
            input sensors and returns a list of new derived measurements.
        """
        super().__init__(sensor_id, domain, scope)
        self._input_sensors = input_sensors
        self._compute_fn = compute_fn

    def observe(self) -> List[Measurement]:
        """Collect inputs from all input sensors, then compute.

        If any input sensor fails, we still compute with whatever
        measurements we got, but increase uncertainty.
        """
        try:
            all_inputs: List[Measurement] = []
            failed_sensors = 0

            for sensor in self._input_sensors:
                try:
                    measurements = sensor.observe()
                    all_inputs.extend(measurements)
                except Exception:
                    failed_sensors += 1

            if not all_inputs:
                self._error_count += 1
                self._last_error = "no input measurements available"
                return []

            results = self._compute_fn(all_inputs)

            # Increase uncertainty if some input sensors failed
            if failed_sensors > 0:
                ratio = failed_sensors / len(self._input_sensors)
                for m in results:
                    m.uncertainty = min(m.uncertainty + ratio * 0.3, 1.0)
                    m.missing.append(
                        f"{failed_sensors}_of_{len(self._input_sensors)}_input_sensors_failed"
                    )

            self._last_observation = datetime.now(timezone.utc)
            self._observation_count += 1
            return results

        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            return []


# ---------------------------------------------------------------------------
# AggregateSensor — combines independent sensors observing the same thing
# ---------------------------------------------------------------------------


class AggregateSensor(Sensor):
    """Combines multiple sensors observing the same phenomenon.

    When independent sources agree, uncertainty shrinks. When they
    disagree, uncertainty grows. This is the closest thing we have
    to ground truth without actually having ground truth.

    The aggregation method:
    1. Collect measurements from all sub-sensors.
    2. For numeric values: compute a weighted average where weights
       are inversely proportional to uncertainty.
    3. Uncertainty of the aggregate is smaller than any individual
       sensor's uncertainty IF they agree, larger if they disagree.

    Limitations:
    - "Independent" is an assumption. If two sensors use the same
      underlying data, combining them does not reduce uncertainty.
    - Numeric averaging only works for numeric values. Non-numeric
      measurements are returned as-is with a note.
    """

    def __init__(
        self,
        sensor_id: str,
        domain: str,
        scope: str,
        sub_sensors: List[Sensor],
    ):
        super().__init__(sensor_id, domain, scope)
        self._sub_sensors = sub_sensors

    def observe(self) -> List[Measurement]:
        """Observe from all sub-sensors and aggregate.

        Returns one aggregate measurement if the values are numeric,
        or all individual measurements with a correlation note if not.
        """
        try:
            all_measurements: List[Measurement] = []
            for sensor in self._sub_sensors:
                try:
                    all_measurements.extend(sensor.observe())
                except Exception:
                    pass

            if not all_measurements:
                self._error_count += 1
                self._last_error = "no sub-sensor produced measurements"
                return []

            # Try numeric aggregation
            numeric_values = []
            uncertainties = []
            for m in all_measurements:
                if isinstance(m.value, (int, float)) and not math.isnan(m.value):
                    numeric_values.append(float(m.value))
                    uncertainties.append(max(m.uncertainty, 0.01))  # avoid div by zero

            if len(numeric_values) >= 2:
                # Weighted average: weight = 1 / uncertainty
                weights = [1.0 / u for u in uncertainties]
                total_weight = sum(weights)
                weighted_avg = sum(
                    v * w for v, w in zip(numeric_values, weights)
                ) / total_weight

                # Aggregate uncertainty: shrinks if sources agree
                variance_of_values = sum(
                    w * (v - weighted_avg) ** 2
                    for v, w in zip(numeric_values, weights)
                ) / total_weight
                disagreement = math.sqrt(variance_of_values) if variance_of_values > 0 else 0

                # Base uncertainty: inverse of total weight, normalized
                base_uncertainty = 1.0 / (1.0 + total_weight)
                # Add disagreement penalty
                agg_uncertainty = min(base_uncertainty + disagreement * 0.5, 1.0)

                # Confidence interval from the range of values
                ci_lo = min(numeric_values) - disagreement
                ci_hi = max(numeric_values) + disagreement

                total_sample = sum(
                    m.sample_size for m in all_measurements
                    if m.sample_size is not None
                )
                all_confounders = list(set(
                    c for m in all_measurements for c in m.confounders
                ))
                all_missing = list(set(
                    g for m in all_measurements for g in m.missing
                ))
                all_sources = ", ".join(set(m.source for m in all_measurements))

                aggregate = Measurement(
                    value=round(weighted_avg, 6),
                    uncertainty=round(agg_uncertainty, 4),
                    confidence_interval=(round(ci_lo, 4), round(ci_hi, 4)),
                    sample_size=total_sample if total_sample > 0 else None,
                    confounders=all_confounders + [
                        "independence_assumed_but_not_verified"
                    ],
                    missing=all_missing,
                    source=f"aggregate({all_sources})",
                    methodology=f"weighted_average_of_{len(numeric_values)}_sensors",
                    temporal_range=all_measurements[0].temporal_range,
                    scope=self.scope,
                )

                self._last_observation = datetime.now(timezone.utc)
                self._observation_count += 1
                return [aggregate]

            # Non-numeric: return all measurements, can't aggregate
            for m in all_measurements:
                m.confounders.append("not_aggregated_non_numeric")

            self._last_observation = datetime.now(timezone.utc)
            self._observation_count += 1
            return all_measurements

        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            return []


# ---------------------------------------------------------------------------
# SensorRegistry — tracks all registered sensors
# ---------------------------------------------------------------------------


class SensorRegistry:
    """Registry of all active sensors.

    Tracks sensors by ID, domain, and scope. Reports health status
    and last observation times. Does not own the sensors -- they can
    be used independently.
    """

    def __init__(self):
        self._sensors: Dict[str, Sensor] = {}

    def register(self, sensor: Sensor) -> None:
        """Register a sensor. Overwrites if sensor_id already exists."""
        self._sensors[sensor.sensor_id] = sensor

    def unregister(self, sensor_id: str) -> bool:
        """Remove a sensor. Returns True if it existed."""
        return self._sensors.pop(sensor_id, None) is not None

    def get(self, sensor_id: str) -> Optional[Sensor]:
        """Look up a sensor by ID."""
        return self._sensors.get(sensor_id)

    def by_domain(self, domain: str) -> List[Sensor]:
        """Return all sensors in a given domain."""
        return [s for s in self._sensors.values() if s.domain == domain]

    def by_scope(self, scope: str) -> List[Sensor]:
        """Return all sensors matching a scope."""
        return [s for s in self._sensors.values() if s.scope == scope]

    def all_sensors(self) -> List[Sensor]:
        """Return all registered sensors."""
        return list(self._sensors.values())

    def observe_all(self) -> List[Measurement]:
        """Run observe() on every sensor and collect all measurements.

        Sensors that fail are skipped -- their health status will reflect
        the failure. This method never raises.
        """
        all_measurements: List[Measurement] = []
        for sensor in self._sensors.values():
            try:
                measurements = sensor.observe()
                all_measurements.extend(measurements)
            except Exception:
                sensor._error_count += 1
        return all_measurements

    def health_report(self) -> List[dict]:
        """Return health status for every registered sensor."""
        return [s.health() for s in self._sensors.values()]

    @property
    def sensor_count(self) -> int:
        return len(self._sensors)

    @property
    def domains(self) -> List[str]:
        """All unique domains across registered sensors."""
        return list(set(s.domain for s in self._sensors.values()))

    def status(self) -> dict:
        """Summary status of the registry."""
        healths = self.health_report()
        healthy = sum(1 for h in healths if h["status"] == "healthy")
        return {
            "total_sensors": self.sensor_count,
            "healthy_sensors": healthy,
            "degraded_sensors": self.sensor_count - healthy,
            "domains": self.domains,
            "sensors": healths,
        }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Test Measurement
    m = Measurement(
        value=0.73,
        uncertainty=0.15,
        confidence_interval=(0.65, 0.81),
        sample_size=500,
        confounders=["income_not_controlled"],
        missing=["rural_areas_undersampled"],
        source="test_dataset",
        methodology="simulated",
        scope="humans:test_population",
    )
    assert m.measurement_hash, "Hash should be computed"
    assert m.validate if hasattr(m, "validate") else True

    # Test sensor validation
    class DummySensor(Sensor):
        def observe(self):
            return [Measurement(
                value=42,
                uncertainty=0.5,
                confidence_interval=(30.0, 54.0),
                source="dummy",
                methodology="test",
                scope="test",
            )]

    ds = DummySensor("test-sensor", "testing", "test")
    measurements = ds.observe()
    assert len(measurements) == 1
    assert ds.validate(measurements[0])

    # Test uncertainty_of
    unc = ds.uncertainty_of(measurements[0])
    assert unc >= measurements[0].uncertainty

    # Test registry
    registry = SensorRegistry()
    registry.register(ds)
    assert registry.sensor_count == 1
    assert registry.get("test-sensor") is ds
    assert len(registry.by_domain("testing")) == 1

    all_m = registry.observe_all()
    assert len(all_m) == 1

    status = registry.status()
    assert status["total_sensors"] == 1

    print("[OK] Measurement dataclass works")
    print("[OK] Sensor base class works")
    print("[OK] SensorRegistry works")
    print(f"[OK] Measurement hash: {m.measurement_hash[:16]}...")
    print(f"[OK] Combined uncertainty: {unc}")
