# JSON Event Schema — IoT Edge Devices

This document defines the JSON schema for behavioral events emitted by
privacy-preserving, non-contact IoT edge devices (thermal / mmWave radar)
installed in an elderly person's home.

---

## Event Object Schema

Every event emitted by the edge device is a JSON object with the following
common fields plus event-specific fields.

### Common Fields (all events)

| Field | Type | Required | Description |
|---|---|---|---|
| `event` | `string` | Yes | Event type identifier. One of the 8 recognized types. |
| `timestamp` | `string` (ISO 8601) | Yes | UTC timestamp when the event was detected. Example: `"2026-03-19T02:45:00Z"` |
| `room` | `string` | No | Room where the event was detected. Values: `"bedroom"`, `"bathroom"`, `"kitchen"`, `"living_room"`, `"hallway"`, `"entrance"` |
| `confidence` | `number` (0.0–1.0) | No | Sensor confidence score for this detection. Default: `1.0` |

### Recognized Event Types

```
bed_exit
tossing_and_turning
walking
posture_change
rise_attempt_fail
wandering
inactivity
appliance_interaction
```

---

## Event Type Definitions

### 1. `bed_exit`

Detected when the elder leaves the bed. Relevant for nighttime sleep disruption
analysis.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"bed_exit"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | When the exit was detected |
| `count` | `integer` | Yes | `≥ 1` | Number of bed exits in the aggregation window |
| `time` | `string` | Yes | Time range, e.g. `"02:00-05:00"` | Time span covering the exits |
| `room` | `string` | No | `"bedroom"` | Always bedroom for bed events |

**Routing threshold:** `count ≥ 2` during nighttime window (23:00–06:00).

**Example:**
```json
{
  "event": "bed_exit",
  "timestamp": "2026-03-19T03:15:00Z",
  "count": 4,
  "time": "01:00-05:00",
  "room": "bedroom",
  "confidence": 0.95
}
```

---

### 2. `tossing_and_turning`

Detected when the elder exhibits prolonged restless movement in bed without
fully exiting.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"tossing_and_turning"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | Start of the restless period |
| `duration_minutes` | `number` | Yes | `> 0` | Total duration of restless movement |
| `time` | `string` | No | Time range | Time span of the restless period |
| `room` | `string` | No | `"bedroom"` | — |

**Routing threshold:** `duration_minutes ≥ 30`.

**Example:**
```json
{
  "event": "tossing_and_turning",
  "timestamp": "2026-03-19T01:30:00Z",
  "duration_minutes": 45,
  "time": "01:30-02:15",
  "room": "bedroom",
  "confidence": 0.88
}
```

---

### 3. `walking`

Detected gait activity. The edge device estimates relative walking speed and
flags anomalous slowness compared to the user's baseline.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"walking"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | When the walking was detected |
| `speed` | `string` | Yes | `"normal"`, `"slow"`, `"anomalous_slow"` | Speed classification relative to baseline |
| `speed_value` | `number` | No | `> 0` (arbitrary unit) | Raw speed measurement from sensor |
| `duration_minutes` | `number` | No | `> 0` | Duration of the walking episode |
| `room` | `string` | No | Any room | Where the walking was detected |

**Speed classifications:**
- `"normal"` — Within expected range of baseline.
- `"slow"` — Below expected range but not yet anomalous.
- `"anomalous_slow"` — ≥ 30% below baseline. This classification is assigned
  by the edge device and is the routing trigger. The L1 router does not
  independently compute the percentage — when `speed == "anomalous_slow"`, the
  30% threshold has already been met.

**Routing threshold:** `speed == "anomalous_slow"` (i.e., ≥ 30% below
`mobility_metrics.walking_speed_baseline_normal`).

**Example:**
```json
{
  "event": "walking",
  "timestamp": "2026-03-19T10:20:00Z",
  "speed": "anomalous_slow",
  "speed_value": 0.42,
  "duration_minutes": 8,
  "room": "hallway",
  "confidence": 0.91
}
```

---

### 4. `posture_change`

Detected change in body posture. The critical subtype `sudden_drop` indicates
a possible fall.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"posture_change"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | When the posture change was detected |
| `posture_subtype` | `string` | Yes | `"normal"`, `"sudden_drop"` | Type of posture change |
| `room` | `string` | No | Any room | Where the change was detected |

**⚠️ CRITICAL:** `posture_subtype: "sudden_drop"` is classified as
`URGENT_FALL_RISK`. Any single occurrence **bypasses ALL suppression logic** —
alert history, trend checks, learning period — and routes **immediately** to
`L2-mobility-fall-expert`.

**Routing threshold:** `posture_subtype == "sudden_drop"` — any single event.

**Example (URGENT):**
```json
{
  "event": "posture_change",
  "timestamp": "2026-03-19T08:12:33Z",
  "posture_subtype": "sudden_drop",
  "room": "bathroom",
  "confidence": 0.97
}
```

**Example (normal — not routed):**
```json
{
  "event": "posture_change",
  "timestamp": "2026-03-19T09:00:00Z",
  "posture_subtype": "normal",
  "room": "living_room",
  "confidence": 0.85
}
```

---

### 5. `rise_attempt_fail`

Detected when the elder attempts to stand from a seated or lying position but
fails (does not achieve standing posture).

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"rise_attempt_fail"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | When the failed attempt was detected |
| `count` | `integer` | Yes | `≥ 1` | Number of consecutive failed attempts |
| `consecutive` | `boolean` | Yes | `true` / `false` | Whether the failures were consecutive |
| `room` | `string` | No | Any room | Where the attempt occurred |

**Routing threshold:** `count ≥ 2` AND `consecutive == true`.

**Example:**
```json
{
  "event": "rise_attempt_fail",
  "timestamp": "2026-03-19T14:30:00Z",
  "count": 2,
  "consecutive": true,
  "room": "living_room",
  "confidence": 0.89
}
```

---

### 6. `wandering`

Detected when the elder exhibits purposeless walking patterns, especially
during nighttime hours.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"wandering"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | When wandering was detected |
| `time` | `string` | No | Time range, e.g. `"02:00-03:30"` | Duration of wandering |
| `duration_minutes` | `number` | No | `> 0` | Total wandering duration |
| `rooms_visited` | `array` of `string` | No | Room identifiers | Rooms traversed during wandering |
| `room` | `string` | No | Any room | Starting room of wandering episode |

**Routing threshold:** Event occurs during the nighttime window 23:00–05:00.

**Example:**
```json
{
  "event": "wandering",
  "timestamp": "2026-03-19T02:15:00Z",
  "time": "02:15-03:45",
  "duration_minutes": 90,
  "rooms_visited": ["bedroom", "hallway", "kitchen", "hallway", "living_room"],
  "room": "bedroom",
  "confidence": 0.82
}
```

---

### 7. `inactivity`

Detected when no meaningful movement is observed from the elder for an
extended period during daytime hours.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"inactivity"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | Start of the inactivity period |
| `duration_hours` | `number` | Yes | `> 0` | Duration of inactivity in hours |
| `time` | `string` | No | Time range | Time span of inactivity |
| `room` | `string` | No | Any room | Where the elder remained inactive |

**Routing threshold:** `duration_hours ≥ 4` during daytime hours.

**Example:**
```json
{
  "event": "inactivity",
  "timestamp": "2026-03-19T09:00:00Z",
  "duration_hours": 5.5,
  "time": "09:00-14:30",
  "room": "living_room",
  "confidence": 0.93
}
```

---

### 8. `appliance_interaction`

Detected when the elder interacts with a household appliance. Anomalously long
interactions may indicate cognitive difficulty.

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `event` | `string` | Yes | `"appliance_interaction"` | — |
| `timestamp` | `string` | Yes | ISO 8601 | When the interaction started |
| `appliance_id` | `string` | Yes | e.g. `"microwave"`, `"tv"`, `"stove"`, `"refrigerator"`, `"washing_machine"` | Identifier of the appliance |
| `interaction_duration_minutes` | `number` | Yes | `> 0` | Duration of the interaction |
| `interaction_duration` | `string` | No | `"normal"`, `"long"`, `"anomalously_long"` | Classification relative to baseline |
| `room` | `string` | No | Any room | Where the appliance is located |

**Routing threshold:** `interaction_duration == "anomalously_long"` (≥ 2 standard
deviations above `activity_metrics.appliance_interaction_avg_duration_minutes`).

**Example:**
```json
{
  "event": "appliance_interaction",
  "timestamp": "2026-03-19T12:00:00Z",
  "appliance_id": "microwave",
  "interaction_duration_minutes": 22,
  "interaction_duration": "anomalously_long",
  "room": "kitchen",
  "confidence": 0.87
}
```

---

## Router Input Format

The L1 router receives a single JSON payload per processing cycle (typically
every 4–6 hours, or on-demand for urgent events).

```json
{
  "user_id": "anon_user_abc123",
  "user_status": "active",
  "processing_window": {
    "start": "2026-03-17T00:00:00Z",
    "end": "2026-03-19T23:59:59Z"
  },
  "logs": [
    {
      "event": "bed_exit",
      "timestamp": "2026-03-18T01:15:00Z",
      "count": 3,
      "time": "01:00-04:30",
      "room": "bedroom"
    },
    {
      "event": "bed_exit",
      "timestamp": "2026-03-19T02:45:00Z",
      "count": 2,
      "time": "02:00-04:00",
      "room": "bedroom"
    },
    {
      "event": "walking",
      "timestamp": "2026-03-19T10:20:00Z",
      "speed": "anomalous_slow",
      "speed_value": 0.42,
      "duration_minutes": 8,
      "room": "hallway"
    },
    {
      "event": "posture_change",
      "timestamp": "2026-03-19T08:12:33Z",
      "posture_subtype": "normal",
      "room": "living_room"
    },
    {
      "event": "inactivity",
      "timestamp": "2026-03-18T10:00:00Z",
      "duration_hours": 2.5,
      "time": "10:00-12:30",
      "room": "living_room"
    }
  ],
  "baseline": {
    "user_id": "anon_user_abc123",
    "status": "active",
    "learning_start_date": "2026-03-01",
    "baseline_computed_date": "2026-03-15",
    "sleep_metrics": {
      "bed_exit_night_avg": 1.2,
      "bed_exit_night_std_dev": 0.4,
      "tossing_avg_duration_minutes": 12.0,
      "tossing_std_dev_minutes": 5.0
    },
    "mobility_metrics": {
      "walking_speed_baseline_normal": 0.65,
      "walking_speed_baseline_slow": 0.455,
      "walking_speed_std_dev": 0.08,
      "rise_attempt_fail_rate": 0.05
    },
    "activity_metrics": {
      "inactivity_avg_daytime_hours": 2.0,
      "inactivity_std_dev_hours": 0.8,
      "appliance_interaction_avg_duration_minutes": 8.0,
      "appliance_interaction_std_dev_minutes": 3.0
    }
  }
}
```

### Field Reference — Router Input

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | `string` | Yes | Anonymized user identifier. Pattern: `anon_user_[a-z0-9]+` |
| `user_status` | `string` | Yes | `"learning"` (14-day baseline collection), `"active"` (normal operations), or `"paused"` (data collection paused) |
| `processing_window` | `object` | No | Start/end timestamps of the event window being processed |
| `processing_window.start` | `string` | No | ISO 8601 UTC timestamp |
| `processing_window.end` | `string` | No | ISO 8601 UTC timestamp |
| `logs` | `array` | Yes | Array of event objects (see event types above) |
| `baseline` | `object \| null` | Yes | Personal baseline metrics. `null` when `user_status` is `"learning"` |
| `baseline.sleep_metrics` | `object` | — | Nighttime behavior baselines |
| `baseline.mobility_metrics` | `object` | — | Walking and movement baselines |
| `baseline.activity_metrics` | `object` | — | Daytime activity and appliance baselines |

### Baseline Metrics Reference

| Metric Path | Type | Description |
|---|---|---|
| `sleep_metrics.bed_exit_night_avg` | `number` | Mean nighttime bed exits per night |
| `sleep_metrics.bed_exit_night_std_dev` | `number` | Standard deviation of nighttime bed exits |
| `sleep_metrics.tossing_avg_duration_minutes` | `number` | Mean tossing/turning duration in minutes |
| `sleep_metrics.tossing_std_dev_minutes` | `number` | Standard deviation of tossing duration |
| `mobility_metrics.walking_speed_baseline_normal` | `number` | Mean normal walking speed (arbitrary units) |
| `mobility_metrics.walking_speed_baseline_slow` | `number` | Slow threshold: `max(mean − 1σ, 0.7 × mean)` |
| `mobility_metrics.walking_speed_std_dev` | `number` | Standard deviation of walking speed |
| `mobility_metrics.rise_attempt_fail_rate` | `number` | Proportion of rise attempts that fail (0.0–1.0) |
| `activity_metrics.inactivity_avg_daytime_hours` | `number` | Mean daytime inactivity hours |
| `activity_metrics.inactivity_std_dev_hours` | `number` | Standard deviation of daytime inactivity |
| `activity_metrics.appliance_interaction_avg_duration_minutes` | `number` | Mean appliance interaction duration |
| `activity_metrics.appliance_interaction_std_dev_minutes` | `number` | Standard deviation of appliance interaction duration |

---

## Router Output Format

The L1 router produces a JSON object containing routing decisions, suppressed
events, and processing metadata. See the SKILL.md Output Format section for the
full schema and field definitions.

```json
{
  "user_id": "anon_user_abc123",
  "timestamp": "2026-03-20T08:15:00Z",
  "routing_decisions": [
    {
      "route_to": "L2-sleep-pattern-expert",
      "alert_class": "sleep_issue",
      "priority": "normal",
      "triggering_events": [],
      "suppression_applied": false,
      "suppression_reason": "Multi-day trend confirmed.",
      "baseline_comparison": {},
      "trend_summary": "..."
    }
  ],
  "suppressed_events": [
    {
      "event": "inactivity",
      "alert_class": "cognitive_issue",
      "suppression_reason": "Below threshold (2.5h < 4h required).",
      "logged_for_future_trend": false
    }
  ],
  "metadata": {
    "total_events_processed": 5,
    "events_meeting_threshold": 2,
    "events_routed": 1,
    "events_suppressed": 0,
    "events_below_threshold": 3,
    "user_status": "active",
    "processing_timestamp": "2026-03-20T08:15:00Z"
  }
}
```

### Alert Classes

| Alert Class | Description | Target L2 Skill |
|---|---|---|
| `sleep_issue` | Nighttime disruptions (bed exits, restlessness) | `L2-sleep-pattern-expert` |
| `mobility_issue` | Gait anomalies, rise failures | `L2-mobility-fall-expert` |
| `cognitive_issue` | Wandering, prolonged inactivity, appliance confusion | `L2-dementia-behavior-expert` |
| `URGENT_FALL_RISK` | Possible fall detected (sudden_drop) | `L2-mobility-fall-expert` |

### Priority Levels

| Priority | When Used | Behavior |
|---|---|---|
| `"normal"` | All standard routed events | L2 expert processes at normal cadence |
| `"IMMEDIATE"` | `posture_change: sudden_drop` only | L2 expert processes immediately; `generate_line_report` called with `urgency_level: "attention_needed"` |
