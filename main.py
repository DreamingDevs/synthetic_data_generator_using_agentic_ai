# main.py
from crewai import Task, Crew
from agents.evaluator_agent import create_evaluator_agent

if __name__ == "__main__":
    evaluator = create_evaluator_agent()

    # 👉 Edit these for your environment (or pass via the UI at runtime)
    SERVER = "localhost\\SQLEXPRESS"
    DATABASE = "MovieReviews"
    # If you need SQL auth, add username/password in the tool call step (the agent can also request it)

    # High-level task that tells the agent what “good” looks like, without dictating tool order.
    task = Task(
        description=(
            "Connect to the target SQL Server database and produce a YAML report. "
            "You should: (1) connect using DBConnectionTool, "
            "(2) get schema via Get Database Schema, "
            "(3) get table row counts, "
            "(4) get foreign keys and their distributions, "
            "(5) save everything with Save YAML Report. "
            f"Use server='{SERVER}' and database='{DATABASE}'. "
            "Name the output file 'schema_analysis.yaml'."
        ),
        agent=evaluator,
        expected_output="A file 'schema_analysis.yaml' saved to disk with the analysis."
    )

    crew = Crew(agents=[evaluator], tasks=[task], verbose=True)
    crew.run()
