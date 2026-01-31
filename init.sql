CREATE DATABASE IF NOT EXISTS team_talent_db;
USE team_talent_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    INDEX (email)
);

-- 2. Skills Catalog (Master List)
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(50) UNIQUE NOT NULL,
    category ENUM('Technical', 'Clinical', 'Soft Skill', 'Regulatory') NOT NULL
);

-- 3. User-Skills (Mapping Table)
CREATE TABLE IF NOT EXISTS user_skills (
    user_id INT,
    skill_id INT,
    proficiency_level INT CHECK (proficiency_level BETWEEN 1 AND 5),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, skill_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

-- 4. Audit Log (The Medical "Must-Have")
-- Tracks every time a skill is changed for compliance
CREATE TABLE IF NOT EXISTS skill_audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    skill_id INT,
    old_level INT,
    new_level INT,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Data (For your demo)
INSERT IGNORE INTO skills (skill_name, category) VALUES 
('Python', 'Technical'), ('MySQL', 'Technical'), 
('ISO 13485', 'Regulatory'), ('Risk Analysis', 'Regulatory'),
('Project Management', 'Soft Skill');

INSERT IGNORE INTO users (full_name, email, role) VALUES 
('Your Name', 'your.email@startup.com', 'Intern'),
('Team Member 1', 'tm1@startup.com', 'Developer');