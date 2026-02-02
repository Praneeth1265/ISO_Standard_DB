# Project Setup Instructions

## Database Setup

1. Create a MySQL database (e.g., `iso_standard_db`).
2. Execute the following SQL scripts from the `MySQL` folder in your database:
   - First: `MySQL/DDL.sql`
   - Second: `MySQL/Triggers & Procedures.sql`

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root directory.
2. Add your database configuration to the `.env` file:
   ```env
   DB_HOST=localhost
   DB_USER=your_db_username
   DB_PASSWORD=your_db_password
   DB_NAME=iso_standard_db
   SECRET_KEY=your_development_key
   ```

## Running the Project

1. Start the application:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`.
