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

We use Mac machine to do the development with below tools. Installed all tools using Homebrew.

- Cursor 1.4.5
- Git 2.39.5
- Python 3.13.7
- unixodbc
- msodbcsql18 
- mssql-tools
- docker desktop
- Azure data studio

> We need Microsoft's ODBC driver and tools, for which we need to tap Microsoft's Homebrew repo.
> brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
> brew update
> HOMEBREW_NO_ENV_FILTERING=1 ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools
> odbcinst -q -d -n "ODBC Driver 18 for SQL Server" (verify installation)

> If Python virtual env. is already created, then reinstall pyodbc.
> pip uninstall pyodbc -y
> pip install pyodbc --no-binary :all:

---

## 🌐 Setup Azure AI Foundry Project with o4-mini

Follow these steps to create an Azure AI Foundry project and deploy the o4-mini reasoning model.

> Prerequisite: An active Azure subscription with Azure OpenAI access approved.

1. Create Azure AI Foundry instance along with a project
   - Select Inbound access from All Networks, later we can change it to specific IP
2. Go to Networking section, choose `Selected Networks and Private Endpoints` and add Mac IP address
3. Navigate to Azure AI Foundry Portal, go to `Models + endpoints` section under the created project
5. Deploy the o4-mini Model from `Deploy base model` option
6. Find below configuration details and keep them handy

```
AZURE_API_BASE=https://<Azure Foundary Instance Name>.services.ai.azure.com/
AZURE_API_KEY=<Azure Foundry Project Key>
AZURE_OPENAI_DEPLOYMENT=o4-mini
AZURE_API_VERSION=2024-12-01-preview
```

---

## 🛢️ Run SQL Server in Docker on macOS

Follow these steps to set up a lightweight SQL Server environment on macOS:

1. **Install Docker Desktop**  
   ```
   brew install --cask docker
   ```
Launch Docker from Applications and wait until the 🐳 icon shows "Docker Engine is running".

2. Pull the lightweight SQL Edge image
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

   - ACCEPT_EULA=1 → Accepts the SQL Server license.
   - MSSQL_SA_PASSWORD → Sets the SA (system administrator) password (must meet complexity rules).
   - MSSQL_PID=Developer → Runs Developer Edition (full feature set for dev/test).
   - -p 1433:1433 → Exposes SQL Server on port 1433.

4. Install Azure Data Studio (for database management)
   ```
   brew install --cask azure-data-studio
   ```

5. Connect to SQL Server
   
   - Server: localhost
   - Port: 1433
   - User: SA
   - Password: XXXXX


> Note: For this PoC, we will use a sample MovieReviews database to test the overall flow. This database will be created in later sections.


## 🐍 Create virtual environment and install package

Check the [requirements.txt](./requirements.txt). Execute below commands.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To deactivate, execute `deactivate`

---

## 📂 Project Structure

```bash
agentic-ai-poc/
├── db/
│   ├── create_schema.sql        # Creates MovieReviews schema with IF NOT EXISTS
│   ├── source_data_generator.py # Generates sample data (genres, movies, reviews)
│   ├── validate.sql             # SQL validation queries for distribution checks
│
├── config.py                    # Configuration (DB creds, Azure AI Foundry keys)
├── main.py                      # Entrypoint to execute the end-to-end agentic workflow
├── .env                         # Holds the environment variables configuration
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 🛠️ Setup Environment Variables

Create `.env` file and setup below variables. The variables are loaded into application through [config.py](config.py).

```
DB_SERVER=localhost
DB_NAME=MovieReviews
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_USER=SA
DB_PASSWORD=XXXXX
# Azure OpenAI
AZURE_API_BASE=https://<Azure Foundry instance Name>.cognitiveservices.azure.com/
AZURE_API_KEY=<Azure Foundry Project Key>
AZURE_OPENAI_DEPLOYMENT=o4-mini
AZURE_API_VERSION=2024-12-01-preview
```

---

## 📜 Create Source Database

Run the [create_schema.sql](./db/create_schema.sql) script in **Azure Query Editor**:

---

## 🎬 Generate Sample Data

Run the Python script:

```
python db/source_data_generator.py
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

## ✅ Step 5: Validate Source Data Distribution

Use [validate.sql](./db/validate.sql) to check correctness.

---

