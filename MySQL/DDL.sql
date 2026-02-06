DROP DATABASE IF EXISTS team_skills_db;
CREATE DATABASE team_skills_db;
USE team_skills_db;

-- Roles Table
CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Team Members Table
CREATE TABLE team_members (
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

-- Skills Table
CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(50) UNIQUE NOT NULL,
    category ENUM('Technical', 'Clinical', 'Soft Skill', 'Regulatory') NOT NULL
);

-- Role Requirements (Scale 1-3)
CREATE TABLE role_requirements (
    role_id INT,
    skill_id INT,
    min_proficiency_required INT DEFAULT 1 CHECK (min_proficiency_required BETWEEN 1 AND 3),
    PRIMARY KEY (role_id, skill_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

-- Member Skills (Scale 1-3)
CREATE TABLE mem_skills (
    mem_id INT,
    skill_id INT,
    proficiency_level INT CHECK (proficiency_level BETWEEN 1 AND 3),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (mem_id, skill_id),
    FOREIGN KEY (mem_id) REFERENCES team_members(mem_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

-- Audit Logs
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL,
    record_id VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(50),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO roles (role_name, description) VALUES 
('Software Intern', 'Entry level developer.'), -- ID 1
('Data Analyst Intern', 'Clinical data support.'), -- ID 2
('QA & Testing Intern', 'Validation support.'), -- ID 3
('Backend Intern', 'Database support.'), -- ID 4
('Regulatory Intern', 'Compliance support.'), -- ID 5
('Senior Backend Developer', 'Lead architect.'), -- ID 6
('Software Quality Lead', 'V&V Specialist.'), -- ID 7
('Medical Data Scientist', 'ML & HIPAA expert.'), -- ID 8
('Regulatory Affairs Head', 'Chief Compliance Officer.'); -- ID 9

INSERT INTO skills (skill_name, category) VALUES 
('Python (Data Science)', 'Technical'), -- 1
('MySQL Database Design', 'Technical'), -- 2
('Streamlit UI Development', 'Technical'), -- 3
('Git & Version Control', 'Technical'), -- 4
('ISO 13485 Compliance', 'Regulatory'), -- 5
('IEC 62304 (Life Cycle)', 'Regulatory'), -- 6
('ISO 14971 (Risk Management)', 'Regulatory'), -- 7
('FDA Software Validation', 'Regulatory'), -- 8
('Clinical Data Analysis', 'Clinical'), -- 9
('HIPAA/GDPR Data Privacy', 'Clinical'), -- 10
('Technical Writing', 'Soft Skill'), -- 11
('Agile Methodology', 'Soft Skill'); -- 12

INSERT INTO team_members (first_name, middle_name, last_name, email, phone_no, role_id) VALUES 
('Praneeth', '', 'Kumar', 'praneeth@gmail.com', '9900112233', 1), -- mem 1
('Gagan', 'S.', 'Reddy', 'gagan@gmail.com', '9900112244', 2), -- mem 2
('Kashyap', '', 'Sharma', 'kashyap@gmail.com', '9900112255', 3), -- mem 3
('Govind', 'V.', 'Nair', 'govind@gmail.com', '9900112266', 4), -- mem 4
('Hardik', '', 'Pandya', 'hardik@gmail.com', '9900112277', 5); -- mem 5

-- Software Intern (Role 1): Python(1) Lvl 1, MySQL(2) Lvl 1
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(1, 1, 1), (1, 2, 1);

-- Senior Backend (Role 6): Python(1) Lvl 3, MySQL(2) Lvl 3, Git(4) Lvl 2
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(6, 1, 3), (6, 2, 3), (6, 4, 2);

-- Software Quality Lead (Role 7): IEC 62304(6) Lvl 3, FDA(8) Lvl 3
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(7, 6, 3), (7, 8, 3);

-- Regulatory Affairs Head (Role 9): ISO 13485(5) Lvl 3, ISO 14971(7) Lvl 3
INSERT INTO role_requirements (role_id, skill_id, min_proficiency_required) VALUES 
(9, 5, 3), (9, 7, 3), (9, 11, 3);

INSERT INTO mem_skills (mem_id, skill_id, proficiency_level) VALUES 
-- Praneeth
(1, 1, 3), (1, 2, 3), (1, 5, 2),
-- Gagan
(2, 1, 3), (2, 9, 3), (2, 10, 2),
-- Kashyap
(3, 3, 3), (3, 4, 3), (3, 6, 2),
-- Govind
(4, 2, 3), (4, 7, 2), (4, 11, 3),
-- Hardik
(5, 5, 3), (5, 8, 3), (5, 12, 3);