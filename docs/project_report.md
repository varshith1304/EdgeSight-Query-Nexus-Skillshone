# Project Report: AI-Powered IoT Operations Assistant

## 1. Introduction
Industrial equipment generates sensor readings and maintenance records. Finding important information manually can take time. This project provides a simple natural-language interface for querying an equipment operations dataset.

## 2. Problem statement
Users need a convenient way to ask operational questions without manually filtering spreadsheets or writing database queries. Answers must be based on available columns and must identify their data source.

## 3. Objectives
- Accept questions written in everyday English.
- Map supported questions to real dataset fields.
- Calculate counts, averages, minimums, maximums, and grouped summaries.
- Support equipment types and facility filtering.
- Show the dataset and filter scope behind each answer.
- Demonstrate aggregate-versus-row-level output by user role.
- Avoid claiming the dataset contains fields that are not present.

## 4. Dataset
The supplied CSV has 82,785 rows and 36 columns. Important categories include asset identity, facility and type, vibration, temperature, electrical readings, pressure, maintenance, alerts, health score, load and failure labels.

## 5. System architecture
User question -> Streamlit interface -> intent/column mapping -> Pandas query -> answer formatter -> answer, table and provenance.

A lightweight local retrieval function selects relevant notes about the dataset and IoT terms. Full LLM-based RAG can be added later with an approved document collection and model.

## 6. Modules
1. User interface: question entry, examples, KPI cards and exploratory charts.
2. Data loader: loads the CSV using Pandas.
3. Query interpreter: identifies metric, aggregation, asset type, facility and question category.
4. Analytics engine: calculates requested values.
5. Provenance: reports source file and scope.
6. Access demonstration: viewer sees aggregate answers; other demo roles may see asset rows for supported queries.

## 7. Security and privacy
The prototype does not expose credentials because no credential fields are present. Its role selector is not production-grade authentication. Production use requires server-side identity verification, permissions, audit logging, secure deployment, and careful control of asset-level details.

## 8. Testing
Test questions should include equipment count, average health, alerts by type, maintenance due count, failure-label count, temperature by asset type, and an unsupported question such as “Which devices use firmware version 5?” The unsupported question should not receive a fabricated answer.

## 9. Limitations
- Rule-based question interpretation rather than a general LLM.
- Lightweight keyword retrieval rather than a production vector database.
- No real-time sensor stream or database connection.
- No explicit network connectivity, firmware adoption, or GPS fields.
- Demo roles do not provide actual security enforcement.
- Health thresholds require validation by reliability engineers.

## 10. Conclusion
The project demonstrates a dataset-grounded assistant for industrial equipment operations. It turns selected natural-language questions into calculations, reports results, and identifies the data source. It provides a foundation for later adding a secure LLM and full RAG pipeline.
