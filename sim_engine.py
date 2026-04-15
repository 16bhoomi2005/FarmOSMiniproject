"""
SmartFarmSimEngine — Rice Field Simulation Engine
================================================
Provides realistic simulated data for all 9 rice fields.
Used as an OFFLINE FALLBACK when real GEE / MongoDB data
is unavailable. All values are rice (Kharif / Rabi paddy)
domain-accurate.

Usage
-----
    import streamlit as st
    from sim_engine import SmartFarmSimEngine

    if "farm_sim" not in st.session_state:
        st.session_state.farm_sim = SmartFarmSimEngine()

    engine = st.session_state.farm_sim
    data   = engine.fields          # dict of field_name → field_data
    engine.update_live()            # ±3 % random walk refresh
"""

import numpy as np
import random
import streamlit as st
from datetime import datetime, timedelta


# ─── Constants ──────────────────────────────────────────────────────────────

FIELD_NAMES = ["North", "South", "East", "West", "Center", "NW", "NE", "SW", "SE"]
THREATS = ["Rice Blast", "Brown Spot", "Sheath Blight", "False Smut", "Stem Borer", "Leaf Folder"]

GROWTH_STAGES = [
    "Germination", "Seedling", "Tillering",
    "Panicle Init.", "Booting", "Heading",
    "Grain Fill", "Maturity"
]

WEATHER_EVENTS = ["Rain", "Drought", "Flood"]


# ─── Helper ──────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, value)))


def _rw(value: float, lo: float, hi: float, pct: float = 0.03) -> float:
    """Apply a ±pct random walk, clamped to [lo, hi]."""
    delta = value * pct * random.uniform(-1, 1)
    return _clamp(value + delta, lo, hi)


# ─── Main Engine ─────────────────────────────────────────────────────────────

class SmartFarmSimEngine:
    """
    Generates and stores simulation data for 9 rice fields.
    Persisted in st.session_state so values survive page navigation.
    """

    SEED = 42

    def __init__(self):
        rng = np.random.default_rng(self.SEED)
        self.fields: dict = {}
        self.alerts: list = []
        self.current_week: int = 8          # Simulated week (1-based)
        self.created_at: datetime = datetime.now()

        for name in FIELD_NAMES:
            self.fields[name] = self._generate_field(name, rng)

        # Time-series (shared structure, per-field)
        self._ts_cache: dict = {}
        for name in FIELD_NAMES:
            self._ts_cache[name] = self._generate_time_series(name, rng)

        self._check_thresholds()

    # ── Field Generation ─────────────────────────────────────────────────────

    def _generate_field(self, name: str, rng: np.random.Generator) -> dict:
        """Generate one field's complete sensor + AI snapshot."""

        # Spectral indices
        ndvi  = float(rng.uniform(0.55, 0.85))
        ndre  = float(rng.uniform(0.40, 0.70))
        evi   = float(rng.uniform(0.30, 0.65))
        ndwi  = float(rng.uniform(0.20, 0.55))
        savi  = float(rng.uniform(0.35, 0.70))
        stress = round(float(1.0 - (ndvi * 0.7 + (1-ndwi) * 0.3)), 3)
        yield_idx = round(float(ndvi * 0.8 + 0.15), 3)

        # Soil
        moisture    = float(rng.uniform(45, 75))   # Rice likes wetter 45-75%
        ph          = float(rng.uniform(5.5, 7.0)) # Rice: 5.5-7.0
        soil_temp   = float(rng.uniform(22, 32))
        nitrogen    = float(rng.uniform(80, 180))
        phosphorus  = float(rng.uniform(20, 60))
        potassium   = float(rng.uniform(100, 250))

        # Atmosphere
        air_temp     = float(rng.uniform(20, 35))  # Kharif rice range
        humidity     = float(rng.uniform(55, 90))  # Rice likes humidity
        leaf_wetness = float(rng.uniform(0, 100))
        light        = float(rng.uniform(200, 1200))

        # Derived scores
        moisture_score = _clamp((moisture - 35) / (75 - 35), 0, 1)
        ph_score       = _clamp(1 - abs(ph - 6.2) / 1.2, 0, 1)

        # Pest risk per threat (0–100)
        pest_risk: dict = {}
        base_risk = 40 if (leaf_wetness > 70 and 20 <= air_temp <= 32) else 15
        for threat in THREATS:
            noise = float(rng.uniform(-10, 25))
            pest_risk[threat] = _clamp(base_risk + noise, 0, 100)

        avg_pest_risk = float(np.mean(list(pest_risk.values())))
        pest_inverse  = _clamp(1 - avg_pest_risk / 100, 0, 1)

        # Health score
        health_score = (
            ndvi          * 0.35 +
            moisture_score * 0.25 +
            pest_inverse   * 0.25 +
            ph_score       * 0.15
        ) * 100

        # Yield prediction (tonnes/acre, rice: ~2.5–5 t/ac)
        noise_factor = float(rng.uniform(0.92, 1.08))
        yield_pred   = _clamp(health_score * 0.048 * noise_factor, 1.5, 6.0)

        # Top threat
        top_threat = max(pest_risk, key=pest_risk.get)

        return {
            "name":        name,
            "crop":        "Rice (Paddy)",
            "area_acres":  10,
            # Spectral
            "ndvi":        round(ndvi,  3),
            "ndre":        round(ndre,  3),
            "evi":         round(evi,   3),
            "ndwi":        round(ndwi,  3),
            "savi":        round(savi,  3),
            "stress":      stress,
            "yield":       yield_idx,
            # Soil
            "moisture":    round(moisture,   1),
            "ph":          round(ph,         2),
            "soil_temp":   round(soil_temp,  1),
            "nitrogen":    round(nitrogen,   1),
            "phosphorus":  round(phosphorus, 1),
            "potassium":   round(potassium,  1),
            # Atmosphere
            "air_temp":      round(air_temp,     1),
            "humidity":      round(humidity,      1),
            "leaf_wetness":  round(leaf_wetness,  1),
            "light":         round(light,          1),
            # AI outputs
            "health_score":  round(health_score,  1),
            "yield_pred":    round(yield_pred,     2),
            "pest_risk":     {k: round(v, 1) for k, v in pest_risk.items()},
            "top_threat":    top_threat,
            "top_threat_score": round(pest_risk[top_threat], 1),
            # Status
            "status":  "Critical" if health_score < 40 else
                       "Warning"  if health_score < 55 else "Healthy",
            "last_updated": datetime.now().strftime("%H:%M:%S"),
        }

    # ── Time-Series Generation ───────────────────────────────────────────────

    def _generate_time_series(self, name: str, rng: np.random.Generator) -> dict:
        """
        Generate 16-week time series:
          - Weeks 1–12: historical (sine + Gaussian noise)
          - Weeks 13–16: LSTM-simulated forecast (degraded)
        Inject 3 random weather events.
        """
        n_hist = 12
        n_fore = 4
        weeks  = n_hist + n_fore

        # --- NDVI ---
        # Peaks around week 8 (grain fill for rice)
        t = np.arange(1, n_hist + 1)
        ndvi_base = (
            0.45
            + 0.30 * np.sin(np.pi * (t - 1) / (n_hist - 1))    # bell curve 0→1→0
            + float(rng.uniform(-0.05, 0.05))                   # field offset
        )
        noise = rng.normal(0, 0.02, n_hist)
        ndvi_hist = np.clip(ndvi_base + noise, 0.25, 0.92)

        # Forecast: slight regression toward mean + widening noise
        last_ndvi = ndvi_hist[-1]
        ndvi_fore = np.array([
            _clamp(last_ndvi - 0.03 * i + rng.normal(0, 0.03 + i * 0.008), 0.2, 0.9)
            for i in range(1, n_fore + 1)
        ])

        # --- Soil Moisture ---
        sm_base = float(rng.uniform(50, 70))
        sm_hist = np.clip(sm_base + rng.normal(0, 4, n_hist), 30, 85)
        sm_fore = np.array([
            _clamp(sm_hist[-1] + rng.normal(0, 5 + i), 25, 85)
            for i in range(1, n_fore + 1)
        ])

        # --- Health Score ---
        hs_hist = np.clip(ndvi_hist * 80 + rng.normal(0, 3, n_hist), 20, 98)
        hs_fore = np.clip(ndvi_fore * 80 + rng.normal(0, 5, n_fore),  15, 98)

        # --- Weather Events (3 per field, only in historical) ---
        event_weeks = sorted(rng.choice(np.arange(1, n_hist + 1), size=3, replace=False).tolist())
        events = [
            {"week": int(w), "type": random.choice(WEATHER_EVENTS)}
            for w in event_weeks
        ]

        # Apply event effects on NDVI
        for ev in events:
            idx = ev["week"] - 1
            if ev["type"] == "Drought":
                ndvi_hist[idx:idx+2] -= 0.08
            elif ev["type"] == "Flood":
                ndvi_hist[idx:idx+1] -= 0.05
                sm_hist[idx:idx+2] = np.clip(sm_hist[idx:idx+2] + 15, 30, 85)
            # Rain slightly boosts
            elif ev["type"] == "Rain":
                ndvi_hist[idx:idx+2] = np.clip(ndvi_hist[idx:idx+2] + 0.03, 0.25, 0.92)

        ndvi_hist = np.clip(ndvi_hist, 0.22, 0.92)

        # Stage label per week (8 stages over 16 weeks)
        stage_map = {w: GROWTH_STAGES[min(int((w - 1) * len(GROWTH_STAGES) / n_hist), len(GROWTH_STAGES) - 1)]
                     for w in range(1, weeks + 1)}

        return {
            "weeks":          list(range(1, weeks + 1)),
            "ndvi_hist":      [round(float(v), 3) for v in ndvi_hist],
            "ndvi_fore":      [round(float(v), 3) for v in ndvi_fore],
            "sm_hist":        [round(float(v), 1) for v in sm_hist],
            "sm_fore":        [round(float(v), 1) for v in sm_fore],
            "hs_hist":        [round(float(v), 1) for v in hs_hist],
            "hs_fore":        [round(float(v), 1) for v in hs_fore],
            "events":         events,
            "stage_map":      stage_map,
            "is_forecast":    [False] * n_hist + [True] * n_fore,
        }

    # ── Live Update ──────────────────────────────────────────────────────────

    def update_live(self):
        """
        Apply ±3 % random walk to all sensor values.
        Re-compute derived health_score, yield_pred, pest_risk.
        Append new alerts if thresholds are crossed.
        """
        for name, f in self.fields.items():
            f["ndvi"]        = _rw(f["ndvi"],        0.20, 0.95)
            f["ndre"]        = _rw(f["ndre"],        0.20, 0.90)
            f["evi"]         = _rw(f["evi"],         0.15, 0.80)
            f["ndwi"]        = _rw(f["ndwi"],        0.05, 0.75)
            f["savi"]        = _rw(f["savi"],        0.15, 0.80)
            f["moisture"]    = _rw(f["moisture"],    30,   85)
            f["ph"]          = _rw(f["ph"],          5.2,  7.5, 0.005)
            f["soil_temp"]   = _rw(f["soil_temp"],   18,   35)
            f["nitrogen"]    = _rw(f["nitrogen"],    60,   200)
            f["phosphorus"]  = _rw(f["phosphorus"],  15,   70)
            f["potassium"]   = _rw(f["potassium"],   80,   280)
            f["air_temp"]    = _rw(f["air_temp"],    15,   38)
            f["humidity"]    = _rw(f["humidity"],    35,   95)
            f["leaf_wetness"]= _rw(f["leaf_wetness"], 0,   100)
            f["light"]       = _rw(f["light"],       100,  1400)

            # Recompute pest risk
            base_risk = 40 if (f["leaf_wetness"] > 70 and 20 <= f["air_temp"] <= 32) else 15
            for threat in THREATS:
                f["pest_risk"][threat] = _clamp(
                    f["pest_risk"][threat] * random.uniform(0.95, 1.05) + random.uniform(-2, 2),
                    0, 100
                )

            # Recompute scalars
            moisture_score = _clamp((f["moisture"] - 35) / 45, 0, 1)
            ph_score       = _clamp(1 - abs(f["ph"] - 6.2) / 1.5, 0, 1)
            avg_pest       = float(np.mean(list(f["pest_risk"].values())))
            pest_inv       = _clamp(1 - avg_pest / 100, 0, 1)

            f["health_score"] = round(
                (f["ndvi"] * 0.35 + moisture_score * 0.25 + pest_inv * 0.25 + ph_score * 0.15) * 100,
                1
            )
            f["yield_pred"] = round(_clamp(f["health_score"] * 0.048, 1.5, 6.0), 2)
            f["top_threat"] = max(f["pest_risk"], key=f["pest_risk"].get)
            f["top_threat_score"] = round(f["pest_risk"][f["top_threat"]], 1)
            f["status"] = (
                "Critical" if f["health_score"] < 40 else
                "Warning"  if f["health_score"] < 55 else "Healthy"
            )
            f["last_updated"] = datetime.now().strftime("%H:%M:%S")

        self._check_thresholds()

    def sync_with_real_data(self, real_data):
        """
        Forces simulation engine to match real satellite results from GEE.
        Every field is aligned with reality. If no specific plot data exists,
        it inherits the farm mean to maintain global integrity.
        """
        mean_ndvi = real_data.get('mean_ndvi', 0.24)
        mean_ndwi = real_data.get('mean_ndwi', -0.1)
        subplots = real_data.get('subplots', {})

        for name, f in self.fields.items():
            # Match directly by key (North == North, etc.)
            matched_data = subplots.get(name)
            
            # Sync indices
            if matched_data:
                f["ndvi"] = matched_data.get("ndvi", f["ndvi"])
                # Recalculate derived indices from real satellite truth
                f["stress"] = round(1.0 - (f["ndvi"] * 0.8), 3)
                f["yield"]  = round(f["ndvi"] * 0.9, 3)
                f["ndwi"] = float(matched_data.get('ndwi', mean_ndwi))
                f["last_updated"] = f"{real_data.get('last_updated', 'Live')} (Synced)"
            else:
                f["ndvi"] = float(mean_ndvi)
                f["ndwi"] = float(mean_ndwi)
                f["last_updated"] = f"{real_data.get('last_updated', 'Live')} (Sub-Auto)"
                
            # Recalculate all correlated sensors (NPK, Moisture, Yield)
            self._recalculate_derived_scores(f)

        # Update global alerts
        self.alerts = [a for a in self.alerts if a["type"] != "Satellite Alert"]
        if mean_ndvi < 0.35:
            self.alerts.append({
                "type": "Satellite Alert",
                "severity": "Critical",
                "message": f"Farm-wide stress detected: Avg NDVI is {mean_ndvi:.2f}",
                "location": "All Plots"
            })
                
        # Re-run threshold checks to update status & alerts
        self._check_thresholds()

    def _recalculate_derived_scores(self, f):
        """
        Recalculates health_score, yield_pred AND SENSOR VALUES (NPK/Moisture)
        to match the satellite reality. (THE INTEGRITY FIX)
        """
        # 1. MOISTURE CORRELATION (NDWI -> Soil Moisture)
        # NDWI -0.1 to 0.4 range mapping to 0-80% Soil Moisture
        # If NDWI is low (-0.11), soil moisture should be ~10-15%
        f["moisture"] = _clamp((f["ndwi"] + 0.15) * 150, 5, 85)
        moisture_score = _clamp((f["ndwi"] + 0.1) / 0.6, 0, 1) 
        
        # 2. NUTRIENT CORRELATION (NDVI -> NPK)
        # If NDVI is 0.24 (Stressed), Nitrogen and Phosphorus should be deficient
        # Highly stressed crops (NDVI < 0.4) usually correlate with severe deficiency
        if f["ndvi"] < 0.4:
            # Drop nutrients to Deficient/Low ranges
            f["nitrogen"]   = _clamp(f["nitrogen"] * 0.4, 30, 60)   # Target 120-140, so 30-60 is Low
            f["phosphorus"] = _clamp(f["phosphorus"] * 0.35, 10, 22) # Target 40-60, so 10-22 is Deficient
            f["potassium"]  = _clamp(f["potassium"] * 0.5, 30, 70)   # Target 120-150, so 30-70 is Low
        elif f["ndvi"] < 0.6:
            # Medium stress
            f["nitrogen"]   = _clamp(f["nitrogen"] * 0.7, 60, 90)
            f["phosphorus"] = _clamp(f["phosphorus"] * 0.8, 25, 35)

        # 3. DERIVED SCORES
        avg_pest_risk = float(np.mean(list(f["pest_risk"].values())))
        pest_inverse  = _clamp(1 - avg_pest_risk / 100, 0, 1)
        ph_score      = _clamp(1 - abs(f["ph"] - 6.2) / 1.2, 0, 1)

        # Final health score (0-100)
        f["health_score"] = (
            f["ndvi"]      * 0.45 +
            moisture_score * 0.30 +
            pest_inverse   * 0.15 +
            ph_score       * 0.10
        ) * 100

        # Final yield prediction
        f["yield_pred"] = _clamp(f["health_score"] * 0.048 * np.random.uniform(0.95, 1.05), 1.0, 6.0)

    def sync_trends_with_real_data(self, trend_file_path):
        """
        Syncs the 16-week historical cache with real historical trend data.
        """
        import json
        import os
        if not os.path.exists(trend_file_path):
            return

        try:
            with open(trend_file_path, 'r') as f:
                trend_data = json.load(f)
            
            recent = trend_data.get('recent_observations', [])
            if not recent:
                return

            # Extract NDVI values and sort by date
            sorted_obs = sorted(recent, key=lambda x: x['date'])
            real_ndvi_values = [obs['NDVI_mean'] for obs in sorted_obs]
            
            # Map real points into the 12-week historical window
            # We'll stretch/compress the few real points we have across the history
            for name in self._ts_cache:
                ts = self._ts_cache[name]
                n_hist = 12
                
                # Create a baseline from real data
                if len(real_ndvi_values) >= 2:
                    # Interpolate real values into 12 weeks
                    xp = np.linspace(0, 1, len(real_ndvi_values))
                    x  = np.linspace(0, 1, n_hist)
                    new_hist = np.interp(x, xp, real_ndvi_values)
                    
                    # Add a tiny bit of field-specific noise so they aren't identical
                    field_noise = np.random.normal(0, 0.01, n_hist)
                    ts['ndvi_hist'] = [round(float(v), 3) for v in np.clip(new_hist + field_noise, 0.1, 0.95)]
                    
                    # Update health score history to match new NDVI
                    ts['hs_hist'] = [round(float(v * 80 + np.random.uniform(-3, 3)), 1) for v in ts['ndvi_hist']]

        except Exception as e:
            print(f"Trend Sync Error: {e}")

    # ── Threshold Checking ───────────────────────────────────────────────────

    def _check_thresholds(self):
        """Check all fields against thresholds and populate self.alerts."""
        from alert_config import THRESHOLDS
        new_alerts = []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for name, f in self.fields.items():
            # soil_moisture
            if f["moisture"] < THRESHOLDS["soil_moisture"]["critical"]:
                new_alerts.append({
                    "timestamp": ts, "field": name,
                    "type": "Low Moisture", "severity": "Critical",
                    "message": f"Soil moisture critically low: {f['moisture']:.0f}%",
                    "status": "Active"
                })
            elif f["moisture"] < THRESHOLDS["soil_moisture"]["warning"]:
                new_alerts.append({
                    "timestamp": ts, "field": name,
                    "type": "Low Moisture", "severity": "Warning",
                    "message": f"Soil moisture low: {f['moisture']:.0f}%",
                    "status": "Active"
                })

            # health_score
            if f["health_score"] < THRESHOLDS["health_score"]["critical"]:
                new_alerts.append({
                    "timestamp": ts, "field": name,
                    "type": "Crop Health", "severity": "Critical",
                    "message": f"Health score very low: {f['health_score']:.0f}",
                    "status": "Active"
                })

            # pest_risk
            for threat, score in f["pest_risk"].items():
                if score >= THRESHOLDS["pest_risk"]["critical"]:
                    new_alerts.append({
                        "timestamp": ts, "field": name,
                        "type": "Pest Risk", "severity": "Critical",
                        "message": f"{threat} risk critical: {score:.0f}/100",
                        "status": "Active"
                    })
                elif score >= THRESHOLDS["pest_risk"]["warning"]:
                    new_alerts.append({
                        "timestamp": ts, "field": name,
                        "type": "Pest Risk", "severity": "Warning",
                        "message": f"{threat} risk elevated: {score:.0f}/100",
                        "status": "Active"
                    })

            # humidity
            if f["humidity"] >= THRESHOLDS["humidity"]["critical"]:
                new_alerts.append({
                    "timestamp": ts, "field": name,
                    "type": "High Humidity", "severity": "Critical",
                    "message": f"Humidity critical: {f['humidity']:.0f}%",
                    "status": "Active"
                })

        # Keep only last 50 alerts
        self.alerts = (self.alerts + new_alerts)[-50:]

    # ── Convenience Accessors ────────────────────────────────────────────────

    def get_field(self, name: str) -> dict:
        return self.fields.get(name, {})

    def get_time_series(self, name: str) -> dict:
        return self._ts_cache.get(name, {})

    def get_all_ndvi(self) -> dict:
        return {n: f["ndvi"] for n, f in self.fields.items()}

    def get_kpi_summary(self) -> dict:
        """Return farm-wide KPIs."""
        scores    = [f["health_score"] for f in self.fields.values()]
        yields    = [f["yield_pred"]   for f in self.fields.values()]
        criticals = [f for f in self.fields.values() if f["status"] == "Critical"]
        interventions = [f for f in self.fields.values() if f["status"] != "Healthy"]

        return {
            "avg_health":          round(float(np.mean(scores)), 1),
            "total_yield":         round(float(sum(yields)), 2),
            "critical_alerts":     len([a for a in self.alerts if a["severity"] == "Critical"]),
            "fields_need_action":  len(interventions),
        }

    def get_spatial_grid(self, index: str, field_name: str) -> list:
        """
        Generate a 10×10 spatial variation grid for a given spectral index.
        Models within-field variability via Gaussian spatial noise.
        """
        rng  = np.random.default_rng(hash(field_name + index) % (2**31))
        base = self.fields[field_name].get(index.lower(), 0.5)
        # Fix: ensure scale is always positive even if base is negative
        scale = max(0.001, abs(base * 0.08))
        grid = base + rng.normal(0, scale, (10, 10))
        # Clip to index-specific range
        ranges = {
            "ndvi": (0.15, 0.95), "ndre": (0.10, 0.90),
            "evi":  (0.10, 0.80), "ndwi": (0.05, 0.80),
            "savi": (0.10, 0.85),
        }
        lo, hi = ranges.get(index.lower(), (0.0, 1.0))
        return np.clip(grid, lo, hi).tolist()


# ─── Session-State Initialiser (call from any page) ─────────────────────────

def get_sim_engine() -> SmartFarmSimEngine:
    """
    Call this from every page that needs simulation data.
    Initialises once, reuses across reruns. 
    Now robust against stale session objects during updates.
    """
    if "farm_sim" not in st.session_state:
        st.session_state.farm_sim = SmartFarmSimEngine()
    else:
        # Robustness check: Ensure existing instance has all required methods
        # Checking for both spatial sync, trend sync, and reactive recalculation
        has_spatial = hasattr(st.session_state.farm_sim, 'sync_with_real_data')
        has_trends  = hasattr(st.session_state.farm_sim, 'sync_trends_with_real_data')
        has_recalc  = hasattr(st.session_state.farm_sim, '_recalculate_derived_scores')
        
        if not (has_spatial and has_trends and has_recalc):
            st.session_state.farm_sim = SmartFarmSimEngine()
            
    return st.session_state.farm_sim
