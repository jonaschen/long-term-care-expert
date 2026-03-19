#!/usr/bin/env python3
"""
tests/test_baseline_manager.py

Unit tests for the BaselineManager (14-day silent learning period).
Uses /tmp/test_baselines/ so the real memory/ directory is never touched.
"""

import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

# Ensure tools/ is importable
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from baseline_manager import LEARNING_PERIOD_DAYS, BaselineManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
TEST_DIR = Path("/tmp/test_baselines")


@pytest.fixture(autouse=True)
def clean_test_dir():
    """Create a fresh test directory before each test, clean up after."""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(TEST_DIR, ignore_errors=True)


@pytest.fixture
def mgr() -> BaselineManager:
    return BaselineManager(TEST_DIR)


def _make_daily_metrics(start_date: date, day_index: int) -> dict:
    """Generate plausible daily metrics for a given day offset."""
    d = start_date + timedelta(days=day_index)
    return {
        "date": d.isoformat(),
        "bed_exit_night_count": 1 + (day_index % 3),
        "tossing_duration_minutes": 15.0 + day_index * 0.5,
        "walking_speed_avg": 0.8 - day_index * 0.01,
        "rise_attempt_fails": day_index % 2,
        "max_inactivity_hours": 2.0 + day_index * 0.1,
        "appliance_interaction_minutes": 30.0 + day_index,
    }


def _fill_learning_period(mgr: BaselineManager, user_id: str) -> date:
    """Add 14 daily logs and return the start date used."""
    start = date(2025, 1, 1)
    for i in range(LEARNING_PERIOD_DAYS):
        mgr.add_daily_log(user_id, _make_daily_metrics(start, i))
    return start


# ---------------------------------------------------------------------------
# User creation
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_creates_learning_user(self, mgr: BaselineManager):
        baseline = mgr.create_user("anon_user_abc123")
        assert baseline["status"] == "learning"
        assert baseline["data_collection_days"] == 0
        assert baseline["baseline_established_date"] is None
        assert baseline["daily_logs"] == []

    def test_file_persisted(self, mgr: BaselineManager):
        mgr.create_user("anon_user_xyz")
        assert (TEST_DIR / "anon_user_xyz.json").exists()

    def test_invalid_user_id_rejected(self, mgr: BaselineManager):
        with pytest.raises(ValueError, match="must match pattern"):
            mgr.create_user("bad-user-id")

    def test_duplicate_user_rejected(self, mgr: BaselineManager):
        mgr.create_user("anon_user_dup")
        with pytest.raises(ValueError, match="already exists"):
            mgr.create_user("anon_user_dup")


# ---------------------------------------------------------------------------
# Daily log ingestion
# ---------------------------------------------------------------------------

class TestAddDailyLog:
    def test_adds_log_and_increments_count(self, mgr: BaselineManager):
        mgr.create_user("anon_user_log1")
        result = mgr.add_daily_log("anon_user_log1", {
            "date": "2025-01-01",
            "bed_exit_night_count": 2,
        })
        assert result["data_collection_days"] == 1
        assert len(result["daily_logs"]) == 1

    def test_duplicate_date_ignored(self, mgr: BaselineManager):
        mgr.create_user("anon_user_dup2")
        mgr.add_daily_log("anon_user_dup2", {"date": "2025-01-01"})
        result = mgr.add_daily_log("anon_user_dup2", {"date": "2025-01-01"})
        assert result["data_collection_days"] == 1

    def test_missing_date_raises(self, mgr: BaselineManager):
        mgr.create_user("anon_user_nodate")
        with pytest.raises(ValueError, match="date"):
            mgr.add_daily_log("anon_user_nodate", {"bed_exit_night_count": 1})

    def test_rejects_after_14_days(self, mgr: BaselineManager):
        mgr.create_user("anon_user_full")
        _fill_learning_period(mgr, "anon_user_full")
        with pytest.raises(ValueError, match="14 days"):
            mgr.add_daily_log("anon_user_full", {"date": "2025-01-16"})

    def test_rejects_non_learning_user(self, mgr: BaselineManager):
        mgr.create_user("anon_user_act")
        _fill_learning_period(mgr, "anon_user_act")
        mgr.compute_baseline("anon_user_act")
        with pytest.raises(ValueError, match="not in learning mode"):
            mgr.add_daily_log("anon_user_act", {"date": "2025-02-01"})


# ---------------------------------------------------------------------------
# Learning period completion check
# ---------------------------------------------------------------------------

class TestLearningPeriodComplete:
    def test_incomplete(self, mgr: BaselineManager):
        mgr.create_user("anon_user_inc")
        mgr.add_daily_log("anon_user_inc", {"date": "2025-01-01"})
        assert mgr.is_learning_period_complete("anon_user_inc") is False

    def test_complete(self, mgr: BaselineManager):
        mgr.create_user("anon_user_cmp")
        _fill_learning_period(mgr, "anon_user_cmp")
        assert mgr.is_learning_period_complete("anon_user_cmp") is True


# ---------------------------------------------------------------------------
# Baseline computation
# ---------------------------------------------------------------------------

class TestComputeBaseline:
    def test_computes_and_activates(self, mgr: BaselineManager):
        mgr.create_user("anon_user_comp")
        _fill_learning_period(mgr, "anon_user_comp")
        result = mgr.compute_baseline("anon_user_comp")

        assert result["status"] == "active"
        assert result["baseline_established_date"] is not None
        assert result["sleep_metrics"] is not None
        assert result["mobility_metrics"] is not None
        assert result["activity_metrics"] is not None

    def test_sleep_metrics_reasonable(self, mgr: BaselineManager):
        mgr.create_user("anon_user_slp")
        _fill_learning_period(mgr, "anon_user_slp")
        result = mgr.compute_baseline("anon_user_slp")

        sleep = result["sleep_metrics"]
        assert sleep["bed_exit_night_avg"] > 0
        assert sleep["bed_exit_night_std_dev"] >= 0
        assert sleep["tossing_avg_duration_minutes"] > 0

    def test_mobility_slow_threshold(self, mgr: BaselineManager):
        mgr.create_user("anon_user_mob")
        _fill_learning_period(mgr, "anon_user_mob")
        result = mgr.compute_baseline("anon_user_mob")

        mob = result["mobility_metrics"]
        assert mob["walking_speed_baseline_slow"] < mob["walking_speed_baseline_normal"]
        assert mob["walking_speed_baseline_slow"] > 0

    def test_insufficient_data_raises(self, mgr: BaselineManager):
        mgr.create_user("anon_user_few")
        mgr.add_daily_log("anon_user_few", {"date": "2025-01-01"})
        with pytest.raises(ValueError, match="Need 14 days"):
            mgr.compute_baseline("anon_user_few")


# ---------------------------------------------------------------------------
# Report gating
# ---------------------------------------------------------------------------

class TestReportGating:
    def test_blocked_during_learning(self, mgr: BaselineManager):
        mgr.create_user("anon_user_gate")
        assert mgr.is_report_allowed("anon_user_gate") is False

    def test_allowed_after_baseline(self, mgr: BaselineManager):
        mgr.create_user("anon_user_gate2")
        _fill_learning_period(mgr, "anon_user_gate2")
        mgr.compute_baseline("anon_user_gate2")
        assert mgr.is_report_allowed("anon_user_gate2") is True


# ---------------------------------------------------------------------------
# Deviation comparison
# ---------------------------------------------------------------------------

class TestCompareToBaseline:
    @pytest.fixture
    def active_user(self, mgr: BaselineManager) -> str:
        uid = "anon_user_cmp1"
        mgr.create_user(uid)
        _fill_learning_period(mgr, uid)
        mgr.compute_baseline(uid)
        return uid

    def test_no_deviation_for_normal_values(self, mgr, active_user):
        baseline = mgr.get_user_baseline(active_user)
        sleep = baseline["sleep_metrics"]
        result = mgr.compare_to_baseline(active_user, {
            "bed_exit_night_count": sleep["bed_exit_night_avg"],
            "tossing_duration_minutes": sleep["tossing_avg_duration_minutes"],
        })
        assert result["is_anomalous"] is False
        assert result["deviations"] == []

    def test_deviation_flagged_for_extreme_value(self, mgr, active_user):
        result = mgr.compare_to_baseline(active_user, {
            "bed_exit_night_count": 99,
        })
        assert result["is_anomalous"] is True
        assert len(result["deviations"]) == 1
        assert result["deviations"][0]["field"] == "bed_exit_night_count"
        assert result["deviations"][0]["direction"] == "above"

    def test_deviation_below_baseline(self, mgr, active_user):
        result = mgr.compare_to_baseline(active_user, {
            "walking_speed_avg": 0.01,
        })
        assert result["is_anomalous"] is True
        devs = [d for d in result["deviations"] if d["field"] == "walking_speed_avg"]
        assert len(devs) == 1
        assert devs[0]["direction"] == "below"

    def test_compare_rejects_learning_user(self, mgr: BaselineManager):
        mgr.create_user("anon_user_lrn")
        with pytest.raises(ValueError, match="not yet established"):
            mgr.compare_to_baseline("anon_user_lrn", {"bed_exit_night_count": 1})


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_user_not_found(self, mgr: BaselineManager):
        with pytest.raises(FileNotFoundError, match="No baseline found"):
            mgr.get_user_baseline("anon_user_ghost")

    def test_sparse_daily_logs(self, mgr: BaselineManager):
        """Logs with only the required 'date' field still compute a baseline."""
        mgr.create_user("anon_user_sparse")
        start = date(2025, 3, 1)
        for i in range(LEARNING_PERIOD_DAYS):
            mgr.add_daily_log("anon_user_sparse", {
                "date": (start + timedelta(days=i)).isoformat(),
            })
        result = mgr.compute_baseline("anon_user_sparse")
        assert result["status"] == "active"
        # All averages should be 0.0 when no metric data provided
        assert result["sleep_metrics"]["bed_exit_night_avg"] == 0.0

    def test_baselines_dir_created_automatically(self):
        new_dir = TEST_DIR / "nested" / "deep"
        mgr = BaselineManager(new_dir)
        mgr.create_user("anon_user_nest")
        assert (new_dir / "anon_user_nest.json").exists()

    def test_paused_user_blocks_reports(self, mgr: BaselineManager):
        mgr.create_user("anon_user_pause")
        baseline = mgr.get_user_baseline("anon_user_pause")
        baseline["status"] = "paused"
        mgr.save_user_baseline("anon_user_pause", baseline)
        assert mgr.is_report_allowed("anon_user_pause") is False
