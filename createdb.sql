CREATE DATABASE irmtestdb;

\c irmtestdb

CREATE TABLE teacher (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE student (
    id SERIAL PRIMARY KEY,
	student_name TEXT,
    teacher_id INT REFERENCES teacher(id),
    course TEXT
);

