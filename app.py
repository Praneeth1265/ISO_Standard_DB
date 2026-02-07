from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from functools import wraps
import re
from dotenv import load_dotenv


app = Flask(__name__, 
            template_folder='Frontend/', 
            static_folder='Frontend/')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conn
    except Exception as e:
        print("DB connection failed:", e)
        return None


def handle_db_error(f):
    """Decorator to handle database errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Error as e:
            flash(f'Database error: {str(e)}', 'danger')
            return redirect(url_for('index'))
    return decorated_function

#routes


@app.route('/')
def index():
    """Home page with dashboard"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed', 'danger')
        return render_template('index.html', stats={})
    
    cursor = connection.cursor(dictionary=True)
    
    # Get statistics
    stats = {}
    
    # Total members
    cursor.execute("SELECT COUNT(*) as count FROM team_members")
    stats['total_members'] = cursor.fetchone()['count']
    
    # Total roles
    cursor.execute("SELECT COUNT(*) as count FROM roles")
    stats['total_roles'] = cursor.fetchone()['count']
    
    # Total skills in catalog
    cursor.execute("SELECT COUNT(*) as count FROM skills")
    stats['total_skills'] = cursor.fetchone()['count']
    
    # Total skill assignments
    cursor.execute("SELECT COUNT(*) as count FROM mem_skills")
    stats['total_assignments'] = cursor.fetchone()['count']
    
    # Recent audit logs (triggered automatically)
    cursor.execute("""
        SELECT * FROM audit_logs 
        ORDER BY change_date DESC 
        LIMIT 10
    """)
    stats['recent_logs'] = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('index.html', stats=stats)

#Role management

@app.route('/roles')
@handle_db_error
def list_roles():
    """List all roles with their requirements"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            r.role_id,
            r.role_name,
            r.description,
            COUNT(DISTINCT tm.mem_id) as member_count,
            COUNT(DISTINCT rr.skill_id) as required_skills
        FROM roles r
        LEFT JOIN team_members tm ON r.role_id = tm.role_id
        LEFT JOIN role_requirements rr ON r.role_id = rr.role_id
        GROUP BY r.role_id
        ORDER BY r.role_name
    """)
    
    roles = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('roles/list.html', roles=roles)

# Replace your add_role route with this updated version:

@app.route('/roles/add', methods=['GET', 'POST'])
@handle_db_error
def add_role():
    """Add a new role with skill requirements (triggers after_role_insert)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        role_name = request.form['role_name'].strip()
        description = request.form['description'].strip()
        
        # Get skill requirements from form
        skill_ids = request.form.getlist('skill_ids[]')
        min_proficiencies = request.form.getlist('min_proficiencies[]')
        
        # This INSERT will trigger after_role_insert
        cursor.execute("""
            INSERT INTO roles (role_name, description) 
            VALUES (%s, %s)
        """, (role_name, description))
        
        # Get the newly created role_id
        role_id = cursor.lastrowid
        
        # Insert skill requirements if any were specified
        if skill_ids and min_proficiencies:
            for skill_id, min_prof in zip(skill_ids, min_proficiencies):
                if skill_id and min_prof:  # Only insert if both values are present
                    cursor.execute("""
                        INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) 
                        VALUES (%s, %s, %s)
                    """, (role_id, skill_id, min_prof))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash(f'Role "{role_name}" added successfully!', 'success')
        return redirect(url_for('view_role', role_id=role_id))
    
    # GET request - get all skills for the dropdown
    cursor.execute("""
        SELECT skill_id, skill_name, category 
        FROM skills 
        ORDER BY category, skill_name
    """)
    skills = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Convert skills to JSON for JavaScript
    import json
    skills_json = json.dumps(skills)
    
    return render_template('roles/add.html', skills_json=skills_json)

@app.route('/roles/<int:role_id>')
@handle_db_error
def view_role(role_id):
    """View role details with requirements and current members"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get role details
    cursor.execute("SELECT * FROM roles WHERE role_id = %s", (role_id,))
    role = cursor.fetchone()
    
    if not role:
        flash('Role not found', 'warning')
        return redirect(url_for('list_roles'))
    
    # Get role requirements
    cursor.execute("""
        SELECT 
            s.skill_id,
            s.skill_name,
            s.category,
            rr.min_proficiency_required
        FROM role_requirements rr
        JOIN skills s ON rr.skill_id = s.skill_id
        WHERE rr.role_id = %s
        ORDER BY s.category, s.skill_name
    """, (role_id,))
    requirements = cursor.fetchall()
    
    # Get members with this role
    cursor.execute("""
        SELECT 
            tm.mem_id,
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name,
            tm.email,
            tm.phone_no
        FROM team_members tm
        WHERE tm.role_id = %s
        ORDER BY tm.first_name, tm.last_name
    """, (role_id,))
    members = cursor.fetchall()
    
    # Get available skills for adding requirements
    cursor.execute("""
        SELECT skill_id, skill_name, category 
        FROM skills 
        WHERE skill_id NOT IN (
            SELECT skill_id FROM role_requirements WHERE role_id = %s
        )
        ORDER BY category, skill_name
    """, (role_id,))
    available_skills = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('roles/view.html', 
                         role=role, 
                         requirements=requirements,
                         members=members,
                         available_skills=available_skills)

@app.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@handle_db_error
def edit_role(role_id):
    """Edit role details and skill requirements (triggers after_role_update)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        role_name = request.form['role_name'].strip()
        description = request.form['description'].strip()
        
        # Get skill requirement updates
        existing_skill_ids = request.form.getlist('existing_skill_ids[]')
        existing_min_proficiencies = request.form.getlist('existing_min_proficiencies[]')
        
        # Get new skills to add
        new_skill_ids = request.form.getlist('new_skill_ids[]')
        new_min_proficiencies = request.form.getlist('new_min_proficiencies[]')
        
        # Get skills marked for deletion
        skills_to_delete = request.form.get('skills_to_delete', '')
        skills_to_delete_list = [s.strip() for s in skills_to_delete.split(',') if s.strip()]
        
        # Update role basic info - This UPDATE will trigger after_role_update
        cursor.execute("""
            UPDATE roles 
            SET role_name = %s, description = %s 
            WHERE role_id = %s
        """, (role_name, description, role_id))
        
        # Delete marked skill requirements
        if skills_to_delete_list:
            for skill_id in skills_to_delete_list:
                cursor.execute("""
                    DELETE FROM role_requirements 
                    WHERE role_id = %s AND skill_id = %s
                """, (role_id, skill_id))
        
        # Update existing skill requirements (proficiency levels)
        if existing_skill_ids and existing_min_proficiencies:
            for skill_id, min_prof in zip(existing_skill_ids, existing_min_proficiencies):
                if skill_id and min_prof and skill_id not in skills_to_delete_list:
                    cursor.execute("""
                        UPDATE role_requirements 
                        SET min_proficiency_required = %s 
                        WHERE role_id = %s AND skill_id = %s
                    """, (min_prof, role_id, skill_id))
        
        # Insert new skill requirements
        if new_skill_ids and new_min_proficiencies:
            for skill_id, min_prof in zip(new_skill_ids, new_min_proficiencies):
                if skill_id and min_prof:  # Only insert if both values are present
                    cursor.execute("""
                        INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) 
                        VALUES (%s, %s, %s)
                    """, (role_id, skill_id, min_prof))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('Role updated successfully!', 'success')
        return redirect(url_for('view_role', role_id=role_id))
    
    # GET request - fetch role details
    cursor.execute("SELECT * FROM roles WHERE role_id = %s", (role_id,))
    role = cursor.fetchone()
    
    if not role:
        flash('Role not found', 'warning')
        cursor.close()
        connection.close()
        return redirect(url_for('list_roles'))
    
    # Get existing skill requirements for this role
    cursor.execute("""
        SELECT 
            s.skill_id,
            s.skill_name,
            s.category,
            rr.min_proficiency_required
        FROM role_requirements rr
        JOIN skills s ON rr.skill_id = s.skill_id
        WHERE rr.role_id = %s
        ORDER BY s.category, s.skill_name
    """, (role_id,))
    existing_requirements = cursor.fetchall()
    
    # Get all skills that are NOT already assigned to this role (for new additions)
    cursor.execute("""
        SELECT skill_id, skill_name, category 
        FROM skills 
        WHERE skill_id NOT IN (
            SELECT skill_id FROM role_requirements WHERE role_id = %s
        )
        ORDER BY category, skill_name
    """, (role_id,))
    available_skills = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Convert to JSON for JavaScript
    import json
    available_skills_json = json.dumps(available_skills)
    existing_skill_ids_json = json.dumps([req['skill_id'] for req in existing_requirements])
    
    return render_template('roles/edit.html', 
                         role=role,
                         existing_requirements=existing_requirements,
                         available_skills_json=available_skills_json,
                         existing_skill_ids_json=existing_skill_ids_json)


@app.route('/roles/<int:role_id>/delete', methods=['POST'])
@handle_db_error
def delete_role(role_id):
    """Delete a role (triggers after_role_delete)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # This DELETE will trigger after_role_delete
    cursor.execute("DELETE FROM roles WHERE role_id = %s", (role_id,))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    flash('Role deleted successfully!', 'success')
    return redirect(url_for('list_roles'))

@app.route('/roles/<int:role_id>/requirements/add', methods=['POST'])
@handle_db_error
def add_role_requirement(role_id):
    """Add skill requirement to a role"""
    skill_id = request.form['skill_id']
    min_proficiency = request.form['min_proficiency_required']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) 
        VALUES (%s, %s, %s)
    """, (role_id, skill_id, min_proficiency))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Skill requirement added successfully!', 'success')
    return redirect(url_for('view_role', role_id=role_id))

@app.route('/roles/<int:role_id>/requirements/<int:skill_id>/delete', methods=['POST'])
@handle_db_error
def delete_role_requirement(role_id, skill_id):
    """Remove skill requirement from a role"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        DELETE FROM role_requirements 
        WHERE role_id = %s AND skill_id = %s
    """, (role_id, skill_id))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Skill requirement removed successfully!', 'success')
    return redirect(url_for('view_role', role_id=role_id))

# ==================== TEAM MEMBERS ====================

@app.route('/members')
@handle_db_error
def list_members():
    """List all team members"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            tm.mem_id,
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name,
            tm.email,
            tm.phone_no,
            r.role_name,
            COUNT(ms.skill_id) as skill_count
        FROM team_members tm
        LEFT JOIN roles r ON tm.role_id = r.role_id
        LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
        GROUP BY tm.mem_id
        ORDER BY tm.first_name, tm.last_name
    """)
    
    members = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('members/list.html', members=members)
@app.route('/members/add', methods=['GET', 'POST'])
@handle_db_error
def add_member():
    """Add a new team member with skills and proficiency (triggers after_member_insert)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Handle JSON request (for progressive save)
        if request.is_json:
            data = request.get_json()
            
            first_name = data.get('first_name', '').strip()
            middle_name = data.get('middle_name', '').strip()
            last_name = data.get('last_name', '').strip()
            email = data.get('email', '').strip()
            phone_no = data.get('phone_no', '').strip()
            role_id = data.get('role_id')
            skills_data = data.get('skills', [])  # Now contains {skill_id, proficiency}
            
            # Validate role_id is provided
            if not role_id or role_id == '' or role_id == 'null':
                return jsonify({'success': False, 'message': 'Role selection is required'}), 400
            
            # Validate Gmail
            gmail_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')
            if not gmail_regex.match(email):
                return jsonify({'success': False, 'message': 'Only Gmail addresses (@gmail.com) are allowed'}), 400
            
            # Validate phone number (10 digits)
            phone_regex = re.compile(r'^\d{10}$')
            if not phone_regex.match(phone_no):
                return jsonify({'success': False, 'message': 'Phone number must be exactly 10 digits'}), 400
            
            # Check for duplicate email
            cursor.execute("SELECT mem_id FROM team_members WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return jsonify({'success': False, 'message': 'Email already exists'}), 400
            
            # Check for duplicate phone
            cursor.execute("SELECT mem_id FROM team_members WHERE phone_no = %s", (phone_no,))
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return jsonify({'success': False, 'message': 'Phone number already exists'}), 400
            
            try:
                # This INSERT will trigger after_member_insert
                cursor.execute("""
                    INSERT INTO team_members (first_name, middle_name, last_name, email, phone_no, role_id) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (first_name, middle_name, last_name, email, phone_no, role_id))
                
                mem_id = cursor.lastrowid
                
                # Add skills with their proficiency levels
                for skill_data in skills_data:
                    skill_id = skill_data.get('skill_id')
                    proficiency = skill_data.get('proficiency', 3)  # Default to 3 if not provided
                    cursor.execute("""
                        INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) 
                        VALUES (%s, %s, %s)
                    """, (mem_id, skill_id, proficiency))
                
                connection.commit()
                
                # Get role name if assigned
                role_name = None
                if role_id:
                    cursor.execute("SELECT role_name FROM roles WHERE role_id = %s", (role_id,))
                    role_result = cursor.fetchone()
                    if role_result:
                        role_name = role_result['role_name']
                
                cursor.close()
                connection.close()
                
                return jsonify({
                    'success': True, 
                    'message': f'Member {first_name} {last_name} added successfully!',
                    'mem_id': mem_id,
                    'role_name': role_name
                }), 200
                
            except Error as e:
                connection.rollback()
                cursor.close()
                connection.close()
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
        
        # Handle traditional form submission (if needed for backward compatibility)
        else:
            first_name = request.form['first_name'].strip()
            middle_name = request.form.get('middle_name', '').strip()
            last_name = request.form['last_name'].strip()
            email = request.form['email'].strip()
            phone_no = request.form['phone_no'].strip()
            role_id = request.form.get('role_id')
            
            # Validate role_id is provided
            if not role_id or role_id == '':
                flash('Role selection is required', 'danger')
                cursor.close()
                connection.close()
                return redirect(url_for('add_member'))
            
            # Validate Gmail
            gmail_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')
            if not gmail_regex.match(email):
                flash('Only Gmail addresses (@gmail.com) are allowed', 'danger')
                cursor.close()
                connection.close()
                return redirect(request.referrer)
            
            # Validate phone number (10 digits)
            phone_regex = re.compile(r'^\d{10}$')
            if not phone_regex.match(phone_no):
                flash('Phone number must be exactly 10 digits', 'danger')
                cursor.close()
                connection.close()
                return redirect(request.referrer)
            
            # This INSERT will trigger after_member_insert
            cursor.execute("""
                INSERT INTO team_members (first_name, middle_name, last_name, email, phone_no, role_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (first_name, middle_name, last_name, email, phone_no, role_id))
            
            mem_id = cursor.lastrowid
            
            # Handle skills with proficiency from form
            selected_skills = request.form.getlist('skills')
            for skill_id in selected_skills:
                proficiency = request.form.get(f'proficiency_{skill_id}', 3)
                cursor.execute("""
                    INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) 
                    VALUES (%s, %s, %s)
                """, (mem_id, skill_id, proficiency))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            flash(f'Team member {first_name} {last_name} added successfully!', 'success')
            return redirect(url_for('list_members'))
    
    # GET request - fetch all skills and roles with requirements
    cursor.execute("""
        SELECT skill_id, skill_name, category 
        FROM skills 
        ORDER BY category, skill_name
    """)
    all_skills = cursor.fetchall()
    
    cursor.execute("""
        SELECT role_id, role_name, description 
        FROM roles 
        ORDER BY role_name
    """)
    all_roles = cursor.fetchall()
    
    # Get role requirements for dynamic filtering
    cursor.execute("""
        SELECT 
            rr.role_id,
            rr.skill_id,
            rr.min_proficiency_required
        FROM role_requirements rr
        ORDER BY rr.role_id, rr.skill_id
    """)
    requirements = cursor.fetchall()
    
    # Organize requirements by role_id
    role_requirements = {}
    for req in requirements:
        role_id = req['role_id']
        if role_id not in role_requirements:
            role_requirements[role_id] = []
        role_requirements[role_id].append({
            'skill_id': req['skill_id'],
            'min_proficiency_required': req['min_proficiency_required']
        })
    
    cursor.close()
    connection.close()
    
    # Convert to JSON for JavaScript
    import json
    all_roles_json = json.dumps(all_roles)
    role_requirements_json = json.dumps(role_requirements)
    
    return render_template('members/add.html', 
                         all_skills=all_skills,
                         all_roles_json=all_roles_json,
                         role_requirements_json=role_requirements_json)


@app.route('/members/<int:mem_id>')
@handle_db_error
def view_member(mem_id):
    """View member profile with skills"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get member details
    cursor.execute("""
        SELECT 
            tm.*,
            r.role_name,
            r.description as role_description,
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name
        FROM team_members tm
        LEFT JOIN roles r ON tm.role_id = r.role_id
        WHERE tm.mem_id = %s
    """, (mem_id,))
    member = cursor.fetchone()
    
    if not member:
        flash('Member not found', 'warning')
        return redirect(url_for('list_members'))
    
    # Get member skills
    cursor.execute("""
        SELECT 
            s.skill_id,
            s.skill_name,
            s.category,
            ms.proficiency_level,
            ms.updated_at
        FROM mem_skills ms
        JOIN skills s ON ms.skill_id = s.skill_id
        WHERE ms.mem_id = %s
        ORDER BY s.category, s.skill_name
    """, (mem_id,))
    skills = cursor.fetchall()
    
    # Get all available skills for adding new ones
    cursor.execute("""
        SELECT skill_id, skill_name, category 
        FROM skills 
        WHERE skill_id NOT IN (
            SELECT skill_id FROM mem_skills WHERE mem_id = %s
        )
        ORDER BY category, skill_name
    """, (mem_id,))
    available_skills = cursor.fetchall()
    
    # Get eligible roles using stored procedure
    cursor.callproc('Get_Eligible_Roles_For_Member', (mem_id,))
    eligible_roles = []
    for result in cursor.stored_results():
        eligible_roles = result.fetchall()
    
    # Get all roles for the dropdown
    cursor.execute("SELECT role_id, role_name FROM roles ORDER BY role_name")
    all_roles = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('members/view.html', 
                         member=member, 
                         skills=skills,
                         available_skills=available_skills,
                         eligible_roles=eligible_roles,
                         all_roles=all_roles)

@app.route('/members/<int:mem_id>/edit', methods=['GET', 'POST'])
@handle_db_error
def edit_member(mem_id):
    """Edit team member details with skill management and proficiency (triggers after_member_update and validate_role_eligibility)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form['last_name'].strip()
        email = request.form['email'].strip()
        phone_no = request.form['phone_no'].strip()
        role_id = request.form.get('role_id')
        
        # Get selected skills from form
        selected_skills = request.form.getlist('skills')
        selected_skills = [int(s) for s in selected_skills]
        
        # Get proficiency levels for each skill
        skill_proficiencies = {}
        for skill_id in selected_skills:
            prof_value = request.form.get(f'proficiency_{skill_id}', 3)
            skill_proficiencies[skill_id] = int(prof_value)
        
        # Validate role_id is provided
        if not role_id or role_id == '':
            flash('Role selection is required', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_member', mem_id=mem_id))
        
        # Validate Gmail
        gmail_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')
        if not gmail_regex.match(email):
            flash('Only Gmail addresses (@gmail.com) are allowed', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_member', mem_id=mem_id))
        
        # Validate phone number (10 digits)
        phone_regex = re.compile(r'^\d{10}$')
        if not phone_regex.match(phone_no):
            flash('Phone number must be exactly 10 digits', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_member', mem_id=mem_id))
        
        # Check for duplicate email (excluding current member)
        cursor.execute("SELECT mem_id FROM team_members WHERE email = %s AND mem_id != %s", (email, mem_id))
        if cursor.fetchone():
            flash('Email already exists for another member', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_member', mem_id=mem_id))
        
        # Check for duplicate phone (excluding current member)
        cursor.execute("SELECT mem_id FROM team_members WHERE phone_no = %s AND mem_id != %s", (phone_no, mem_id))
        if cursor.fetchone():
            flash('Phone number already exists for another member', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_member', mem_id=mem_id))
        
        try:
            # Get current skills with proficiency for comparison
            cursor.execute("SELECT skill_id, proficiency_level FROM mem_skills WHERE mem_id = %s", (mem_id,))
            current_skills_data = {row['skill_id']: row['proficiency_level'] for row in cursor.fetchall()}
            current_skills = set(current_skills_data.keys())
            new_skills = set(selected_skills)
            
            # Calculate changes
            skills_to_add = new_skills - current_skills
            skills_to_remove = current_skills - new_skills
            skills_to_update = new_skills & current_skills  # Skills that exist in both
            
            # This UPDATE will trigger validate_role_eligibility and after_member_update
            cursor.execute("""
                UPDATE team_members 
                SET first_name = %s, middle_name = %s, last_name = %s, 
                    email = %s, phone_no = %s, role_id = %s 
                WHERE mem_id = %s
            """, (first_name, middle_name, last_name, email, phone_no, role_id, mem_id))
            
            # Add new skills with their proficiency levels
            for skill_id in skills_to_add:
                proficiency = skill_proficiencies.get(skill_id, 3)
                cursor.execute("""
                    INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) 
                    VALUES (%s, %s, %s)
                """, (mem_id, skill_id, proficiency))
            
            # Update proficiency for existing skills (only if changed)
            for skill_id in skills_to_update:
                new_proficiency = skill_proficiencies.get(skill_id, 3)
                old_proficiency = current_skills_data.get(skill_id)
                if new_proficiency != old_proficiency:
                    cursor.execute("""
                        UPDATE mem_skills 
                        SET proficiency_level = %s 
                        WHERE mem_id = %s AND skill_id = %s
                    """, (new_proficiency, mem_id, skill_id))
            
            # Remove deselected skills
            for skill_id in skills_to_remove:
                cursor.execute("""
                    DELETE FROM mem_skills 
                    WHERE mem_id = %s AND skill_id = %s
                """, (mem_id, skill_id))
            
            connection.commit()
            
            # Build success message
            changes = []
            if skills_to_add:
                changes.append(f"{len(skills_to_add)} skill(s) added")
            if skills_to_remove:
                changes.append(f"{len(skills_to_remove)} skill(s) removed")
            
            if changes:
                flash(f'Member updated successfully! Changes: {", ".join(changes)}', 'success')
            else:
                flash('Member updated successfully!', 'success')
            
        except Error as e:
            connection.rollback()
            # Check if it's the role eligibility error
            if '45000' in str(e) or 'Ineligible for Role' in str(e):
                flash('Cannot assign this role: Member does not meet the minimum skill requirements.', 'danger')
            else:
                flash(f'Error updating member: {str(e)}', 'danger')
        
        cursor.close()
        connection.close()
        
        return redirect(url_for('list_members'))
    
    # GET request
    cursor.execute("""
        SELECT 
            tm.*,
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name
        FROM team_members tm
        WHERE tm.mem_id = %s
    """, (mem_id,))
    member = cursor.fetchone()
    
    if not member:
        flash('Member not found', 'warning')
        cursor.close()
        connection.close()
        return redirect(url_for('list_members'))
    
    # Get all skills
    cursor.execute("""
        SELECT skill_id, skill_name, category 
        FROM skills 
        ORDER BY category, skill_name
    """)
    all_skills = cursor.fetchall()
    
    # Get member's current skills WITH proficiency levels
    cursor.execute("""
        SELECT skill_id, proficiency_level 
        FROM mem_skills 
        WHERE mem_id = %s
    """, (mem_id,))
    member_skills_data = cursor.fetchall()
    member_skill_ids = [row['skill_id'] for row in member_skills_data]
    member_skill_proficiencies = {row['skill_id']: row['proficiency_level'] for row in member_skills_data}
    
    # Get all roles for dropdown
    cursor.execute("""
        SELECT role_id, role_name, description 
        FROM roles 
        ORDER BY role_name
    """)
    all_roles = cursor.fetchall()
    
    # Get role requirements for dynamic filtering
    cursor.execute("""
        SELECT 
            rr.role_id,
            rr.skill_id,
            rr.min_proficiency_required
        FROM role_requirements rr
        ORDER BY rr.role_id, rr.skill_id
    """)
    requirements = cursor.fetchall()
    
    # Organize requirements by role_id
    role_requirements = {}
    for req in requirements:
        role_id = req['role_id']
        if role_id not in role_requirements:
            role_requirements[role_id] = []
        role_requirements[role_id].append({
            'skill_id': req['skill_id'],
            'min_proficiency_required': req['min_proficiency_required']
        })
    
    cursor.close()
    connection.close()
    
    # Convert to JSON for JavaScript
    import json
    all_roles_json = json.dumps(all_roles)
    role_requirements_json = json.dumps(role_requirements)
    member_skill_proficiencies_json = json.dumps(member_skill_proficiencies)
    
    return render_template('members/edit.html', 
                         member=member,
                         all_skills=all_skills,
                         member_skill_ids=member_skill_ids,
                         member_skill_proficiencies=member_skill_proficiencies_json,
                         all_roles=all_roles,
                         all_roles_json=all_roles_json,
                         role_requirements_json=role_requirements_json)

@app.route('/members/<int:mem_id>/delete', methods=['POST'])
@handle_db_error
def delete_member(mem_id):
    """Delete a team member (triggers after_member_delete)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # This DELETE will trigger after_member_delete
    cursor.execute("DELETE FROM team_members WHERE mem_id = %s", (mem_id,))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('list_members'))

# ==================== SKILLS ====================

@app.route('/skills')
@handle_db_error
def list_skills():
    """List all skills in catalog"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            s.skill_id,
            s.skill_name,
            s.category,
            COUNT(DISTINCT ms.mem_id) as member_count,
            COALESCE(AVG(ms.proficiency_level), 0) as avg_proficiency
        FROM skills s
        LEFT JOIN mem_skills ms ON s.skill_id = ms.skill_id
        GROUP BY s.skill_id
        ORDER BY s.category, s.skill_name
    """)
    
    skills = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('skills/list.html', skills=skills)


@app.route('/skills/add', methods=['GET', 'POST'])
@handle_db_error
def add_skill():
    """Add a new skill to catalog with optional role assignments (triggers after_skill_insert)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        skill_name = request.form['skill_name'].strip()
        category = request.form['category']
        
        # Get role assignments from form (optional)
        role_ids = request.form.getlist('role_ids[]')
        min_proficiencies = request.form.getlist('min_proficiencies[]')
        
        # This INSERT will trigger after_skill_insert
        cursor.execute("""
            INSERT INTO skills (skill_name, category) 
            VALUES (%s, %s)
        """, (skill_name, category))
        
        # Get the newly created skill_id
        skill_id = cursor.lastrowid
        
        # Insert role requirements if any were specified
        if role_ids and min_proficiencies:
            for role_id, min_prof in zip(role_ids, min_proficiencies):
                if role_id and min_prof:  # Only insert if both values are present
                    cursor.execute("""
                        INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) 
                        VALUES (%s, %s, %s)
                    """, (role_id, skill_id, min_prof))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash(f'Skill "{skill_name}" added successfully!', 'success')
        return redirect(url_for('view_skill', skill_id=skill_id))
    
    # GET request - get all roles for the dropdown
    cursor.execute("""
        SELECT role_id, role_name 
        FROM roles 
        ORDER BY role_name
    """)
    roles = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Convert roles to JSON for JavaScript
    import json
    roles_json = json.dumps(roles)
    
    categories = ['Technical', 'Clinical', 'Soft Skill', 'Regulatory']
    return render_template('skills/add.html', categories=categories, roles_json=roles_json)

@app.route('/skills/<int:skill_id>')
@handle_db_error
def view_skill(skill_id):
    """View skill details and who has it"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get skill details
    cursor.execute("SELECT * FROM skills WHERE skill_id = %s", (skill_id,))
    skill = cursor.fetchone()
    
    if not skill:
        flash('Skill not found', 'warning')
        return redirect(url_for('list_skills'))
    
    # Get members with this skill
    cursor.execute("""
        SELECT 
            tm.mem_id,
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name,
            r.role_name,
            tm.email,
            ms.proficiency_level,
            ms.updated_at
        FROM mem_skills ms
        JOIN team_members tm ON ms.mem_id = tm.mem_id
        LEFT JOIN roles r ON tm.role_id = r.role_id
        WHERE ms.skill_id = %s
        ORDER BY ms.proficiency_level DESC, tm.first_name, tm.last_name
    """, (skill_id,))
    members = cursor.fetchall()
    
    # Get roles requiring this skill
    cursor.execute("""
        SELECT 
            r.role_id,
            r.role_name,
            rr.min_proficiency_required
        FROM role_requirements rr
        JOIN roles r ON rr.role_id = r.role_id
        WHERE rr.skill_id = %s
        ORDER BY r.role_name
    """, (skill_id,))
    required_by_roles = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('skills/view.html', 
                         skill=skill, 
                         members=members,
                         required_by_roles=required_by_roles)


@app.route('/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@handle_db_error
def edit_skill(skill_id):
    """Edit skill name, category, and role assignments (triggers after_skill_update_master)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        skill_name = request.form['skill_name'].strip()
        category = request.form['category']
        
        # Get role requirement updates
        existing_role_ids = request.form.getlist('existing_role_ids[]')
        existing_min_proficiencies = request.form.getlist('existing_min_proficiencies[]')
        
        # Get new roles to add
        new_role_ids = request.form.getlist('new_role_ids[]')
        new_min_proficiencies = request.form.getlist('new_min_proficiencies[]')
        
        # Get roles marked for deletion
        roles_to_delete = request.form.get('roles_to_delete', '')
        roles_to_delete_list = [r.strip() for r in roles_to_delete.split(',') if r.strip()]
        
        # Validate inputs
        if not skill_name:
            flash('Skill name cannot be empty', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_skill', skill_id=skill_id))
        
        if category not in ['Technical', 'Clinical', 'Soft Skill', 'Regulatory']:
            flash('Invalid category selected', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('edit_skill', skill_id=skill_id))
        
        # This UPDATE will trigger after_skill_update_master
        cursor.execute("""
            UPDATE skills 
            SET skill_name = %s, category = %s 
            WHERE skill_id = %s
        """, (skill_name, category, skill_id))
        
        # Delete marked role requirements
        if roles_to_delete_list:
            for role_id in roles_to_delete_list:
                cursor.execute("""
                    DELETE FROM role_requirements 
                    WHERE role_id = %s AND skill_id = %s
                """, (role_id, skill_id))
        
        # Update existing role requirements (proficiency levels)
        if existing_role_ids and existing_min_proficiencies:
            for role_id, min_prof in zip(existing_role_ids, existing_min_proficiencies):
                if role_id and min_prof and role_id not in roles_to_delete_list:
                    cursor.execute("""
                        UPDATE role_requirements 
                        SET min_proficiency_required = %s 
                        WHERE role_id = %s AND skill_id = %s
                    """, (min_prof, role_id, skill_id))
        
        # Insert new role requirements
        if new_role_ids and new_min_proficiencies:
            for role_id, min_prof in zip(new_role_ids, new_min_proficiencies):
                if role_id and min_prof:  # Only insert if both values are present
                    cursor.execute("""
                        INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) 
                        VALUES (%s, %s, %s)
                    """, (role_id, skill_id, min_prof))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash(f'Skill "{skill_name}" updated successfully!', 'success')
        return redirect(url_for('view_skill', skill_id=skill_id))
    
    # GET request - show the edit form
    cursor.execute("SELECT * FROM skills WHERE skill_id = %s", (skill_id,))
    skill = cursor.fetchone()
    
    if not skill:
        flash('Skill not found', 'warning')
        cursor.close()
        connection.close()
        return redirect(url_for('list_skills'))
    
    # Get existing role requirements for this skill
    cursor.execute("""
        SELECT 
            r.role_id,
            r.role_name,
            rr.min_proficiency_required
        FROM role_requirements rr
        JOIN roles r ON rr.role_id = r.role_id
        WHERE rr.skill_id = %s
        ORDER BY r.role_name
    """, (skill_id,))
    existing_requirements = cursor.fetchall()
    
    # Get all roles that are NOT already assigned to this skill (for new additions)
    cursor.execute("""
        SELECT role_id, role_name 
        FROM roles 
        WHERE role_id NOT IN (
            SELECT role_id FROM role_requirements WHERE skill_id = %s
        )
        ORDER BY role_name
    """, (skill_id,))
    available_roles = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Convert to JSON for JavaScript
    import json
    available_roles_json = json.dumps(available_roles)
    existing_role_ids_json = json.dumps([req['role_id'] for req in existing_requirements])
    
    categories = ['Technical', 'Clinical', 'Soft Skill', 'Regulatory']
    return render_template('skills/edit.html', 
                         skill=skill, 
                         categories=categories,
                         existing_requirements=existing_requirements,
                         available_roles_json=available_roles_json,
                         existing_role_ids_json=existing_role_ids_json)

@app.route('/skills/<int:skill_id>/delete', methods=['POST'])
@handle_db_error
def delete_skill(skill_id):
    """Delete a skill from catalog (triggers after_skill_delete)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # This DELETE will trigger after_skill_delete
    cursor.execute("DELETE FROM skills WHERE skill_id = %s", (skill_id,))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    flash('Skill deleted successfully!', 'success')
    return redirect(url_for('list_skills'))

# ==================== MEMBER SKILLS ====================

@app.route('/members/<int:mem_id>/skills/add', methods=['POST'])
@handle_db_error
def add_member_skill(mem_id):
    """Add a skill to a member (triggers after_memskill_insert)"""
    skill_id = request.form['skill_id']
    proficiency_level = request.form['proficiency_level']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # This INSERT will trigger after_memskill_insert
    cursor.execute("""
        INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) 
        VALUES (%s, %s, %s)
    """, (mem_id, skill_id, proficiency_level))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Skill added successfully!', 'success')
    return redirect(url_for('view_member', mem_id=mem_id))

@app.route('/members/<int:mem_id>/skills/<int:skill_id>/update', methods=['POST'])
@handle_db_error
def update_member_skill(mem_id, skill_id):
    """Update skill proficiency level (triggers after_memskill_update)"""
    proficiency_level = request.form['proficiency_level']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # This UPDATE will trigger after_memskill_update (only logs if level actually changed)
    cursor.execute("""
        UPDATE mem_skills 
        SET proficiency_level = %s 
        WHERE mem_id = %s AND skill_id = %s
    """, (proficiency_level, mem_id, skill_id))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Skill proficiency updated successfully!', 'success')
    return redirect(url_for('view_member', mem_id=mem_id))

@app.route('/members/<int:mem_id>/skills/<int:skill_id>/delete', methods=['POST'])
@handle_db_error
def delete_member_skill(mem_id, skill_id):
    """Remove a skill from a member (triggers after_memskill_delete)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # This DELETE will trigger after_memskill_delete
    cursor.execute("""
        DELETE FROM mem_skills 
        WHERE mem_id = %s AND skill_id = %s
    """, (mem_id, skill_id))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Skill removed successfully!', 'success')
    return redirect(url_for('view_member', mem_id=mem_id))

# ==================== FIND EXPERTS (Stored Procedure) ====================

@app.route('/find-experts', methods=['GET', 'POST'])
@handle_db_error
def find_experts():
    """Find experts for a project using stored procedure Find_Experts_For_Project"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT skill_id, skill_name, category FROM skills ORDER BY category, skill_name"
    )
    all_skills = cursor.fetchall()

    experts = []
    selected_skill = None
    min_proficiency = 3
    searched = False

    if request.method == 'POST':
        searched = True
        selected_skill = request.form['skill_name']
        min_proficiency = int(request.form['min_proficiency'])

        # Call stored procedure
        cursor.callproc(
            'Find_Experts_For_Project',
            (selected_skill, min_proficiency)
        )

        for result in cursor.stored_results():
            experts = result.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'find_experts.html',
        all_skills=all_skills,
        experts=experts,
        selected_skill=selected_skill,
        min_proficiency=min_proficiency,
        searched=searched
    )

# ==================== MEMBER PROFILE (Stored Procedure) ====================

@app.route('/profile/<email>')
@handle_db_error
def member_profile(email):
    """Get member profile using stored procedure Get_Member_Profile"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Call stored procedure
    cursor.callproc('Get_Member_Profile', (email,))
    
    # Fetch results
    profile_data = []
    for result in cursor.stored_results():
        profile_data = result.fetchall()
    
    cursor.close()
    connection.close()
    
    if not profile_data:
        flash('Member not found', 'warning')
        return redirect(url_for('list_members'))
    
    member = {
        'full_name': profile_data[0]['full_name'],
        'role_name': profile_data[0]['role_name'],
        'phone_no': profile_data[0]['phone_no'],
        'email': email
    }
    
    return render_template('member_profile.html', member=member, skills=profile_data)

# ==================== ELIGIBLE ROLES (Stored Procedure) ====================

@app.route('/members/<int:mem_id>/eligible-roles')
@handle_db_error
def eligible_roles(mem_id):
    """View roles that member is eligible for using Get_Eligible_Roles_For_Member"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get member details
    cursor.execute("""
        SELECT 
            mem_id,
            CONCAT_WS(' ', first_name, NULLIF(middle_name, ''), last_name) AS full_name,
            email
        FROM team_members
        WHERE mem_id = %s
    """, (mem_id,))
    member = cursor.fetchone()
    
    if not member:
        flash('Member not found', 'warning')
        return redirect(url_for('list_members'))
    
    # Call stored procedure
    cursor.callproc('Get_Eligible_Roles_For_Member', (mem_id,))
    
    eligible = []
    for result in cursor.stored_results():
        eligible = result.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('members/eligible_roles.html', 
                         member=member, 
                         eligible_roles=eligible)

# ==================== AUDIT LOGS ====================

@app.route('/audit-logs')
@handle_db_error
def audit_logs():
    """View audit log history (populated by triggers)"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter parameters
    table_filter = request.args.get('table', '')
    operation_filter = request.args.get('operation', '')
    limit = request.args.get('limit', 100, type=int)
    
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if table_filter:
        query += " AND table_name = %s"
        params.append(table_filter)
    
    if operation_filter:
        query += " AND operation_type = %s"
        params.append(operation_filter)
    
    query += " ORDER BY change_date DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    # Get distinct tables and operations for filters
    cursor.execute("SELECT DISTINCT table_name FROM audit_logs ORDER BY table_name")
    tables = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT operation_type FROM audit_logs ORDER BY operation_type")
    operations = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('audit_logs.html', 
                         logs=logs,
                         tables=tables,
                         operations=operations,
                         table_filter=table_filter,
                         operation_filter=operation_filter,
                         limit=limit)

# ==================== REPORTS ====================

@app.route('/reports')
@handle_db_error
def reports():
    """Generate various reports"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Skills by category
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as skill_count,
            COUNT(DISTINCT ms.mem_id) as members_with_skills
        FROM skills s
        LEFT JOIN mem_skills ms ON s.skill_id = ms.skill_id
        GROUP BY category
        ORDER BY category
    """)
    category_stats = cursor.fetchall()
    
    # Top skills (most common)
    cursor.execute("""
        SELECT 
            s.skill_name,
            s.category,
            COUNT(ms.mem_id) as member_count,
            AVG(ms.proficiency_level) as avg_proficiency
        FROM skills s
        LEFT JOIN mem_skills ms ON s.skill_id = ms.skill_id
        GROUP BY s.skill_id
        HAVING member_count > 0
        ORDER BY member_count DESC
        LIMIT 10
    """)
    top_skills = cursor.fetchall()
    
    # Members by skill count
    cursor.execute("""
        SELECT 
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name,
            r.role_name,
            COUNT(ms.skill_id) as skill_count,
            AVG(ms.proficiency_level) as avg_proficiency
        FROM team_members tm
        LEFT JOIN roles r ON tm.role_id = r.role_id
        LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
        GROUP BY tm.mem_id
        ORDER BY skill_count DESC
    """)
    member_stats = cursor.fetchall()
    
    # Role requirements summary
    cursor.execute("""
        SELECT 
            r.role_name,
            COUNT(rr.skill_id) as required_skills,
            COUNT(DISTINCT tm.mem_id) as current_members
        FROM roles r
        LEFT JOIN role_requirements rr ON r.role_id = rr.role_id
        LEFT JOIN team_members tm ON r.role_id = tm.role_id
        GROUP BY r.role_id
        ORDER BY r.role_name
    """)
    role_stats = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('reports.html',
                         category_stats=category_stats,
                         top_skills=top_skills,
                         member_stats=member_stats,
                         role_stats=role_stats)

@app.route('/reports/user-skills')
@handle_db_error
def user_skills_report():
    """User-wise skill assignment report"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            tm.mem_id,
            CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name,
            tm.email,
            r.role_name,
            GROUP_CONCAT(
                CONCAT(s.skill_name, ' (', ms.proficiency_level, ')')
                ORDER BY s.category, s.skill_name
                SEPARATOR ', '
            ) AS skills
        FROM team_members tm
        LEFT JOIN roles r ON tm.role_id = r.role_id
        LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
        LEFT JOIN skills s ON ms.skill_id = s.skill_id
        GROUP BY tm.mem_id
        ORDER BY tm.first_name, tm.last_name
    """)

    report = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'reports/user_skills.html',
        report=report
    )

# ==================== API ENDPOINTS ====================

@app.route('/api/skills')
def api_skills():
    """API endpoint to get all skills"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM skills ORDER BY category, skill_name")
    skills = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(skills)

@app.route('/api/members')
def api_members():
    """API endpoint to get all members"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            mem_id, 
            CONCAT_WS(' ', first_name, NULLIF(middle_name, ''), last_name) AS full_name,
            email, 
            phone_no,
            role_id
        FROM team_members
        ORDER BY first_name, last_name
    """)
    members = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(members)

@app.route('/api/roles')
def api_roles():
    """API endpoint to get all roles"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM roles ORDER BY role_name")
    roles = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(roles)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)