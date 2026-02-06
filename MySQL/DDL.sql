CREATE DATABASE IF NOT EXISTS team_skills_db;
USE team_skills_db;
CREATE TABLE IF NOT EXISTS roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
CREATE TABLE IF NOT EXISTS team_members (
    mem_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_no VARCHAR(15) UNIQUE NOT NULL,
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE SET NULL,
    INDEX (email)
);
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(50) UNIQUE NOT NULL,
    category ENUM('Technical', 'Clinical', 'Soft Skill', 'Regulatory') NOT NULL
);
CREATE TABLE IF NOT EXISTS role_requirements (
    role_id INT,
    skill_id INT,
    min_proficiency_required INT DEFAULT 2,
    PRIMARY KEY (role_id, skill_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS mem_skills (
    mem_id INT,
    skill_id INT,
    proficiency_level INT CHECK (proficiency_level BETWEEN 1 AND 3),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (mem_id, skill_id),
    FOREIGN KEY (mem_id) REFERENCES team_members(mem_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL,
    record_id VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(50),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample Data
INSERT INTO skills (skill_name, category) VALUES 
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

INSERT INTO team_members (first_name, middle_name, last_name, email, phone_no, role_id) VALUES 
('Praneeth', '', 'Kumar', 'praneeth@startup.com', '9900112233', 1),
('Gagan', 'S.', 'Reddy', 'gagan@startup.com', '9900112244', 2),
('Kashyap', '', 'Sharma', 'kashyap@startup.com', '9900112255', 3),
('Govind', 'V.', 'Nair', 'govind@startup.com', '9900112266', 4),
('Hardik', '', 'Pandya', 'hardik@startup.com', '9900112277', 5);

INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES 
(1, 1, 4), (1, 2, 5), (1, 5, 3),
(2, 1, 5), (2, 9, 4), (2, 10, 4),
(3, 3, 5), (3, 4, 4), (3, 6, 3),
(4, 2, 4), (4, 7, 3), (4, 11, 4),
(5, 5, 5), (5, 8, 4), (5, 12, 5);

INSERT INTO roles (role_name, description) VALUES 
('Senior Backend Developer', 'Expert in data architecture and secure server logic.'),
('Software Quality Lead', 'Responsible for software verification and validation (V&V).'),
('Medical Data Scientist', 'Analyzes clinical datasets using ML while ensuring privacy.'),
('Regulatory Affairs Head', 'Oversees all global medical certifications and risk mgmt.');


-- Role 1 (Backend Intern): Requires Python(1) and MySQL(2)
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(1, 1, 2), (1, 2, 3);

-- Role 6 (Senior Backend Dev): Needs high Tech + basic Git
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(6, 1, 4), -- Python Level 4
(6, 2, 5), -- MySQL Level 5
(6, 4, 3); -- Git Level 3

-- Role 7 (Software Quality Lead): Needs Regulatory + Tech Writing
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(7, 6, 4), -- IEC 62304 (Life Cycle) Level 4
(7, 8, 4), -- FDA Validation Level 4
(1, 11, 4); -- Technical Writing Level 4

-- Role 8 (Medical Data Scientist): Needs Technical + Clinical + Regulatory
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(8, 1, 5), -- Python (Data Science) Level 5
(8, 9, 4), -- Clinical Data Analysis Level 4
(8, 10, 5); -- HIPAA/GDPR Privacy Level 5

-- Role 9 (Regulatory Affairs Head): The "Master" Role
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(9, 5, 5), -- ISO 13485 Compliance Level 5
(9, 7, 5), -- ISO 14971 Risk Mgmt Level 5
(9, 11, 5); -- Technical Writing Level 5