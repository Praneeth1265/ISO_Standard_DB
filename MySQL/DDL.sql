CREATE DATABASE IF NOT EXISTS team_skills_db;
USE team_skills_db;
CREATE TABLE IF NOT EXISTS team_members (
    mem_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    INDEX (email)
);
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(50) UNIQUE NOT NULL,
    category ENUM('Technical', 'Clinical', 'Soft Skill', 'Regulatory') NOT NULL
);
CREATE TABLE IF NOT EXISTS mem_skills (
    mem_id INT,
    skill_id INT,
    proficiency_level INT CHECK (proficiency_level BETWEEN 1 AND 5),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (mem_id, skill_id),
    FOREIGN KEY (mem_id) REFERENCES team_members(mem_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,       -- Which table changed? (e.g., 'team_members')
    operation_type VARCHAR(20) NOT NULL,   -- 'INSERT', 'UPDATE', 'DELETE'
    record_id VARCHAR(50),                 -- The ID of the row (stored as string to handle composite keys)
    old_value TEXT,                        -- What was there before (NULL for Inserts)
    new_value TEXT,                        -- What is there now (NULL for Deletes)
    changed_by VARCHAR(50),                -- Who did it (System User)
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill Catalog: Categorized for Medical Sector
INSERT IGNORE INTO skills (skill_name, category) VALUES 
('Python (Data Science)', 'Technical'),
('MySQL Database Design', 'Technical'),
('Streamlit UI Development', 'Technical'),
('Git & Version Control', 'Technical'),
('ISO 13485 Compliance', 'Regulatory'),
('IEC 62304 (Life Cycle)', 'Regulatory'),
('ISO 14971 (Risk Management)', 'Regulatory'),
('FDA Software Validation', 'Regulatory'),
('Clinical Data Analysis', 'Clinical'),
('HIPAA/GDPR Data Privacy', 'Clinical'),
('Technical Writing', 'Soft Skill'),
('Agile Methodology', 'Soft Skill');

-- Your Team Members
INSERT IGNORE INTO team_members (full_name, email, role) VALUES 
('Praneeth', 'praneeth@startup.com', 'Software Intern'),
('Gagan', 'gagan@startup.com', 'Data Analyst Intern'),
('Kashyap', 'kashyap@startup.com', 'QA & Testing Intern'),
('Govind', 'govind@startup.com', 'Backend Intern'),
('Hardik', 'hardik@startup.com', 'Regulatory Intern');

-- Sample Skill Assignments
-- Note: IDs are 1-5 based on the order of the inserts above
INSERT IGNORE INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES 
-- Intern 1 Skills
(1, 1, 4), -- Python
(1, 2, 5), -- MySQL
(1, 5, 3), -- ISO 13485
-- Intern 2 Skills
(2, 1, 5), -- Python
(2, 9, 4), -- Clinical Data
(2, 10, 4), -- Privacy
-- Intern 3 Skills
(3, 3, 5), -- Streamlit
(3, 4, 4), -- Git
(3, 6, 3), -- IEC 62304
-- Intern 4 Skills
(4, 2, 4), -- MySQL
(4, 7, 3), -- Risk Mgmt
(4, 11, 4), -- Tech Writing
-- Intern 5 Skills
(5, 5, 5), -- ISO 13485 (Expert)
(5, 8, 4), -- FDA Validation
(5, 12, 5); -- Agile
