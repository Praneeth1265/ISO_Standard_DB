import pytest
from app import get_db_connection

def test_member_update_delete_triggers(client):
    """Test UPDATE and DELETE triggers for team_members table"""
    
    # 1. Setup: Create a member directly (we know INSERT triggers work)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("INSERT INTO team_members (full_name, email, role) VALUES ('Trigger Test', 'trigger@test.com', 'Tester')")
    conn.commit()
    mem_id = cursor.lastrowid
    cursor.close()
    conn.close()

    # 2. Test UPDATE Trigger via App (or direct DB, let's use direct DB for precision on triggers)
    # Using app routes is better for "Integration", but direct DB is cleaner for verifying specific DB logic.
    # Let's use direct DB execution to isolate the DB logic test.
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Perform UPDATE
    cursor.execute("UPDATE team_members SET role = 'Senior Tester' WHERE mem_id = %s", (mem_id,))
    conn.commit()
    
    # Verify Audit Log for UPDATE
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE table_name = 'team_members' AND operation_type = 'UPDATE' AND record_id = %s
    """, (mem_id,))
    log = cursor.fetchone()
    
    assert log is not None
    assert 'Role: Tester' in log['old_value']
    assert 'Role: Senior Tester' in log['new_value']
    
    # 3. Test DELETE Trigger
    cursor.execute("DELETE FROM team_members WHERE mem_id = %s", (mem_id,))
    conn.commit()
    
    # Verify Audit Log for DELETE
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE table_name = 'team_members' AND operation_type = 'DELETE' AND record_id = %s
    """, (mem_id,))
    log = cursor.fetchone()
    
    assert log is not None
    assert 'Name: Trigger Test' in log['old_value']
    assert log['new_value'] is None
    
    cursor.close()
    conn.close()

def test_skill_triggers(client):
    """Test INSERT, UPDATE, DELETE triggers for skills table"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. INSERT
    cursor.execute("INSERT INTO skills (skill_name, category) VALUES ('Trigger Skill', 'Soft Skill')")
    conn.commit()
    skill_id = cursor.lastrowid
    
    # Verify INSERT Log
    cursor.execute("SELECT * FROM audit_logs WHERE table_name = 'skills' AND operation_type = 'INSERT' AND record_id = %s", (skill_id,))
    assert cursor.fetchone() is not None
    
    # 2. UPDATE
    cursor.execute("UPDATE skills SET skill_name = 'Updated Skill' WHERE skill_id = %s", (skill_id,))
    conn.commit()
    
    # Verify UPDATE Log
    cursor.execute("SELECT * FROM audit_logs WHERE table_name = 'skills' AND operation_type = 'UPDATE' AND record_id = %s", (skill_id,))
    log = cursor.fetchone()
    assert log is not None
    assert 'Skill: Trigger Skill' in log['old_value']
    assert 'Skill: Updated Skill' in log['new_value']
    
    # 3. DELETE
    cursor.execute("DELETE FROM skills WHERE skill_id = %s", (skill_id,))
    conn.commit()
    
    # Verify DELETE Log
    cursor.execute("SELECT * FROM audit_logs WHERE table_name = 'skills' AND operation_type = 'DELETE' AND record_id = %s", (skill_id,))
    log = cursor.fetchone()
    assert log is not None
    assert 'Skill: Updated Skill' in log['old_value']
    
    cursor.close()
    conn.close()

def test_mem_skill_triggers(client):
    """Test Mem_Skills triggers (proficiency changes)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Setup: Member + Skill
    cursor.execute("INSERT INTO team_members (full_name, email, role) VALUES ('MS User', 'ms@test.com', 'Dev')")
    mem_id = cursor.lastrowid
    cursor.execute("INSERT INTO skills (skill_name, category) VALUES ('MS Skill', 'Technical')")
    skill_id = cursor.lastrowid
    conn.commit()
    
    record_id = f"{mem_id}-{skill_id}"
    
    # 1. INSERT (Assignment)
    cursor.execute("INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES (%s, %s, %s)", (mem_id, skill_id, 3))
    conn.commit()
    
    cursor.execute("SELECT * FROM audit_logs WHERE table_name = 'mem_skills' AND operation_type = 'INSERT' AND record_id = %s", (record_id,))
    assert cursor.fetchone() is not None
    
    # 2. UPDATE (Proficiency Change)
    cursor.execute("UPDATE mem_skills SET proficiency_level = 5 WHERE mem_id = %s AND skill_id = %s", (mem_id, skill_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM audit_logs WHERE table_name = 'mem_skills' AND operation_type = 'UPDATE' AND record_id = %s", (record_id,))
    log = cursor.fetchone()
    assert log is not None
    assert 'Proficiency: 3' in log['old_value']
    assert 'Proficiency: 5' in log['new_value']
    
    # 3. DELETE
    cursor.execute("DELETE FROM mem_skills WHERE mem_id = %s AND skill_id = %s", (mem_id, skill_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM audit_logs WHERE table_name = 'mem_skills' AND operation_type = 'DELETE' AND record_id = %s", (record_id,))
    log = cursor.fetchone()
    assert log is not None
    assert 'Proficiency: 5' in log['old_value']
    
    cursor.close()
    conn.close()

def test_procedure_find_experts(client):
    """Test Stored Procedure: Find_Experts_For_Project"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Setup: 2 members with Java, different proficiency
    cursor.execute("INSERT INTO skills (skill_name, category) VALUES ('Java', 'Technical')")
    skill_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO team_members (full_name, email, role) VALUES ('Expert A', 'expert.a@test.com', 'Dev')")
    mem_a = cursor.lastrowid
    cursor.execute("INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES (%s, %s, 5)", (mem_a, skill_id))
    
    cursor.execute("INSERT INTO team_members (full_name, email, role) VALUES ('Expert B', 'expert.b@test.com', 'Junior')")
    mem_b = cursor.lastrowid
    cursor.execute("INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES (%s, %s, 3)", (mem_b, skill_id))
    
    conn.commit()
    
    # Call Procedure
    cursor.callproc('Find_Experts_For_Project', ('Java', 4)) # Min level 4
    
    # Fetch results
    results = []
    for result in cursor.stored_results():
        results = result.fetchall()
    
    # Expect only Expert A (Level 5 >= 4), Expert B is 3
    assert len(results) == 1
    assert results[0]['Team Member'] == 'Expert A'
    assert results[0]['Proficiency'] == 5
    
    cursor.close()
    conn.close()

def test_procedure_member_profile(client):
    """Test Stored Procedure: Get_Member_Profile"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Setup
    cursor.execute("INSERT INTO team_members (full_name, email, role) VALUES ('Profile User', 'profile@test.com', 'Lead')")
    mem_id = cursor.lastrowid
    cursor.execute("INSERT INTO skills (skill_name, category) VALUES ('Profile Skill', 'Technical')")
    skill_id = cursor.lastrowid
    cursor.execute("INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES (%s, %s, 4)", (mem_id, skill_id))
    conn.commit()
    
    # Call Procedure
    cursor.callproc('Get_Member_Profile', ('profile@test.com',))
    
    results = []
    for result in cursor.stored_results():
        results = result.fetchall()
        
    assert len(results) == 1
    row = results[0]
    assert row['full_name'] == 'Profile User'
    assert row['skill_name'] == 'Profile Skill'
    assert row['proficiency_level'] == 4
    
    cursor.close()
    conn.close()
