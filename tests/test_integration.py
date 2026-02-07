from ISO_Standard_DB.app import get_db_connection

def test_add_member_flow(client):
    """Test adding a member and verifying DB entry + Trigger Audit Log"""
    
    # 1. Simulate POST request to add member
    response = client.post('/members/add', data={
        'full_name': 'Integration Test User',
        'email': 'integration@gmail.com', # Valid gmail
        'role': 'Integration Tester'
    }, follow_redirects=True)

    # 2. Check UI Response
    assert response.status_code == 200
    assert b'Team member Integration Test User added successfully!' in response.data

    # 3. Check Database (Integration)
    # Use the app's get_db_connection which should now use the TEST_DB_NAME
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # DEBUG: Check connection
    # cursor.execute("SELECT DATABASE()")
    
    cursor.execute("SELECT * FROM team_members WHERE email = 'integration@gmail.com'")
    member = cursor.fetchone()
    assert member is not None
    assert member['full_name'] == 'Integration Test User'

    # 4. Check Trigger (Audit Log)
    # The 'after_member_insert' trigger should have fired
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE table_name = 'team_members' AND operation_type = 'INSERT' AND record_id = %s
    """, (member['mem_id'],))
    
    log = cursor.fetchone()
    assert log is not None
    assert 'Integration Test User' in log['new_value'] # Ensuring trigger captured the name
    
    cursor.close()
    conn.close()

def test_invalid_email_validation(client):
    """Test that non-gmail emails are rejected"""
    response = client.post('/members/add', data={
        'full_name': 'Bad User',
        'email': 'bad@yahoo.com',
        'role': 'Tester'
    }, follow_redirects=True)

    # Should stay on page or redirect back - the app redirects to request.referrer
    # We check for the flash message
    assert b'Only Gmail addresses' in response.data
    
    # Verify it was NOT added to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM team_members WHERE email = 'bad@yahoo.com'")
    assert cursor.fetchone() is None
    conn.close()

def test_add_skill_and_assign(client):
    """Test adding a skill, then assigning it to a member (Triggers check)"""
    
    # Prerequisite: We need a member. Let's reuse 'Integration Test User' created in previous test?
    # NO, tests should be independent if possible, or order-independent. 
    # But pytest runs alphabetically/sequentially. To be safe, verify or create.
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ensure member exists
    cursor.execute("SELECT mem_id FROM team_members WHERE email = 'integration@gmail.com'")
    member = cursor.fetchone()
    
    if not member:
        cursor.execute("INSERT INTO team_members (full_name, email, role) VALUES ('Skill User', 'skill@gmail.com', 'Dev')")
        conn.commit()
        mem_id = cursor.lastrowid
    else:
        mem_id = member['mem_id']
        
    cursor.close()
    conn.close()
    
    # 1. Add a new Skill via POST
    response = client.post('/skills/add', data={
        'skill_name': 'Pytest Automation',
        'category': 'Technical'
    }, follow_redirects=True)
    
    # with open('/tmp/response_debug.html', 'wb') as f:
    #     f.write(response.data)

    assert response.status_code == 200
    # Jinja2 escapes the quotes, so we need to match the escaped version
    assert b'Skill &#34;Pytest Automation&#34; added successfully!' in response.data
    
    # 2. Assign this skill to the member via POST
    # First get the skill_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT skill_id FROM skills WHERE skill_name = 'Pytest Automation'")
    skill_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    response = client.post(f'/members/{mem_id}/skills/add', data={
        'skill_id': skill_id,
        'proficiency_level': 5
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Skill added successfully!' in response.data
    
    # 3. Check Audit Log for Mem_Skill Insert
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE table_name = 'mem_skills' 
        AND operation_type = 'INSERT' 
        AND record_id = %s
    """, (f"{mem_id}-{skill_id}",))
    
    log = cursor.fetchone()
    assert log is not None
    assert 'Proficiency: 5' in log['new_value']
    
    cursor.close()
    conn.close()
