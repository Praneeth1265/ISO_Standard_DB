import pytest
import mysql.connector
import os
import re
from ISO_Standard_DB.app import app, get_db_connection

# Define test database credentials
TEST_DB_NAME = 'test_team_skills_db'

def parse_sql_file(file_path):
    """
    Parses a SQL file and yields executable statements.
    Handles 'DELIMITER' commands to support triggers and procedures.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    statements = []
    current_stmt = []
    delimiter = ';'
    
    for line in lines:
        line_strip = line.strip()
        
        if not line_strip or line_strip.startswith('--'):
            continue
            
        # Handle DELIMITER command
        if line_strip.upper().startswith('DELIMITER'):
            parts = line_strip.split()
            if len(parts) > 1:
                delimiter = parts[1]
            continue
            
        # Skip Database creation/selection lines to keep tests isolated in TEST_DB
        # Example: CREATE DATABASE IF NOT EXISTS team_skills_db;
        if 'CREATE DATABASE' in line_strip.upper() and 'IF NOT EXISTS' in line_strip.upper():
             continue
        if line_strip.upper().startswith('USE '):
             continue

        current_stmt.append(line)
        
        # Check if the line ends with the current delimiter
        if line_strip.endswith(delimiter):
            # Form complete statement
            full_stmt = "".join(current_stmt)
            
            # Remove delimiter from the end
            full_stmt = full_stmt.strip()
            if full_stmt.endswith(delimiter):
               full_stmt = full_stmt[:-len(delimiter)]
            
            # Additional Cleanup for specific SQL weirdness if needed
            if full_stmt.strip():
                statements.append(full_stmt.strip())
            current_stmt = []
            
    return statements

def execute_sql_file(cursor, file_path):
    statements = parse_sql_file(file_path)
    
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as err:
            # defined error codes
            # 1050: Table exists
            # 1359: Trigger exists
            # 1304: Procedure exists
            # 1061: Duplicate key name
            # 1826: Duplicate foreign key constraint
            
            if err.errno in (1050, 1359, 1304, 1061): 
                print(f"WARNING: Object already exists, skipping: {err}")
            elif err.errno == 1826:
                print(f"WARNING: Duplicate foreign key, ignoring: {err}")
            else:
                print(f"ERROR executing: {stmt[:100]}... -> {err}")
                raise err

@pytest.fixture(scope='session', autouse=True)
def setup_test_database():
    """Creates a test database and runs the DDL schema."""
    
    # 1. Connect to MySQL Server (no specific DB)
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "")
    )
    cursor = conn.cursor()
    
    # 2. Re-create the test database
    # Force drop
    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    conn.close()

    # 3. Switch environment variable so the App uses the Test DB
    os.environ['DB_NAME'] = TEST_DB_NAME

    # 4. Apply Schema (Tables, Triggers, Procedures)
    test_conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=TEST_DB_NAME
    )
    test_cursor = test_conn.cursor()
    
    # Enable necessary settings
    test_cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    
    print("--- Setting up Tables ---")
    execute_sql_file(test_cursor, 'MySQL/DDL.sql')
    
    print("--- Setting up Triggers & Procedures ---")
    execute_sql_file(test_cursor, 'MySQL/Triggers & Procedures.sql')

    test_conn.commit()
    test_cursor.close()
    test_conn.close()

    yield  # Run the tests

    # Cleanup after all tests
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "")
    )
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cursor.close()
    conn.close()

@pytest.fixture
def client():
    """Configures the app for testing"""
    app.config['TESTING'] = True
    app.secret_key = 'test-secret-key'
    
    with app.test_client() as client:
        yield client
