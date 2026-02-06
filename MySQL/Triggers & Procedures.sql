-- TRIGGERS (9) --

DELIMITER //

-- INSERT MEMBER
CREATE TRIGGER after_member_insert
AFTER INSERT ON team_members
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('team_members', 'INSERT', NEW.mem_id, NULL, 
            CONCAT('Name: ', NEW.first_name, ' ', NEW.last_name, ', RoleID: ', IFNULL(NEW.role_id, 'None'), ', Phone: ', NEW.phone_no), USER());
END //

DELIMITER ;

DELIMITER //
-- UPDATE MEMBER
CREATE TRIGGER after_member_update
AFTER UPDATE ON team_members
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('team_members', 'UPDATE', NEW.mem_id, 
            CONCAT('Name: ', OLD.first_name, ' ', OLD.last_name, ', RoleID: ', IFNULL(OLD.role_id, 'None')), 
            CONCAT('Name: ', NEW.first_name, ' ', NEW.last_name, ', RoleID: ', IFNULL(NEW.role_id, 'None')), USER());
END //

DELIMITER ;

DELIMITER //
-- DELETE MEMBER
CREATE TRIGGER after_member_delete
AFTER DELETE ON team_members
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('team_members', 'DELETE', OLD.mem_id, 
            CONCAT('Name: ', OLD.first_name, ' ', OLD.last_name, ', Email: ', OLD.email), NULL, USER());
END //

DELIMITER ;

DELIMITER //
-- INSERT SKILL
CREATE TRIGGER after_skill_insert
AFTER INSERT ON skills
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('skills', 'INSERT', NEW.skill_id, NULL, CONCAT('Skill: ', NEW.skill_name), USER());
END //

DELIMITER ;

DELIMITER //
-- UPDATE SKILL
CREATE TRIGGER after_skill_update_master
AFTER UPDATE ON skills
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('skills', 'UPDATE', NEW.skill_id, 
            CONCAT('Skill: ', OLD.skill_name), 
            CONCAT('Skill: ', NEW.skill_name), USER());
END//

DELIMITER ;

DELIMITER //
-- DLT SKILL
CREATE TRIGGER after_skill_delete
AFTER DELETE ON skills
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('skills', 'DELETE', OLD.skill_id, CONCAT('Skill: ', OLD.skill_name), NULL, USER());
END//

DELIMITER ;

DELIMITER //
-- INSERT MEM_SKILL
CREATE TRIGGER after_memskill_insert
AFTER INSERT ON mem_skills
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('mem_skills', 'INSERT', CONCAT(NEW.mem_id, '-', NEW.skill_id), 
            NULL, 
            CONCAT('Proficiency: ', NEW.proficiency_level), USER());
END//

DELIMITER ;

DELIMITER //
-- UPDATE MEM_SKILL
CREATE TRIGGER after_memskill_update
AFTER UPDATE ON mem_skills
FOR EACH ROW
BEGIN
    -- Only log if the level actually changed
    IF OLD.proficiency_level <> NEW.proficiency_level THEN
        INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
        VALUES ('mem_skills', 'UPDATE', CONCAT(NEW.mem_id, '-', NEW.skill_id), 
                CONCAT('Proficiency: ', OLD.proficiency_level), 
                CONCAT('Proficiency: ', NEW.proficiency_level), USER());
    END IF;
END//

DELIMITER ;

DELIMITER //
-- DLT MEM_SKILL
CREATE TRIGGER after_memskill_delete
AFTER DELETE ON mem_skills
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('mem_skills', 'DELETE', CONCAT(OLD.mem_id, '-', OLD.skill_id), 
            CONCAT('Proficiency: ', OLD.proficiency_level), NULL, USER());
END //
DELIMITER ;

DELIMITER //

-- INSERT ROLE
CREATE TRIGGER after_role_insert
AFTER INSERT ON roles
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('roles', 'INSERT', NEW.role_id, NULL, 
            CONCAT('Role: ', NEW.role_name), USER());
END //
DELIMITER ;

DELIMITER //
-- UPDATE ROLE
CREATE TRIGGER after_role_update
AFTER UPDATE ON roles
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('roles', 'UPDATE', NEW.role_id, 
            CONCAT('Role: ', OLD.role_name), 
            CONCAT('Role: ', NEW.role_name), USER());
END //
DELIMITER ;

DELIMITER //
-- DELETE ROLE
CREATE TRIGGER after_role_delete
AFTER DELETE ON roles
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('roles', 'DELETE', OLD.role_id, 
            CONCAT('Role: ', OLD.role_name), NULL, USER());
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER validate_role_eligibility
BEFORE UPDATE ON team_members
FOR EACH ROW
BEGIN
    DECLARE missing_skills INT;

    -- Check if the new role has requirements the user doesn't meet
    SELECT COUNT(*) INTO missing_skills
    FROM role_requirements rr
    LEFT JOIN mem_skills ms ON rr.skill_id = ms.skill_id AND ms.mem_id = NEW.mem_id
    WHERE rr.role_id = NEW.role_id
    AND (ms.skill_id IS NULL OR ms.proficiency_level < rr.min_proficiency_required);

    -- If there are missing or insufficient skills, block the update
    IF missing_skills > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ineligible for Role: Member does not meet the minimum skill requirements for this role.';
    END IF;
END //

DELIMITER ;

-- PROCEDURES -- 
DELIMITER //

-- 1. Find Experts
CREATE PROCEDURE Find_Experts_For_Project(
    IN p_selected_skill VARCHAR(50),
    IN p_min_proficiency INT
)
BEGIN
    SELECT 
        CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS 'Team Member',
        r.role_name AS 'Job Role',
        s.skill_name AS 'Skill',
        ms.proficiency_level AS 'Proficiency',
        tm.email AS 'Contact Email',
        tm.phone_no AS 'Phone'
    FROM team_members tm
    LEFT JOIN roles r ON tm.role_id = r.role_id
    JOIN mem_skills ms ON tm.mem_id = ms.mem_id
    JOIN skills s ON ms.skill_id = s.skill_id
    WHERE 
        s.skill_name = p_selected_skill 
        AND ms.proficiency_level >= p_min_proficiency
    ORDER BY ms.proficiency_level DESC;
END //
DELIMITER ;

DELIMITER //
-- 2. Member Profile
CREATE PROCEDURE Get_Member_Profile(
    IN p_member_email VARCHAR(100)
)
BEGIN
    SELECT 
        CONCAT_WS(' ', tm.first_name, NULLIF(tm.middle_name, ''), tm.last_name) AS full_name,
        tm.phone_no,
        r.role_name,
        s.skill_name,
        s.category,
        ms.proficiency_level,
        ms.updated_at
    FROM team_members tm
    LEFT JOIN roles r ON tm.role_id = r.role_id
    LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
    LEFT JOIN skills s ON ms.skill_id = s.skill_id
    WHERE tm.email = p_member_email;
END //

DELIMITER ;

DELIMITER //
-- 3. Check Eligibility
CREATE PROCEDURE Get_Eligible_Roles_For_Member(IN p_mem_id INT)
BEGIN
    SELECT r.role_id, r.role_name
    FROM roles r
    WHERE NOT EXISTS (
        SELECT 1 
        FROM role_requirements rr
        LEFT JOIN mem_skills ms ON rr.skill_id = ms.skill_id AND ms.mem_id = p_mem_id
        WHERE rr.role_id = r.role_id
        AND (ms.skill_id IS NULL OR ms.proficiency_level < rr.min_proficiency_required)
    );
END //
DELIMITER ;