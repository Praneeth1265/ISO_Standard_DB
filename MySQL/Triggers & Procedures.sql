-- TRIGGERS (9) --

DELIMITER //
-- INSERT MEM
CREATE TRIGGER after_member_insert
AFTER INSERT ON team_members
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('team_members', 'INSERT', NEW.mem_id, NULL, CONCAT('Name: ', NEW.full_name, ', Role: ', NEW.role), USER());
END //

DELIMITER ;

DELIMITER //
-- UPDATE MEM
CREATE TRIGGER after_member_update
AFTER UPDATE ON team_members
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('team_members', 'UPDATE', NEW.mem_id, 
            CONCAT('Name: ', OLD.full_name, ', Role: ', OLD.role), 
            CONCAT('Name: ', NEW.full_name, ', Role: ', NEW.role), USER());
END// 

DELIMITER ;

DELIMITER //
-- DLT MEM
CREATE TRIGGER after_member_delete
AFTER DELETE ON team_members
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, operation_type, record_id, old_value, new_value, changed_by)
    VALUES ('team_members', 'DELETE', OLD.mem_id, CONCAT('Name: ', OLD.full_name, ', Role: ', OLD.role), NULL, USER());
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


-- PROCEDURES -- 

DELIMITER //
-- EXPERTS
CREATE PROCEDURE Find_Experts_For_Project(
    IN p_selected_skill VARCHAR(50),  -- Input from the Skill Dropdown
    IN p_min_proficiency INT          -- Input from the Level Dropdown (e.g., 7)
)
BEGIN
    -- Select the necessary details joining all 3 tables
    SELECT 
        tm.full_name AS 'Team Member',
        tm.role AS 'Job Role',
        s.skill_name AS 'Skill',
        ms.proficiency_level AS 'Proficiency',
        tm.email AS 'Contact Email'
    FROM team_members tm
    JOIN mem_skills ms ON tm.mem_id = ms.mem_id
    JOIN skills s ON ms.skill_id = s.skill_id
    WHERE 
        s.skill_name = p_selected_skill  -- Matches the chosen skill
        AND ms.proficiency_level >= p_min_proficiency -- Filters for quality
    ORDER BY 
        ms.proficiency_level DESC; -- Shows best candidates first
END //

DELIMITER ;

DELIMITER //
-- MEM PROFILE
CREATE PROCEDURE Get_Member_Profile(
    IN p_member_email VARCHAR(100)
)
BEGIN
    SELECT 
        tm.full_name,
        tm.role,
        s.skill_name,
        s.category,
        ms.proficiency_level
    FROM team_members tm
    LEFT JOIN mem_skills ms ON tm.mem_id = ms.mem_id
    LEFT JOIN skills s ON ms.skill_id = s.skill_id
    WHERE tm.email = p_member_email;
END //

DELIMITER ;