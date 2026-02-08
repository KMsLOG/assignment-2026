from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from pymysql.connections import Connection

MIN_COUNTS = {
    "departments": 10,
    "professors": 100,
    "courses": 500,
    "students": 10000,
}

DEPARTMENTS = [
    ("CSE", "컴퓨터공학과"),
    ("ECE", "전자공학과"),
    ("MEC", "기계공학과"),
    ("MAT", "수학과"),
    ("PHY", "물리학과"),
    ("CHE", "화학과"),
    ("BIO", "생명과학과"),
    ("ECO", "경제학과"),
    ("BUS", "경영학과"),
    ("LIT", "국어국문학과"),
    ("SOC", "사회학과"),
    ("PSY", "심리학과"),
]

LAST_NAMES = [
    "김",
    "이",
    "박",
    "최",
    "정",
    "강",
    "조",
    "윤",
    "장",
    "임",
    "한",
    "오",
    "서",
    "신",
    "권",
    "황",
    "안",
    "송",
    "전",
    "홍",
]

GIVEN_NAME_SYLLABLES = [
    "민",
    "준",
    "서",
    "연",
    "지",
    "우",
    "하",
    "윤",
    "현",
    "수",
    "도",
    "경",
    "나",
    "영",
    "진",
    "채",
    "은",
    "태",
    "호",
    "린",
    "선",
    "아",
    "율",
    "건",
    "빈",
    "혁",
    "원",
    "솔",
    "훈",
]

COURSE_TITLES = [
    "자료구조",
    "알고리즘",
    "운영체제",
    "데이터베이스",
    "컴퓨터네트워크",
    "소프트웨어공학",
    "웹프로그래밍",
    "인공지능개론",
    "머신러닝기초",
    "딥러닝응용",
    "확률과통계",
    "선형대수",
    "공학수학",
    "전자회로",
    "디지털논리설계",
    "신호및시스템",
    "유체역학",
    "열역학",
    "고체역학",
    "일반물리학",
    "유기화학",
    "분석화학",
    "세포생물학",
    "미시경제학",
    "거시경제학",
    "회계원리",
    "마케팅원론",
    "조직행동론",
    "국어학개론",
    "문학비평입문",
    "사회조사방법론",
    "사회심리학",
    "인지심리학",
    "발달심리학",
    "통계프로그래밍",
    "클라우드컴퓨팅",
    "정보보호개론",
    "컴파일러구성",
    "분산시스템",
    "모바일애플리케이션",
]

SCHEDULE_DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
TIME_SLOTS = [
    ("09:00:00", "10:30:00"),
    ("10:30:00", "12:00:00"),
    ("13:00:00", "14:30:00"),
    ("14:30:00", "16:00:00"),
    ("16:00:00", "17:30:00"),
    ("18:30:00", "20:00:00"),
]


def _chunks(rows: list[tuple], size: int) -> Iterable[list[tuple]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _name_for(index: int, m1: int, m2: int) -> str:
    family = LAST_NAMES[index % len(LAST_NAMES)]
    first = GIVEN_NAME_SYLLABLES[(index * m1) % len(GIVEN_NAME_SYLLABLES)]
    second = GIVEN_NAME_SYLLABLES[(index * m2 + 7) % len(GIVEN_NAME_SYLLABLES)]
    return f"{family}{first}{second}"


def _table_counts(conn: Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in MIN_COUNTS:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = int(cur.fetchone()[0])
    return counts


def _needs_seed(counts: dict[str, int]) -> bool:
    for table, minimum in MIN_COUNTS.items():
        if counts.get(table, 0) < minimum:
            return True
    return False


def _seed_departments(conn: Connection) -> list[int]:
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO departments (code, name) VALUES (%s, %s)",
            DEPARTMENTS,
        )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM departments ORDER BY id")
        return [int(row[0]) for row in cur.fetchall()]


def _seed_professors(conn: Connection, department_ids: list[int]) -> dict[int, list[int]]:
    rows: list[tuple[str, str, str, int]] = []
    total = 120

    for i in range(total):
        professor_no = f"PF{i + 1:06d}"
        name = _name_for(i, 7, 13)
        email = f"prof{i + 1:04d}@univ.ac.kr"
        department_id = department_ids[i % len(department_ids)]
        rows.append((professor_no, name, email, department_id))

    with conn.cursor() as cur:
        for chunk in _chunks(rows, 1000):
            cur.executemany(
                "INSERT INTO professors (professor_no, name, email, department_id) "
                "VALUES (%s, %s, %s, %s)",
                chunk,
            )
    conn.commit()

    professors_by_department: dict[int, list[int]] = defaultdict(list)
    with conn.cursor() as cur:
        cur.execute("SELECT id, department_id FROM professors ORDER BY id")
        for professor_id, department_id in cur.fetchall():
            professors_by_department[int(department_id)].append(int(professor_id))
    return professors_by_department


def _seed_students(conn: Connection, department_ids: list[int]) -> None:
    rows: list[tuple[str, str, int, int]] = []
    total = 10000

    for i in range(total):
        student_no = f"2026{i + 1:06d}"
        name = _name_for(i, 5, 11)
        department_id = department_ids[i % len(department_ids)]
        grade = (i % 4) + 1
        rows.append((student_no, name, department_id, grade))

    with conn.cursor() as cur:
        for chunk in _chunks(rows, 1000):
            cur.executemany(
                "INSERT INTO students (student_no, name, department_id, grade) "
                "VALUES (%s, %s, %s, %s)",
                chunk,
            )
    conn.commit()


def _seed_courses(
    conn: Connection,
    department_ids: list[int],
    professors_by_department: dict[int, list[int]],
) -> None:
    rows: list[tuple[str, str, int, int, int, str, str, str, int, int, str]] = []
    total = 600

    for i in range(total):
        department_id = department_ids[i % len(department_ids)]
        professors = professors_by_department[department_id]
        professor_id = professors[(i // len(department_ids)) % len(professors)]

        title = COURSE_TITLES[i % len(COURSE_TITLES)]
        section = (i // len(COURSE_TITLES)) + 1
        name = f"{title} {section:02d}분반"
        course_code = f"CR{i + 1:06d}"
        credits = (i % 3) + 1
        capacity = 20 + (i % 41)
        schedule_day = SCHEDULE_DAYS[i % len(SCHEDULE_DAYS)]
        start_time, end_time = TIME_SLOTS[i % len(TIME_SLOTS)]

        rows.append(
            (
                course_code,
                name,
                credits,
                capacity,
                0,
                schedule_day,
                start_time,
                end_time,
                department_id,
                professor_id,
                "2026-1",
            )
        )

    with conn.cursor() as cur:
        for chunk in _chunks(rows, 1000):
            cur.executemany(
                "INSERT INTO courses ("
                "course_code, name, credits, capacity, enrolled, "
                "schedule_day, start_time, end_time, department_id, professor_id, semester"
                ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                chunk,
            )
    conn.commit()


def seed_runtime_data(conn: Connection) -> dict[str, object]:
    current_counts = _table_counts(conn)
    if not _needs_seed(current_counts):
        return {"seeded": False, "counts": current_counts}

    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("DELETE FROM enrollments")
        cur.execute("DELETE FROM courses")
        cur.execute("DELETE FROM students")
        cur.execute("DELETE FROM professors")
        cur.execute("DELETE FROM departments")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    department_ids = _seed_departments(conn)
    professors_by_department = _seed_professors(conn, department_ids)
    _seed_students(conn, department_ids)
    _seed_courses(conn, department_ids, professors_by_department)

    return {"seeded": True, "counts": _table_counts(conn)}
