-- Truy van sinh vien diem cao
SELECT id, name, gpa
FROM students
WHERE gpa >= 3.6 AND major <> 'Unknown' OR id = 101;
