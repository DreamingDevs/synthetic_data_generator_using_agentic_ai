# Agentic AI PoC – Synthetic Data Generator for SQL Server

## 🎯 Purpose

The goal of this project is to build an Agentic AI system using the Optimizer–Evaluator–Validator pattern. The system:

* Understands a production database schema, data distributions, and usage patterns.
* Creates a synthetic database with the same schema.
* Generates synthetic data that follows the source database’s distributions and usage patterns.
* Uses CrewAI agents (Evaluator, Optimizer, Validator) integrated with Azure AI Foundry (`o4-mini` model).

This project enables teams to safely generate test data without exposing production data.

---

## 🖥️ Environment setup

These instructions target macOS. Install the following tools (Homebrew recommended):

- Cursor (e.g., 1.4.5)
- Git (e.g., 2.39.5)
- Python 3.13.x
- `unixodbc`
- `msodbcsql18`
- `mssql-tools`
- Docker Desktop
- Azure Data Studio

> Microsoft’s ODBC driver and tools are installed from Microsoft’s Homebrew repo:
```
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_NO_ENV_FILTERING=1 ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools
odbcinst -q -d -n "ODBC Driver 18 for SQL Server"   # verify installation
```

> If a Python virtual environment already existed prior to installing the ODBC driver, reinstall `pyodbc`:
```
pip uninstall pyodbc -y
pip install pyodbc --no-binary :all:
```

---

## 🌐 Set up Azure AI Foundry project with o4-mini

Create an Azure AI Foundry project and deploy the `o4-mini` reasoning model.

> Prerequisite: An active Azure subscription with Azure OpenAI access approved.

1. Create an Azure AI Foundry hub and project.
   - Start with inbound access from all networks. You can restrict to specific IPs later.
2. In Networking, choose Selected networks and private endpoints, and add your Mac’s IP address.
3. In the Azure AI Foundry portal, navigate to Models + endpoints in your project.
4. Deploy the `o4-mini` model via Deploy base model.
5. Capture the following configuration values:

```
AZURE_API_BASE=https://<azure-ai-foundry-resource>.services.ai.azure.com/
AZURE_API_KEY=<project API key>
AZURE_OPENAI_DEPLOYMENT=o4-mini
AZURE_API_VERSION=2024-12-01-preview
```

---

## 🛢️ Run SQL Server in Docker on macOS

Set up a lightweight SQL Server environment on macOS:

1. Install Docker Desktop
   ```
   brew install --cask docker
   ```
   Launch Docker and wait until it shows “Docker Engine is running”.

2. Pull the SQL Edge image
   ```
   docker pull mcr.microsoft.com/azure-sql-edge
   ```

3. Run the SQL container
   ```
   docker run -e "ACCEPT_EULA=1" \
           -e "MSSQL_SA_PASSWORD=XXXXX" \
           -e "MSSQL_PID=Developer" \
           -p 1433:1433 \
           -d --name sql \
           mcr.microsoft.com/azure-sql-edge
   ```

   - `ACCEPT_EULA=1`: Accepts the SQL Server license.
   - `MSSQL_SA_PASSWORD`: SA (system administrator) password (must meet complexity requirements).
   - `MSSQL_PID=Developer`: Developer Edition (full feature set for dev/test).
   - `-p 1433:1433`: Exposes SQL Server on port 1433.

4. Install Azure Data Studio (for database management)
   ```
   brew install --cask azure-data-studio
   ```

5. Connect to SQL Server
   
   - Server: `localhost`
   - Port: `1433`
   - User: `SA`
   - Password: your SA password

> Note: This PoC uses a sample `MovieReviews` database created in later sections.


## 🐍 Create a virtual environment and install dependencies

Review [requirements.txt](./requirements.txt), then run:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To deactivate, run `deactivate`.

---

## 📂 Project structure

```
agentic-ai-poc/
├── db/
│   ├── create_schema.sql        # Creates MovieReviews schema if not exists
│   ├── source_data_generator.py # Generates sample data (genres, movies, reviews)
│   ├── validate.sql             # SQL validation queries for distribution checks
│
├── config.py                    # Configuration (DB credentials, Azure AI Foundry keys)
├── main.py                      # Entrypoint to execute the end-to-end agentic workflow
├── .env                         # Environment variables (not committed)
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 🛠️ Configure environment variables

Create a `.env` file with the variables below. They are loaded by [config.py](config.py).

```
DB_SERVER=localhost
DB_NAME=MovieReviews
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_USER=SA
DB_PASSWORD=<your SA password>

# Azure AI Foundry
AZURE_API_BASE=https://<azure-ai-foundry-resource>.services.ai.azure.com/
AZURE_API_KEY=<project API key>
AZURE_OPENAI_DEPLOYMENT=o4-mini
AZURE_API_VERSION=2024-12-01-preview
```

> Security note: Never commit `.env` to version control.

---

## 📜 Create the source database

Create the `MovieReviews` schema by running [db/create_schema.sql](./db/create_schema.sql) using Azure Data Studio.

---

## 🎬 Generate sample data

Run the Python script:

```
python db/source_data_generator.py
```

### Data generation rules

1. Genres: 20 real genres (Action, Drama, Comedy, etc.).
2. Movies: 1,000 movies.
   * 60% of movies have 3 genres.
   * 0 movies have exactly 2 genres.
   * The remaining 40% are distributed across 15 genres.
3. Reviews: 10,000 reviews.
   * 500 movies have no reviews.
   * 100 movies receive 90% of all reviews.
   * The remaining 400 movies receive 10% of reviews.

---

## ✅ Validate source data distribution

Use [db/validate.sql](./db/validate.sql) to validate data distributions and correctness.

---
