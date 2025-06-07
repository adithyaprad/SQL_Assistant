from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import mysql.connector
from typing import List, Union, Dict, Any, Optional
from google.adk.tools import FunctionTool
import uuid
import asyncio

APP_NAME = "sql_generator_app"
USER_ID = "dev_user_01"
GEMINI_MODEL = "gemini-2.0-flash-exp"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
}

def get_connection(database: Optional[str] = None) -> mysql.connector.connection.MySQLConnection:
    """Creates and returns a MySQL connection"""
    config = DB_CONFIG.copy()
    if database:
        config["database"] = database
    return mysql.connector.connect(**config)

def execute_sql_query(query: str, database: Optional[str] = "test") -> dict:
    """Executes SQL queries and returns results. Handles CREATE/INSERT/SELECT operations.
    
    Args:
        query: The SQL query to execute
        database: The database to connect to (default: "test")
    
    Returns:
        dict: Contains 'status' (success/error), 'results' (for SELECT), 
              or 'row_count' (for INSERT/UPDATE), and error messages if any.
    """
    try:
        connection = get_connection(database)
        cursor = connection.cursor()
        
        cursor.execute(query)

        connection.commit()
        
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return {
                "status": "success",
                "results": results,
                "columns": columns
            }
        else:
            connection.commit()
            return {
                "status": "success",
                "row_count": cursor.rowcount,
                "message": f"Query executed, affected rows: {cursor.rowcount}"
            }
            
    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error_message": f"SQL Error: {err.msg}",
            "error_code": err.errno
        }
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def create_database(database_name: str) -> dict:
    """Creates a new database with the specified name.
    
    Args:
        database_name: The name of the database to create
        
    Returns:
        dict: Status of the operation
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        connection.commit()
        
        return {
            "status": "success",
            "message": f"Database '{database_name}' created successfully"
        }
    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error_message": f"Error creating database: {err.msg}",
            "error_code": err.errno
        }
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def drop_database(database_name: str) -> dict:
    """Drops the specified database.
    
    Args:
        database_name: The name of the database to drop
        
    Returns:
        dict: Status of the operation
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
        connection.commit()
        
        return {
            "status": "success",
            "message": f"Database '{database_name}' dropped successfully"
        }
    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error_message": f"Error dropping database: {err.msg}",
            "error_code": err.errno
        }
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def describe_table(database_name: str, table_name: str) -> dict:
    """Describes the structure of a table.
    
    Args:
        database_name: The name of the database
        table_name: The name of the table
        
    Returns:
        dict: Table structure information
    """
    try:
        connection = get_connection(database_name)
        cursor = connection.cursor()
        
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        column_info = []
        
        for col in columns:
            column_info.append({
                "field": col[0],
                "type": col[1],
                "null": col[2],
                "key": col[3],
                "default": col[4],
                "extra": col[5]
            })
        
        return {
            "status": "success",
            "database": database_name,
            "table": table_name,
            "columns": column_info
        }
    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error_message": f"Error describing table: {err.msg}",
            "error_code": err.errno
        }
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

sql_tool = FunctionTool(func=execute_sql_query)
create_db_tool = FunctionTool(func=create_database)
drop_db_tool = FunctionTool(func=drop_database)
describe_table_tool = FunctionTool(func=describe_table)


sql_analyzer_agent = LlmAgent(
    name="SqlRequirementsAnalyzerAgent",
    model=GEMINI_MODEL,
    instruction="""You are a SQL Requirements Analyzer AI.
    Based on the user's natural language query, analyze and extract the key requirements for SQL generation.
    Identify tables, fields, relationships, filtering conditions, and expected output format.
    Output a structured analysis that will help with SQL generation.
    """,
    description="Analyzes requirements for SQL generation from natural language query.",
    output_key="sql_requirements"
)

sql_generator_agent = LlmAgent(
    name="SqlGeneratorAgent",
    model=GEMINI_MODEL,
    instruction="""You are a SQL Generator AI.
    Based on the requirements analysis provided in the session state under the key 'sql_requirements',
    write the initial SQL query that fulfills these requirements.
    Output *only* the raw SQL code block without additional explanations.
    Follow SQL best practices for readability and performance.
    """,
    description="Generates initial SQL code based on requirements analysis.",
    output_key="generated_sql"
)

sql_reviewer_agent = LlmAgent(
    name="SqlReviewerAgent",
    model=GEMINI_MODEL,
    instruction="""You are a SQL Reviewer AI.
    Review the SQL query provided in the session state under the key 'generated_sql'.
    Provide constructive feedback on potential errors, performance issues, or improvements.
    Focus on SQL best practices, query optimization, and correctness.
    Output only the review comments.
    """,
    description="Reviews SQL code and provides feedback.",
    output_key="sql_review_comments"
)

sql_optimizer_agent = LlmAgent(
    name="SqlOptimizerAgent",
    model=GEMINI_MODEL,
    instruction="""You are a SQL Optimizer AI.
    Take the original SQL query provided in the session state key 'generated_sql'
    and the review comments found in the session state key 'sql_review_comments'.
    Optimize the original SQL query to address the feedback and improve its performance and readability.
    Output *only* the final, optimized SQL query block with brief comments explaining key parts of the query.
    """,
    description="Optimizes SQL based on review comments.",
    output_key="optimized_sql"
)

sql_execution_agent = LlmAgent(
    name="SqlExecutionAgent",
    model=GEMINI_MODEL,
    instruction="""You are a SQL Execution AI.
    Execute the SQL query in the session state key 'optimized_sql'.
    You have access to the following tools:
    - sql_tool: For executing general SQL queries (SELECT, INSERT, UPDATE, etc.)
    - create_db_tool: For creating databases
    - drop_db_tool: For dropping databases
    - describe_table_tool: For describing table structure
    
    For CREATE TABLE statements, make sure to either:
    1. Include the database name in the statement (e.g., CREATE TABLE database_name.table_name ...)
    2. Or specify the database parameter when using sql_tool
    
    Output the results of the query execution.
    """,
    description="Executes SQL query and returns results.",
    tools=[sql_tool, create_db_tool, drop_db_tool, describe_table_tool]
)

root_agent = SequentialAgent(
    name="SqlPipelineAgent",
    sub_agents=[sql_analyzer_agent, sql_generator_agent, sql_reviewer_agent, sql_optimizer_agent, sql_execution_agent]
)

# Create session service
session_service = InMemorySessionService()
# Create a global runner
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

def call_agent(query):
    # Generate a unique session ID for each query
    session_id = f"sql_session_{uuid.uuid4().hex[:8]}"
    
    # Create an event loop and run the async operations
    try:
        # Use a new event loop for each call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async session creation and query execution
        result = loop.run_until_complete(_run_agent_async(query, session_id))
        loop.close()
        return result
    except Exception as e:
        print(f"Error in call_agent: {str(e)}")
        return f"Error: {str(e)}"

async def _run_agent_async(query, session_id):
    try:
        # Create a new session for this query
        await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
        
        content = types.Content(role='user', parts=[types.Part(text=query)])
        events = []
        
        # Collect events from the async run
        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
            events.append(event)
        
        responses = []
        for event in events:
            if event.is_final_response():
                final_response = event.content.parts[0].text
                print("Agent Response: ", final_response)
                responses.append(final_response)
        
        return "\n\n".join(responses) if responses else "No response from agent."
    except Exception as e:
        print(f"Error in _run_agent_async: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    call_agent("Create a query to find all customers who purchased more than $1000 in the last month")
