#!/usr/bin/env python3
"""
tools/baseline_manager.py

Manages per-user behavioral baselines for the 14-day silent learning period.

During the first 14 days after onboarding, the system collects daily
aggregated IoT metrics without sending any reports to the family.  Once
14 days of valid data are collected the baseline (averages + standard
deviations) is computed automatically, the user status flips to "active",
and the L1 router is allowed to generate reports.

Typical flow:
    mgr = BaselineManager(Path("memory/user_baselines"))
    mgr.create_user("anon_user_abc123")
    mgr.add_daily_log("anon_user_abc123", {"date": "2025-01-15", ...})
    ...  # repeat for 14 days
    if mgr.is_learning_period_complete("anon_user_abc123"):
        mgr.compute_baseline("anon_user_abc123")
    if mgr.is_report_allowed("anon_user_abc123"):
        deviations = mgr.compare_to_baseline("anon_user_abc123", current)
"""

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LEARNING_PERIOD_DAYS = 14
USER_ID_PATTERN = re.compile(r"^anon_user_[a-z0-9]+$")

# Metric field names that map daily_logs → baseline metric groups
_SLEEP_FIELDS = {
    "bed_exit_night_count": ("bed_exit_night_avg", "bed_exit_night_std_dev"),
    "tossing_duration_minutes": ("tossing_avg_duration_minutes", "tossing_std_dev_minutes"),
}
_MOBILITY_FIELDS = {
    "walking_speed_avg": ("walking_speed_baseline_normal", "walking_speed_std_dev"),
    "rise_attempt_fails": ("rise_attempt_fail_rate", None),
}
_ACTIVITY_FIELDS = {
    "max_inactivity_hours": ("inactivity_avg_daytime_hours", "inactivity_std_dev_hours"),
    "appliance_interaction_minutes": (
        "appliance_interaction_avg_duration_minutes",
        "appliance_interaction_std_dev_minutes",
    ),
}

# Threshold multiplier — deviations beyond mean ± (DEVIATION_SIGMA * std_dev)
# are flagged.  Default 2.0 ≈ 95 % confidence under normal distribution.
DEVIATION_SIGMA = 2.0

# When baseline walking speed std-dev is large, slow threshold = mean − 1 std-dev.
# This ratio is the floor: slow threshold is never below this fraction of normal.
WALKING_SPEED_SLOW_RATIO = 0.7

# Minimum std-dev used when recorded variance is zero.  Prevents infinite
# sigma values for constant-value metrics during the learning period.
ZERO_VARIANCE_EPSILON = 1e-6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mean(values: list[float]) -> float:
    """Return arithmetic mean, or 0.0 for empty lists."""
    return statistics.mean(values) if values else 0.0


def _stdev(values: list[float]) -> float:
    """Return population standard deviation (pstdev) for the given values."""
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# BaselineManager
# ---------------------------------------------------------------------------

class BaselineManager:
    """Create, load, update and query per-user behavioral baselines."""

    def __init__(self, baselines_dir: Path | str) -> None:
        self.baselines_dir = Path(baselines_dir)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    # -- path helper --------------------------------------------------------

    def _user_path(self, user_id: str) -> Path:
        return self.baselines_dir / f"{user_id}.json"

    # -- CRUD ---------------------------------------------------------------

    def create_user(self, user_id: str) -> dict:
        """Initialise a new user in *learning* mode.

        Raises ``ValueError`` if the user_id format is invalid or the user
        already exists.
        """
        if not USER_ID_PATTERN.match(user_id):
            raise ValueError(
                f"user_id must match pattern anon_user_[a-z0-9]+, got: {user_id}"
            )
        path = self._user_path(user_id)
        if path.exists():
            raise ValueError(f"User {user_id} already exists")

        baseline: dict[str, Any] = {
            "user_id": user_id,
            "status": "learning",
            "learning_start_date": _now_iso(),
            "baseline_established_date": None,
            "data_collection_days": 0,
            "sleep_metrics": None,
            "mobility_metrics": None,
            "activity_metrics": None,
            "daily_logs": [],
        }
        self.save_user_baseline(user_id, baseline)
        return baseline

    def get_user_baseline(self, user_id: str) -> dict:
        """Load an existing baseline from disk.

        Raises ``FileNotFoundError`` if the user file does not exist.
        """
        path = self._user_path(user_id)
        if not path.exists():
            raise FileNotFoundError(f"No baseline found for user {user_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_user_baseline(self, user_id: str, baseline: dict) -> None:
        """Persist a baseline dict to ``{user_id}.json``."""
        path = self._user_path(user_id)
        path.write_text(
            json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # -- daily log ingestion ------------------------------------------------

    def add_daily_log(self, user_id: str, daily_metrics: dict) -> dict:
        """Append one day's aggregated metrics during the learning period.

        ``daily_metrics`` must contain at least ``"date"`` (YYYY-MM-DD).
        Duplicate dates are silently ignored.

        Returns the updated baseline dict.

        Raises ``ValueError`` if the user is not in *learning* status or the
        maximum 14 daily logs have already been collected.
        """
        baseline = self.get_user_baseline(user_id)

        if baseline["status"] != "learning":
            raise ValueError(
                f"User {user_id} is not in learning mode (status={baseline['status']})"
            )
        if baseline["data_collection_days"] >= LEARNING_PERIOD_DAYS:
            raise ValueError(
                f"User {user_id} already has {LEARNING_PERIOD_DAYS} days of data"
            )
        if "date" not in daily_metrics:
            raise ValueError("daily_metrics must include a 'date' field")

        # Prevent duplicate dates
        existing_dates = {log["date"] for log in baseline["daily_logs"]}
        if daily_metrics["date"] in existing_dates:
            return baseline

        baseline["daily_logs"].append(daily_metrics)
        baseline["data_collection_days"] = len(baseline["daily_logs"])
        self.save_user_baseline(user_id, baseline)
        return baseline

    # -- baseline computation -----------------------------------------------

    def is_learning_period_complete(self, user_id: str) -> bool:
        """Return ``True`` when 14 days of valid data have been collected."""
        baseline = self.get_user_baseline(user_id)
        return baseline["data_collection_days"] >= LEARNING_PERIOD_DAYS

    def compute_baseline(self, user_id: str) -> dict:
        """Compute averages and standard deviations from daily_logs.

        Transitions the user from *learning* → *active*.

        Raises ``ValueError`` if fewer than 14 days of data exist.
        """
        baseline = self.get_user_baseline(user_id)
        if baseline["data_collection_days"] < LEARNING_PERIOD_DAYS:
            raise ValueError(
                f"Need {LEARNING_PERIOD_DAYS} days of data, "
                f"only have {baseline['data_collection_days']}"
            )

        logs = baseline["daily_logs"]

        # -- sleep ---
        baseline["sleep_metrics"] = self._compute_group(logs, _SLEEP_FIELDS)

        # -- mobility ---
        mob = self._compute_group(logs, _MOBILITY_FIELDS)
        # Derive the "slow" threshold as mean − 1 std-dev (or 70 % of normal)
        normal = mob.get("walking_speed_baseline_normal", 0.0)
        std = mob.get("walking_speed_std_dev", 0.0)
        mob["walking_speed_baseline_slow"] = max(normal - std, normal * WALKING_SPEED_SLOW_RATIO)
        baseline["mobility_metrics"] = mob

        # -- activity ---
        baseline["activity_metrics"] = self._compute_group(logs, _ACTIVITY_FIELDS)

        baseline["status"] = "active"
        baseline["baseline_established_date"] = _now_iso()

        self.save_user_baseline(user_id, baseline)
        return baseline

    @staticmethod
    def _compute_group(
        logs: list[dict],
        field_map: dict[str, tuple[str, Optional[str]]],
    ) -> dict[str, float]:
        """Compute mean (and optionally std-dev) for each field in *field_map*.

        ``field_map`` maps a daily-log key to a tuple of
        ``(avg_baseline_key, stddev_baseline_key | None)``.
        """
        result: dict[str, float] = {}
        for log_key, (avg_key, std_key) in field_map.items():
            values = [
                log[log_key] for log in logs if log_key in log and log[log_key] is not None
            ]
            result[avg_key] = _mean(values)
            if std_key is not None:
                result[std_key] = _stdev(values)
        return result

    # -- report gating ------------------------------------------------------

    def is_report_allowed(self, user_id: str) -> bool:
        """Return ``True`` only when the user baseline is established."""
        baseline = self.get_user_baseline(user_id)
        return baseline["status"] == "active"

    # -- deviation comparison -----------------------------------------------

    def compare_to_baseline(
        self,
        user_id: str,
        current_metrics: dict,
    ) -> dict[str, Any]:
        """Compare current event metrics against the stored baseline.

        Returns a dict with ``"deviations"`` (list of flagged fields) and
        ``"is_anomalous"`` (bool — True if any deviation exceeds the
        threshold).

        Each deviation entry contains:
            field, current_value, baseline_mean, baseline_std_dev,
            deviation_sigma, direction ("above" | "below")

        Raises ``ValueError`` if the user is still in learning mode.
        """
        baseline = self.get_user_baseline(user_id)
        if baseline["status"] != "active":
            raise ValueError(
                f"Cannot compare — user {user_id} baseline not yet established"
            )

        deviations: list[dict[str, Any]] = []

        comparisons: list[tuple[str, dict, dict[str, tuple[str, Optional[str]]]]] = [
            ("sleep_metrics", baseline.get("sleep_metrics") or {}, _SLEEP_FIELDS),
            ("mobility_metrics", baseline.get("mobility_metrics") or {}, _MOBILITY_FIELDS),
            ("activity_metrics", baseline.get("activity_metrics") or {}, _ACTIVITY_FIELDS),
        ]

        for _group_name, group_baseline, field_map in comparisons:
            for log_key, (avg_key, std_key) in field_map.items():
                if log_key not in current_metrics:
                    continue
                current_val = current_metrics[log_key]
                mean_val = group_baseline.get(avg_key, 0.0)
                std_val = group_baseline.get(std_key, 0.0) if std_key else 0.0

                effective_std = std_val if std_val > ZERO_VARIANCE_EPSILON else ZERO_VARIANCE_EPSILON
                sigma = abs(current_val - mean_val) / effective_std

                if sigma >= DEVIATION_SIGMA:
                    deviations.append({
                        "field": log_key,
                        "current_value": current_val,
                        "baseline_mean": mean_val,
                        "baseline_std_dev": std_val,
                        "deviation_sigma": round(sigma, 2),
                        "direction": "above" if current_val > mean_val else "below",
                    })

        return {
            "deviations": deviations,
            "is_anomalous": len(deviations) > 0,
        }
