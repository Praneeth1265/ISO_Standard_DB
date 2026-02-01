import email

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

# ==================== ROUTES ====================

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
    
    # Total skills in catalog
    cursor.execute("SELECT COUNT(*) as count FROM skills")
    stats['total_skills'] = cursor.fetchone()['count']
    
    # Total skill assignments
    cursor.execute("SELECT COUNT(*) as count FROM mem_skills")
    stats['total_assignments'] = cursor.fetchone()['count']
    
    # Recent audit logs
    cursor.execute("""
        SELECT * FROM audit_logs 
        ORDER BY change_date DESC 
        LIMIT 5
    """)
    stats['recent_logs'] = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('index.html', stats=stats)

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
            tm.full_name,
            tm.email,
            tm.role,
            COUNT(ms.skill_id) as skill_count
        FROM team_members tm
        LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
        GROUP BY tm.mem_id
        ORDER BY tm.full_name
    """)
    
    members = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('members/list.html', members=members)

@app.route('/members/add', methods=['GET', 'POST'])
@handle_db_error
def add_member():
    """Add a new team member"""
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email'].strip()
        role = request.form['role']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        

        gmail_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')

       

        if not gmail_regex.match(email):
            flash('Only Gmail addresses (@gmail.com) are allowed', 'danger')
            return redirect(request.referrer)
        else:
            cursor.execute("""
            INSERT INTO team_members (full_name, email, role) 
            VALUES (%s, %s, %s)
            """, (full_name, email, role))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash(f'Team member {full_name} added successfully!', 'success')
        return redirect(url_for('list_members'))
    
    return render_template('members/add.html')

@app.route('/members/<int:mem_id>')
@handle_db_error
def view_member(mem_id):
    """View member profile with skills"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get member details
    cursor.execute("SELECT * FROM team_members WHERE mem_id = %s", (mem_id,))
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
    
    cursor.close()
    connection.close()
    
    return render_template('members/view.html', 
                         member=member, 
                         skills=skills,
                         available_skills=available_skills)

@app.route('/members/<int:mem_id>/edit', methods=['GET', 'POST'])
@handle_db_error
def edit_member(mem_id):
    """Edit team member details"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        role = request.form['role']
        
        cursor.execute("""
            UPDATE team_members 
            SET full_name = %s, email = %s, role = %s 
            WHERE mem_id = %s
        """, (full_name, email, role, mem_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('Member updated successfully!', 'success')
        return redirect(url_for('view_member', mem_id=mem_id))
    
    cursor.execute("SELECT * FROM team_members WHERE mem_id = %s", (mem_id,))
    member = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return render_template('members/edit.html', member=member)

@app.route('/members/<int:mem_id>/delete', methods=['POST'])
@handle_db_error
def delete_member(mem_id):
    """Delete a team member"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("DELETE FROM team_members WHERE mem_id = %s", (mem_id,))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('list_members'))

 #==================== EDIT SKILL ROUTE ====================
# Add this route after the delete_skill route in your Flask app

@app.route('/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@handle_db_error
def edit_skill(skill_id):
    """Edit skill name and category"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        skill_name = request.form['skill_name'].strip()
        category = request.form['category']
        
        # Validate inputs
        if not skill_name:
            flash('Skill name cannot be empty', 'danger')
            return redirect(url_for('edit_skill', skill_id=skill_id))
        
        if category not in ['Technical', 'Clinical', 'Soft Skill', 'Regulatory']:
            flash('Invalid category selected', 'danger')
            return redirect(url_for('edit_skill', skill_id=skill_id))
        
        # Update the skill
        cursor.execute("""
            UPDATE skills 
            SET skill_name = %s, category = %s 
            WHERE skill_id = %s
        """, (skill_name, category, skill_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash(f'Skill "{skill_name}" updated successfully!', 'success')
        return redirect(url_for('view_skill', skill_id=skill_id))
    
    # GET request - show the edit form
    cursor.execute("SELECT * FROM skills WHERE skill_id = %s", (skill_id,))
    skill = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    if not skill:
        flash('Skill not found', 'warning')
        return redirect(url_for('list_skills'))
    
    return render_template('skills/edit.html', skill=skill)

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
            COUNT(ms.mem_id) as member_count,
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
    """Add a new skill to catalog"""
    if request.method == 'POST':
        skill_name = request.form['skill_name']
        category = request.form['category']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO skills (skill_name, category) 
            VALUES (%s, %s)
        """, (skill_name, category))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash(f'Skill "{skill_name}" added successfully!', 'success')
        return redirect(url_for('list_skills'))
    
    categories = ['Technical', 'Clinical', 'Soft Skill', 'Regulatory']
    return render_template('skills/add.html', categories=categories)

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
            tm.full_name,
            tm.role,
            tm.email,
            ms.proficiency_level,
            ms.updated_at
        FROM mem_skills ms
        JOIN team_members tm ON ms.mem_id = tm.mem_id
        WHERE ms.skill_id = %s
        ORDER BY ms.proficiency_level DESC, tm.full_name
    """, (skill_id,))
    
    members = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('skills/view.html', skill=skill, members=members)
@app.route('/reports/user-skills')
@handle_db_error
def user_skills_report():
    """User-wise skill assignment report"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            tm.mem_id,
            tm.full_name,
            tm.email,
            tm.role,
            GROUP_CONCAT(
                CONCAT(s.skill_name, ' (', ms.proficiency_level, ')')
                ORDER BY s.category, s.skill_name
                SEPARATOR ', '
            ) AS skills
        FROM team_members tm
        LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
        LEFT JOIN skills s ON ms.skill_id = s.skill_id
        GROUP BY tm.mem_id
        ORDER BY tm.full_name
    """)

    report = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'reports/user_skills.html',
        report=report
    )


@app.route('/skills/<int:skill_id>/delete', methods=['POST'])
@handle_db_error
def delete_skill(skill_id):
    """Delete a skill from catalog"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
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
    """Add a skill to a member"""
    skill_id = request.form['skill_id']
    proficiency_level = request.form['proficiency_level']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
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
    """Update skill proficiency level"""
    proficiency_level = request.form['proficiency_level']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
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
    """Remove a skill from a member"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        DELETE FROM mem_skills 
        WHERE mem_id = %s AND skill_id = %s
    """, (mem_id, skill_id))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Skill removed successfully!', 'success')
    return redirect(url_for('view_member', mem_id=mem_id))

# ==================== FIND EXPERTS ====================
@app.route('/find-experts', methods=['GET', 'POST'])
@handle_db_error
def find_experts():
    """Find experts for a project using stored procedure"""
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
    """Get member profile using stored procedure"""
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
        'role': profile_data[0]['role'],
        'email': email
    }
    
    return render_template('member_profile.html', member=member, skills=profile_data)

# ==================== AUDIT LOGS ====================

@app.route('/audit-logs')
@handle_db_error
def audit_logs():
    """View audit log history"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter parameters
    table_filter = request.args.get('table', '')
    operation_filter = request.args.get('operation', '')
    limit = request.args.get('limit', 50, type=int)
    
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
    
    cursor.close()
    connection.close()
    
    return render_template('audit_logs.html', 
                         logs=logs,
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
            tm.full_name,
            tm.role,
            COUNT(ms.skill_id) as skill_count,
            AVG(ms.proficiency_level) as avg_proficiency
        FROM team_members tm
        LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
        GROUP BY tm.mem_id
        ORDER BY skill_count DESC
    """)
    member_stats = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('reports.html',
                         category_stats=category_stats,
                         top_skills=top_skills,
                         member_stats=member_stats)

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
    
    cursor.execute("SELECT mem_id, full_name, email, role FROM team_members")
    members = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(members)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
