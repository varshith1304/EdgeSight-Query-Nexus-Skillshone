# AI-Powered IoT Operations Assistant

A beginner-friendly Streamlit project that answers natural-language questions using `iot_operations_01.csv`.

## Dataset fields supported

Equipment identity and grouping: `asset_id`, `asset_type`, `facility_id`, `asset_criticality_class`, `manufacturer_id`, `asset_model_generation`.

Sensor and operational data: vibration, bearing/motor/ambient temperatures, motor current, current imbalance, power factor, inlet/outlet/differential pressure, acoustic emissions, load, OEE and AI health score.

Maintenance and risk fields: operating hours since PM, scheduled PM due within 7 days, corrective maintenance age, prior failures, sensor alert counts and unscheduled failure within 7 days.

This dataset does **not** contain explicit firmware adoption, network connectivity status, MQTT/CoAP telemetry logs, GPS coordinates, credentials, or security certificates. The application does not fabricate answers about those fields.

## Run on Windows

1. Install Python 3.10 or later.
2. Open a terminal in this folder.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

4. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

5. Start the app:

```bash
streamlit run app.py
```

The app should open in your browser.

## Example questions

- How many equipment records are there?
- What is the average health score?
- Which asset types have the most alerts in the last 7 days?
- How many assets are due for preventive maintenance within 7 days?
- Show assets with an unscheduled failure within 7 days
- What is the average bearing temperature for compressors?
- Which facilities have the lowest average health score?
- What is the average vibration for centrifugal pumps?

## How it works

1. Streamlit displays the chat-style question input and dashboard.
2. `iot_assistant.py` maps common question phrases to real dataset columns.
3. Pandas performs calculations and filtering.
4. A lightweight local retrieval function selects relevant reference notes for context (a simple RAG-style foundation).
5. The app reports the dataset and filters used as provenance.
6. A demo role selector limits asset-level row displays for the Viewer role.

## Important production limitations

This is a prototype, not a certified industrial safety system. The role selector is only a UI demonstration; it is not real authentication. Before deployment, add identity-provider login, server-side authorization, audit logs, secrets management, input validation, and tests. Validate operational thresholds with qualified engineers. The dataset's `unscheduled_failure_within_7d` field is an outcome label and should not be described as a guaranteed live prediction.

## Suggested next improvements

- Add real user authentication and role-to-facility permissions.
- Add a vector database and vetted documents for full RAG.
- Connect a chosen LLM only after deciding hosting, privacy, and cost requirements.
- Add date-range filters and download/export support.
- Add tests for query interpretation and calculation correctness.
