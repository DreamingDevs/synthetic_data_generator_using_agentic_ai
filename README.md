# Agentic AI PoC – Synthetic Data Generator for SQL Server

## 🎯 Purpose

The goal of this project is to build an **Agentic AI system** using the **Optimizer–Evaluator–Validator pattern**. The system:

* Understands a **production database schema, data distribution and usage patterns**.
* Creates a **synthetic database** with the same schema.
* Generates **synthetic data** that follows the source database's **distributions and usage patterns**.
* Uses **CrewAI agents** (Evaluator, Optimizer, Validator) integrated with **Azure AI Foundry** (`o4-mini` model).

This project helps teams safely generate test data without exposing production data.

---

## 🖥️ Environment Setup

We use a **Windows 11 VM** as the development environment. Create an Azure Windows VM with 4 vCores and 16GB memory.

### Install Prerequisites

- SQL Server 2022 Express
- SQL Server Management Studio 21
- Git 2.50.1
- Python 3.13.6
- VS Code 1.103.1
- Microsoft ODBC Driver 17 (or 18) for SQL Server

---

#### requirements.txt

```
faker
pyodbc
pyodb
crewai
crewai-tools
PyYAML
```

---

### Install Python Dependencies

Create a virtual environment and install requirements using Git Bash:

```powershell
python -m venv .venv
source .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 📂 Project Structure

```bash
agentic-ai-poc/
├── db/
│   ├── create_schema.sql        # Creates MovieReviews schema with IF NOT EXISTS
│   ├── source_data_generator.py # Generates sample data (genres, movies, reviews)
│   ├── validate.sql             # SQL validation queries for distribution checks
│
├── tools/
│   ├── db_connection_tool.py    # Tool to connect to SQL Server
│   ├── schema_tools.py          # Tool to analyze schema
│   ├── data_analysis_tools.py   # Tool to analyze data distributions
│   ├── yaml_tools.py            # Tool to write analysis into YAML files
|   ├── connection_manager.py    # Holds the connection to SQL Server which can be reused by tools 
│
├── agents/
│   └── evaluator_agent.py       # Evaluator Agent using CrewAI + Azure AI Foundry
│
├── config.py                    # Configuration (DB creds, Azure AI Foundry keys)
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 🎬 Step 1: Create MovieReviews Database

> Note: For this PoC, we will use a sample MovieReviews database to test the overall flow.

Run the [create_schema.sql](../SyntheticDataGenerator/scripts/create_schema.sql) script in **SQL Server Management Studio (SSMS)**:

---

## 🎬 Step 2: Generate Sample Data

Run the Python script:

```bash
python scripts/source_data_generator.py
```

### Data Generation Rules

1. **Genres**: 20 real genres (Action, Drama, Comedy, etc.).
2. **Movies**: 1000 movies.

   * 3 genres → 60% of movies.
   * 2 genres → 0 movies.
   * Remaining 15 genres → 40% distributed.
3. **Reviews**: 10,000 reviews.

   * 500 movies → no reviews.
   * 100 movies → 90% of reviews.
   * Remaining 400 movies → 10% of reviews.

---

## ✅ Step 3: Validate Data Distribution

Use [validate.sql](../SyntheticDataGenerator/scripts/validate.sql) to check correctness.

---

---

## 🛠️ Tools Overview

To keep the project modular and extensible, we implemented **tools** that the agents can call when performing analysis or transformations. Each tool is a standalone component, so future agents (like Optimizer, Validator) can reuse them.

### 🔌 `db_connection_tool.py`
* Provides a tool interface for connecting to SQL Server.
* Hands over an active connection to the **connection manager** for reuse.
* Ensures that agents do not need to worry about raw DB connectivity.

### 🔑 `connection_manager.py`
* Maintains a **singleton connection** to SQL Server.
* Allows all tools (schema analysis, data analysis, YAML writer) to reuse the same connection.
* Helps in avoiding repeated open/close operations and keeps resource usage optimized.

### 📊 `schema_tools.py`
* Reads the database schema (tables, columns, datatypes, primary keys, foreign keys).
* Returns schema metadata in a structured format.
* Enables the agent to "understand" the database structure before analyzing data.

### 📈 `data_analysis_tools.py`
* Examines **data distributions** in tables.
* Evaluates foreign key relationships (e.g., *movies per genre*, *reviews per movie*).
* Provides statistical summaries that agents can later use for synthetic data generation.

### 📝 `yaml_tools.py`
* Takes analysis results and writes them into a structured **YAML file**.
* YAML provides a portable, human-readable format that Optimizer and Validator agents can consume.
* Ensures outputs are persisted, version-controlled, and shareable.

---

## 🔗 How Tools Work Together

1. **Evaluator Agent** triggers tools to:
   - Connect to the database via `db_connection_tool.py`.
   - Fetch schema metadata with `schema_tools.py`.
   - Run data distribution analysis with `data_analysis_tools.py`.
   - Store results into YAML using `yaml_tools.py`.
   
2. The YAML output becomes the **input for the Optimizer agent**, which will later generate synthetic data rules.  
3. The **Validator agent** can rerun these tools to confirm that generated data matches the original distributions.


## 📌 Notes

* Deploying a model on Azure AI Foundry is free. Costs occur only when you consume tokens.
* Ensure `pyodbc` has the correct **ODBC Driver 18** installed.
* This PoC is designed for **SQL Server Express 2022**, but can be extended to other editions.
