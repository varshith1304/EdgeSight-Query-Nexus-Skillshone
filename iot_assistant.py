import re
import pandas as pd

NUMERIC_METRICS = {
    "health": ("ai_health_index_score", "AI health index score"),
    "health score": ("ai_health_index_score", "AI health index score"),
    "bearing temperature": ("bearing_temp_c", "bearing temperature (°C)"),
    "bearing temp": ("bearing_temp_c", "bearing temperature (°C)"),
    "winding temperature": ("motor_winding_temp_c", "motor winding temperature (°C)"),
    "ambient temperature": ("ambient_temp_c", "ambient temperature (°C)"),
    "vibration": ("vibration_rms_mm_s", "RMS vibration (mm/s)"),
    "motor current": ("motor_current_amps", "motor current (A)"),
    "power factor": ("power_factor", "power factor"),
    "differential pressure": ("differential_pressure_bar", "differential pressure (bar)"),
    "overall equipment effectiveness": ("overall_equipment_effectiveness_pct", "overall equipment effectiveness (%)"),
    "oee": ("overall_equipment_effectiveness_pct", "overall equipment effectiveness (%)"),
    "load": ("avg_load_pct_last_7d", "average load over last 7 days (%)"),
    "average load": ("avg_load_pct_last_7d", "average load over last 7 days (%)"),
    "age": ("asset_age_years", "asset age (years)"),
    "operating hours": ("operating_hours_since_last_pm", "operating hours since last preventive maintenance"),
    "failures": ("prior_failures_last_12m", "prior failures in last 12 months"),
}

REFERENCE_NOTES = [
    "AI health index score is a dataset-provided score; interpret it in the context of the dataset and do not assume it is a calibrated probability of failure.",
    "RMS vibration is measured in millimeters per second. Rising vibration can be a maintenance signal, but thresholds depend on equipment type and operating conditions.",
    "Bearing temperature and motor winding temperature are recorded in degrees Celsius.",
    "Preventive maintenance due within seven days is represented by scheduled_pm_due_within_7d.",
    "Unscheduled failure within seven days is represented by unscheduled_failure_within_7d.",
    "Sensor alert counts are available for the last 7 days and the last 30 days.",
    "The dataset contains equipment and maintenance measurements. It does not contain explicit MQTT connectivity status, firmware adoption, credentials, certificates, or GPS coordinates."
]

class IoTAssistant:
    def __init__(self, df):
        self.df = df.copy()
        self.df["observation_date"] = pd.to_datetime(self.df["observation_date"], errors="coerce")

    def _asset_filter(self, q):
        q = q.lower()
        for asset_type in sorted(self.df["asset_type"].dropna().unique(), key=len, reverse=True):
            if asset_type.lower() in q:
                return self.df[self.df["asset_type"].str.lower() == asset_type.lower()], asset_type
        return self.df, None

    def _facility_filter(self, q, data):
        match = re.search(r"\bfac[- ]?0*(\d+)\b", q.lower())
        if match:
            facility = f"FAC-{int(match.group(1)):04d}"
            return data[data["facility_id"].str.upper() == facility], facility
        return data, None

    def _retrieve_notes(self, question):
        # Lightweight local retrieval: rank reference notes by word overlap.
        words = set(re.findall(r"[a-z0-9_]+", question.lower()))
        ranked = []
        for note in REFERENCE_NOTES:
            note_words = set(re.findall(r"[a-z0-9_]+", note.lower()))
            score = len(words & note_words)
            if score:
                ranked.append((score, note))
        ranked.sort(reverse=True)
        return [n for _, n in ranked[:2]]

    def answer(self, question, role="Viewer"):
        q = question.lower().strip()
        data, asset_filter = self._asset_filter(q)
        data, facility_filter = self._facility_filter(q, data)
        filters = []
        if asset_filter:
            filters.append(f"asset_type = {asset_filter}")
        if facility_filter:
            filters.append(f"facility_id = {facility_filter}")
        scope = "Filtered records" if filters else "All records"
        scope_detail = "; ".join(filters) if filters else "no asset-type/facility filter"

        # Access-control demo: Viewer receives aggregate answers, not asset-level rows.
        can_view_asset_rows = role in ("Operations Manager", "Reliability Engineer")
        provenance = f"iot_operations_01.csv; {scope} ({scope_detail}); {len(data):,} matching records."
        notes = self._retrieve_notes(question)
        note = "Reference context: " + " ".join(notes) if notes else ""

        def result(answer, table=None):
            return {"answer": answer, "table": table, "provenance": provenance, "note": note}

        if any(x in q for x in ["how many records", "number of records", "how many assets", "how many equipment", "total assets", "record count"]):
            return result(f"There are {len(data):,} matching equipment records.")
        if "asset type" in q and any(x in q for x in ["how many", "count", "distribution", "most", "breakdown"]):
            t = data["asset_type"].value_counts().rename_axis("Asset type").reset_index(name="Records")
            return result(f"The dataset has {data['asset_type'].nunique()} asset types in the selected scope.", t)
        if "facility" in q and any(x in q for x in ["lowest", "average", "health", "score", "worst"]):
            t = data.groupby("facility_id", as_index=False)["ai_health_index_score"].mean().rename(columns={"ai_health_index_score":"Average health score"}).sort_values("Average health score").head(10)
            return result("These are the 10 facilities with the lowest average AI health index score in the selected scope.", t.round(2))
        if "alert" in q:
            col = "num_sensor_alerts_last_7d" if ("7 day" in q or "7-day" in q or "last 7" in q or "week" in q) else "num_sensor_alerts_last_30d"
            label = "last 7 days" if col.endswith("7d") else "last 30 days"
            if any(x in q for x in ["asset type", "types", "which type", "most"]):
                t = data.groupby("asset_type", as_index=False)[col].sum().rename(columns={col:f"Alerts ({label})"}).sort_values(f"Alerts ({label})", ascending=False)
                return result(f"Sensor alert totals by asset type for the {label}.", t)
            return result(f"Total sensor alerts recorded over the {label}: {int(data[col].sum()):,}. Average per record: {data[col].mean():.2f}.")
        if "maintenance" in q or "preventive" in q or "pm due" in q or "due within" in q:
            due = data["scheduled_pm_due_within_7d"].astype(str).str.lower().eq("yes")
            n = int(due.sum())
            if can_view_asset_rows and any(x in q for x in ["show", "list", "which assets", "asset id", "details"]):
                t = data.loc[due, ["asset_id","asset_type","facility_id","asset_criticality_class","operating_hours_since_last_pm"]].head(100)
                return result(f"{n:,} records are marked as due for scheduled preventive maintenance within 7 days. Showing up to 100 matching records.", t)
            return result(f"{n:,} records ({n / max(len(data),1) * 100:.2f}%) are marked as due for scheduled preventive maintenance within 7 days.")
        if "unscheduled failure" in q or ("failure" in q and ("within 7" in q or "next 7" in q)):
            failed = data["unscheduled_failure_within_7d"].fillna(0).astype(int).eq(1)
            n = int(failed.sum())
            if can_view_asset_rows and any(x in q for x in ["show", "list", "which assets", "asset id", "details"]):
                cols = ["asset_id","asset_type","facility_id","asset_criticality_class","ai_health_index_score","num_sensor_alerts_last_7d"]
                return result(f"{n:,} records have unscheduled_failure_within_7d = 1. Showing up to 100.", data.loc[failed, cols].head(100))
            return result(f"{n:,} records have unscheduled_failure_within_7d = 1 ({n / max(len(data),1) * 100:.2f}% of matching records). This is the dataset's label, not a guarantee of a future real-world event.")
        if "due" in q and "failure" not in q and "maintenance" not in q:
            n = int(data["scheduled_pm_due_within_7d"].astype(str).str.lower().eq("yes").sum())
            return result(f"{n:,} records are marked scheduled_pm_due_within_7d = Yes.")
        if "health" in q or "oee" in q or "effectiveness" in q:
            col = "overall_equipment_effectiveness_pct" if ("oee" in q or "effectiveness" in q) else "ai_health_index_score"
            label = "overall equipment effectiveness (%)" if col.startswith("overall") else "AI health index score"
            if any(x in q for x in ["lowest", "worst", "bottom", "which assets", "show assets", "list assets"]):
                t = data.nsmallest(10, col)[["asset_id","asset_type","facility_id",col,"num_sensor_alerts_last_7d"]].copy() if can_view_asset_rows else data.groupby("asset_type", as_index=False)[col].mean().sort_values(col).head(10)
                return result(f"Lowest {label} results in the selected scope (top 10).", t.round(2))
            return result(f"Average {label}: {data[col].mean():.2f}; median: {data[col].median():.2f}; minimum: {data[col].min():.2f}; maximum: {data[col].max():.2f}.")
        for key, (col, label) in NUMERIC_METRICS.items():
            if key in q:
                if any(x in q for x in ["average", "avg", "mean"]):
                    return result(f"Average {label}: {data[col].mean():.2f} across {data[col].notna().sum():,} non-missing records.")
                if any(x in q for x in ["maximum", "max", "highest", "peak"]):
                    return result(f"Maximum {label}: {data[col].max():.2f}.")
                if any(x in q for x in ["minimum", "min", "lowest"]):
                    return result(f"Minimum {label}: {data[col].min():.2f}.")
                if any(x in q for x in ["show", "list", "which assets", "asset id"]):
                    if not can_view_asset_rows:
                        return result("This demo role can view aggregate information only. Choose an authorised operations or reliability role to see asset-level rows.")
                    t = data[["asset_id","asset_type","facility_id",col]].sort_values(col, ascending=False).head(10)
                    return result(f"Top 10 records by {label}.", t.round(2))
                return result(f"Average {label}: {data[col].mean():.2f}; minimum: {data[col].min():.2f}; maximum: {data[col].max():.2f}.")
        if any(x in q for x in ["oldest", "age"]):
            return result(f"Average asset age: {data['asset_age_years'].mean():.2f} years; oldest record: {data['asset_age_years'].max():.1f} years.")
        if "above rated load" in q or "overload" in q:
            n = int(data["has_been_run_above_rated_load_last_7d"].astype(str).str.lower().eq("yes").sum())
            return result(f"{n:,} records are marked as having run above rated load during the last 7 days.")
        if "columns" in q or "fields" in q or "data schema" in q:
            return result("The dataset has these columns: " + ", ".join(self.df.columns))
        return result("I couldn't confidently map that question to a supported dataset query. Try asking about equipment count, asset types, health score, vibration, temperature, alerts, preventive maintenance, facilities, load, or unscheduled failures. I will not invent values for fields that are absent from the dataset.")
