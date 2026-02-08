SET NAMES utf8mb4;
SET time_zone = '+09:00';

CREATE DATABASE IF NOT EXISTS course_registration
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE course_registration;

CREATE TABLE IF NOT EXISTS departments (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(16) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS professors (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  professor_no CHAR(8) NOT NULL UNIQUE,
  name VARCHAR(50) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  department_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_professors_department
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS students (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  student_no CHAR(10) NOT NULL UNIQUE,
  name VARCHAR(50) NOT NULL,
  department_id INT UNSIGNED NOT NULL,
  grade TINYINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT ck_students_grade CHECK (grade BETWEEN 1 AND 4),
  CONSTRAINT fk_students_department
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS courses (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  course_code CHAR(8) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  credits TINYINT UNSIGNED NOT NULL,
  capacity SMALLINT UNSIGNED NOT NULL,
  enrolled SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  schedule_day ENUM('MON', 'TUE', 'WED', 'THU', 'FRI') NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  department_id INT UNSIGNED NOT NULL,
  professor_id BIGINT UNSIGNED NOT NULL,
  semester VARCHAR(12) NOT NULL DEFAULT '2026-1',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT ck_courses_credits CHECK (credits BETWEEN 1 AND 3),
  CONSTRAINT ck_courses_capacity CHECK (capacity > 0),
  CONSTRAINT ck_courses_enrolled CHECK (enrolled <= capacity),
  CONSTRAINT ck_courses_time CHECK (start_time < end_time),
  CONSTRAINT fk_courses_department
    FOREIGN KEY (department_id) REFERENCES departments(id),
  CONSTRAINT fk_courses_professor
    FOREIGN KEY (professor_id) REFERENCES professors(id)
) ENGINE = InnoDB;

CREATE INDEX idx_courses_department ON courses(department_id);
CREATE INDEX idx_courses_professor ON courses(professor_id);
CREATE INDEX idx_courses_semester ON courses(semester);
CREATE INDEX idx_courses_schedule ON courses(schedule_day, start_time, end_time);

CREATE TABLE IF NOT EXISTS enrollments (
  student_id BIGINT UNSIGNED NOT NULL,
  course_id BIGINT UNSIGNED NOT NULL,
  enrolled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (student_id, course_id),
  CONSTRAINT fk_enrollments_student
    FOREIGN KEY (student_id) REFERENCES students(id),
  CONSTRAINT fk_enrollments_course
    FOREIGN KEY (course_id) REFERENCES courses(id)
) ENGINE = InnoDB;

CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
