"""
Data sources for AI bias analysis.

This project does not generate original bias measurements. It aggregates
and displays published research.
"""

from dataclasses import dataclass
from typing import Any, List


@dataclass
class DataSource:
    """A citable, auditable data source."""

    name: str
    url: str
    description: str
    license: str
    citation: str
    is_mock: bool  # True if synthetic/demo data


# ---------------------------------------------------------------------------
# Real public datasets (summaries only — we do not reproduce raw data)
# ---------------------------------------------------------------------------

COMPAS_SOURCE = DataSource(
    name="ProPublica COMPAS Recidivism Analysis",
    url="https://github.com/propublica/compas-analysis",
    description=(
        "ProPublica's 2016 investigation into the COMPAS recidivism risk-score "
        "tool used in Broward County, Florida. The analysis examined roughly "
        "7,000 arrestees scored by COMPAS between 2013 and 2014."
    ),
    license="Apache 2.0 (data); see repository for details",
    citation=(
        "Angwin, J., Larson, J., Mattu, S., & Kirchner, L. (2016). "
        '"Machine Bias." ProPublica, May 23, 2016. '
        "https://www.propublica.org/article/machine-bias-risk-assessments-in-criminal-sentencing"
    ),
    is_mock=False,
)


def get_compas_summary() -> dict[str, Any]:
    """Return a summary of the ProPublica COMPAS recidivism analysis.

    **Important**: This is a SUMMARY of published public research, not our
    own analysis. The numbers below come from ProPublica's publicly released
    methodology and data repository.

    Source
    ------
    ProPublica, "Machine Bias", May 23 2016.
    https://github.com/propublica/compas-analysis
    """
    return {
        "source": COMPAS_SOURCE.name,
        "source_url": COMPAS_SOURCE.url,
        "citation": COMPAS_SOURCE.citation,
        "is_mock": False,
        "methodology_note": (
            "This is a SUMMARY of ProPublica's published research. "
            "We did not perform this analysis ourselves."
        ),
        "key_findings": [
            (
                "Black defendants were roughly twice as likely as white "
                "defendants to be misclassified as higher risk but not "
                "actually re-offend (false positive)."
            ),
            (
                "White defendants were more likely to be misclassified as "
                "lower risk but go on to commit additional crimes "
                "(false negative)."
            ),
            (
                "Overall prediction accuracy was similar across racial "
                "groups (~60%), but error types were distributed unevenly."
            ),
        ],
        "dataset_size_approx": 7_000,
        "time_period": "2013-2014",
        "jurisdiction": "Broward County, Florida, USA",
    }


# ---------------------------------------------------------------------------
# Data-loading stub (not yet implemented)
# ---------------------------------------------------------------------------


def load_data_source(source: DataSource) -> list[dict[str, Any]]:
    """Download and cache data from the source URL.

    Not yet implemented -- currently returns an empty list with a warning.

    When implemented this function will:
    1. Check a local cache directory for a previously downloaded copy.
    2. If not cached, download the dataset from ``source.url``.
    3. Parse into a list of dicts suitable for analysis.
    4. Cache the result locally for subsequent calls.

    Parameters
    ----------
    source : DataSource
        The data source to load.

    Returns
    -------
    list[dict]
        Parsed records from the source. Until real loading is implemented,
        returns an empty list so callers receive a consistent return type
        without synthetic data leaking into measurements.
    """
    print(
        f"WARNING: load_data_source() is not yet implemented. "
        f"Returning [] instead of real data from '{source.name}'. "
        f"See {source.url} to download the dataset manually."
    )
    return []
