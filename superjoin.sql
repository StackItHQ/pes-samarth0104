create database superzz;
use superzz;
CREATE TABLE internships (
    id INT PRIMARY KEY,
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    cgpa_cutoff FLOAT,
    remarks VARCHAR(255)
);

Select * from internships;
INSERT INTO internships (id, company_name, job_title, cgpa_cutoff, remarks)
VALUES (15, 'Google', 'Software Engineer', 9, 'Excellent opportunity');
DELETE FROM internships
WHERE id = 10;
