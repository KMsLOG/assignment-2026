"""Runtime dataset generation logic for development and evaluation."""

from __future__ import annotations

from collections import defaultdict
from datetime import time

from sqlalchemy import func, insert, select, text
from sqlalchemy.orm import Session

from app.repository.models import Course, Department, Professor, Student

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
    (time(9, 0), time(10, 30)),
    (time(10, 30), time(12, 0)),
    (time(13, 0), time(14, 30)),
    (time(14, 30), time(16, 0)),
    (time(16, 0), time(17, 30)),
    (time(18, 30), time(20, 0)),
]


def _name_for(index: int, m1: int, m2: int) -> str:
    """Generate a deterministic Korean-style full name from token tables."""
    family = LAST_NAMES[index % len(LAST_NAMES)]
    first = GIVEN_NAME_SYLLABLES[(index * m1) % len(GIVEN_NAME_SYLLABLES)]
    second = GIVEN_NAME_SYLLABLES[(index * m2 + 7) % len(GIVEN_NAME_SYLLABLES)]
    return f"{family}{first}{second}"


def _table_counts(db: Session) -> dict[str, int]:
    """Return current row counts for core domain tables."""
    counts = {
        "departments": db.scalar(select(func.count()).select_from(Department)) or 0,
        "professors": db.scalar(select(func.count()).select_from(Professor)) or 0,
        "courses": db.scalar(select(func.count()).select_from(Course)) or 0,
        "students": db.scalar(select(func.count()).select_from(Student)) or 0,
    }
    return {k: int(v) for k, v in counts.items()}


def _needs_seed(counts: dict[str, int]) -> bool:
    """Return True when any table is below the required minimum count."""
    return any(counts[table] < min_count for table, min_count in MIN_COUNTS.items())


def seed_runtime_data(db: Session) -> dict[str, object]:
    """Populate minimum viable data set when DB is empty or undersized."""
    current_counts = _table_counts(db)
    if not _needs_seed(current_counts):
        db.rollback()
        return {"seeded": False, "counts": current_counts}

    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        db.execute(text("DELETE FROM enrollments"))
        db.execute(text("DELETE FROM courses"))
        db.execute(text("DELETE FROM students"))
        db.execute(text("DELETE FROM professors"))
        db.execute(text("DELETE FROM departments"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        db.execute(
            insert(Department),
            [{"code": code, "name": name} for code, name in DEPARTMENTS],
        )
        department_ids = list(db.scalars(select(Department.id).order_by(Department.id)))

        professor_rows: list[dict[str, object]] = []
        for i in range(120):
            professor_rows.append(
                {
                    "professor_no": f"PF{i + 1:06d}",
                    "name": _name_for(i, 7, 13),
                    "email": f"prof{i + 1:04d}@univ.ac.kr",
                    "department_id": department_ids[i % len(department_ids)],
                }
            )
        db.execute(insert(Professor), professor_rows)

        student_rows: list[dict[str, object]] = []
        for i in range(10000):
            student_rows.append(
                {
                    "student_no": f"2026{i + 1:06d}",
                    "name": _name_for(i, 5, 11),
                    "department_id": department_ids[i % len(department_ids)],
                    "grade": (i % 4) + 1,
                }
            )
        db.execute(insert(Student), student_rows)

        professors = db.execute(select(Professor.id, Professor.department_id).order_by(Professor.id)).all()
        professors_by_department: dict[int, list[int]] = defaultdict(list)
        for professor_id, department_id in professors:
            professors_by_department[int(department_id)].append(int(professor_id))

        course_rows: list[dict[str, object]] = []
        for i in range(600):
            department_id = department_ids[i % len(department_ids)]
            professors_for_dept = professors_by_department[department_id]
            professor_id = professors_for_dept[(i // len(department_ids)) % len(professors_for_dept)]
            title = COURSE_TITLES[i % len(COURSE_TITLES)]
            section = (i // len(COURSE_TITLES)) + 1
            start_time, end_time = TIME_SLOTS[i % len(TIME_SLOTS)]

            course_rows.append(
                {
                    "course_code": f"CR{i + 1:06d}",
                    "name": f"{title} {section:02d}분반",
                    "credits": (i % 3) + 1,
                    "capacity": 20 + (i % 41),
                    "enrolled": 0,
                    "schedule_day": SCHEDULE_DAYS[i % len(SCHEDULE_DAYS)],
                    "start_time": start_time,
                    "end_time": end_time,
                    "department_id": department_id,
                    "professor_id": professor_id,
                    "semester": "2026-1",
                }
            )
        db.execute(insert(Course), course_rows)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"seeded": True, "counts": _table_counts(db)}
