# Team Skills Management System

A Flask-based web application for managing team members, skills, and role requirements in healthcare/medical device organizations, designed with ISO 13485 and IEC 62304 compliance in mind.

## Features

- **Team Members Management**: Add, edit, view, and delete team members with contact information and role assignments
- **Skills Management**: Define skills across categories (Technical, Clinical, Soft Skill, Regulatory) with proficiency tracking (Beginner, Intermediate, Advanced)
- **Role Requirements**: Define required skills and minimum proficiency levels for each role
- **Find Experts**: Search for team members by skill and proficiency level
- **Eligibility Tracking**: Automatically track which members meet requirements for various roles
- **Reports & Analytics**: Comprehensive dashboards showing skills distribution, top skills, and member statistics with CSV export
- **Audit Logs**: Complete audit trail of all changes via database triggers
- **Automated Testing**: Pytest test suite for database triggers, procedures, and integration testing

## Project Structure

```
ISO_Standard_DB/
├── app.py                      # Flask application with all routes
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration (create this)
├── Frontend/                   # HTML templates and static files
│   ├── base.html              # Base template with navigation and styling
│   ├── index.html             # Dashboard homepage
│   ├── reports.html           # Analytics and reports page
│   ├── find_experts.html      # Expert search interface
│   ├── audit_logs.html        # Audit trail viewer
│   ├── members/               # Member CRUD templates
│   ├── roles/                 # Role CRUD templates
│   └── skills/                # Skill CRUD templates
├── MySQL/                      # Database scripts
│   ├── DDL.sql                # Schema and sample data
│   └── Triggers & Procedures.sql  # 9 triggers + 3 stored procedures
└── tests/                      # Test suite
    ├── conftest.py            # Pytest configuration and fixtures
    ├── test_actions_procedures.py  # Database trigger tests
    └── test_integration.py    # Integration tests
```

## Database Schema

- **roles**: Role definitions with descriptions
- **team_members**: Member details (name, email, phone, role)
- **skills**: Skill catalog with categories
- **role_requirements**: Required skills per role with minimum proficiency
- **mem_skills**: Member skill assignments with proficiency levels (1-3)
- **audit_logs**: Complete audit trail of all changes

## Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

## Installation

1. **Clone or download the project**
   ```bash
   cd ISO_Standard_DB
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MySQL database**
   
   a. Log into MySQL:
   ```bash
   mysql -u root -p
   ```
   
   b. Execute the database scripts in order:
   ```sql
   SOURCE MySQL/DDL.sql;
   SOURCE MySQL/Triggers & Procedures.sql;
   ```
   
   This creates the `team_skills_db` database with:
   - 6 tables (roles, team_members, skills, role_requirements, mem_skills, audit_logs)
   - 9 triggers (after insert/update/delete on members, skills, mem_skills)
   - 3 stored procedures (Get_Eligible_Roles_For_Member, Search_Experts_By_Skill, Validate_Role_Eligibility)
   - Sample data (5 members, 9 roles, 12 skills)

4. **Configure environment variables**
   
   Create a `.env` file in the project root directory:
   ```env
   DB_HOST=localhost
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_NAME=team_skills_db
   SECRET_KEY=your_secret_key_here_change_in_production
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Access the application**
   
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. **Navigate the application**
   - **Dashboard**: Overview with member count, skills distribution, and recent activities
   - **Members**: Add/edit/view team members and their skills
   - **Skills**: Manage skill catalog across all categories
   - **Roles**: Define roles with required skills and proficiency levels
   - **Find Experts**: Search for members by skill and proficiency
   - **Reports**: View analytics and export data to CSV
   - **Audit Logs**: Track all system changes

## Running Tests

1. **Run all tests**
   ```bash
   pytest tests/ -v
   ```

2. **Run specific test files**
   ```bash
   pytest tests/test_actions_procedures.py -v
   pytest tests/test_integration.py -v
   ```

3. **Test coverage**
   - Database triggers (INSERT, UPDATE, DELETE on members, skills, mem_skills)
   - Stored procedures (eligibility checking, expert search)
   - Integration tests (member CRUD operations, skill assignments)

## Key Features Explained

### Proficiency Scale
- **Level 1**: Beginner - Basic understanding
- **Level 2**: Intermediate - Working proficiency
- **Level 3**: Advanced - Expert level (formerly "Expert")

### Role Eligibility
Members are automatically marked eligible for roles when they possess all required skills at or above the minimum proficiency level. The stored procedure `Get_Eligible_Roles_For_Member` handles this logic.

### Audit Trail
All INSERT, UPDATE, and DELETE operations on members, skills, and member-skill assignments are automatically logged to the `audit_logs` table with timestamps and user information.

### CSV Export
Reports page allows exporting all visible data to CSV format with date-stamped filenames for easy tracking and analysis.

## Technology Stack

- **Backend**: Flask 3.0.0 (Python web framework)
- **Database**: MySQL with stored procedures and triggers
- **Frontend**: Jinja2 templates, vanilla JavaScript, custom CSS
- **Icons**: Font Awesome
- **Testing**: Pytest
- **Configuration**: python-dotenv

## Troubleshooting

### Database Connection Issues
- Verify MySQL service is running
- Check `.env` file credentials
- Ensure `team_skills_db` database exists

### Import Errors
- Reinstall requirements: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)

### Port Already in Use
- Change port in `app.py` (line 1733): `app.run(debug=True, host='0.0.0.0', port=5001)`

## License

This project is developed for healthcare/medical device organizations requiring ISO 13485 and IEC 62304 compliance tracking.
