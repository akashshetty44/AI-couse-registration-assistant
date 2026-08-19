from database import (
    get_course,
    get_prerequisites,
    get_completed_courses,
    get_registered_courses,
    course_exists_in_registration
)


GRADE_VALUES = {
    "A+": 10,
    "A": 9,
    "B+": 8,
    "B": 7,
    "C+": 6,
    "C": 5,
    "D": 4,
    "F": 0
}


def grade_meets_requirement(
    student_grade,
    minimum_grade
):

    return (
        GRADE_VALUES.get(
            student_grade,
            0
        )
        >=
        GRADE_VALUES.get(
            minimum_grade,
            0
        )
    )


def check_prerequisites(
    student_id,
    course_code
):

    prerequisites = get_prerequisites(
        course_code
    )

    completed = {
        item["course_code"]:
        item["grade"]

        for item in
        get_completed_courses(
            student_id
        )
    }

    missing = []
    satisfied = []

    for prerequisite in prerequisites:

        code = prerequisite[
            "prerequisite_code"
        ]

        minimum_grade = prerequisite[
            "minimum_grade"
        ]

        if code not in completed:

            missing.append(
                {
                    "course_code": code,
                    "course_name":
                        prerequisite["course_name"],
                    "reason":
                        "Course not completed"
                }
            )

        elif not grade_meets_requirement(
            completed[code],
            minimum_grade
        ):

            missing.append(
                {
                    "course_code": code,
                    "course_name":
                        prerequisite["course_name"],
                    "reason":
                        f"Minimum grade "
                        f"{minimum_grade} required, "
                        f"but student received "
                        f"{completed[code]}"
                }
            )

        else:

            satisfied.append(
                {
                    "course_code": code,
                    "course_name":
                        prerequisite["course_name"],
                    "grade":
                        completed[code]
                }
            )

    return missing, satisfied


def check_timetable_conflict(
    student_id,
    course_code
):

    target_course = get_course(
        course_code
    )

    if not target_course:

        return False, "Course not found."

    target_days = {
        day.strip()
        for day in
        target_course["days"].split(",")
    }

    for registered_course in get_registered_courses(
        student_id
    ):

        registered_days = {
            day.strip()
            for day in
            registered_course["days"].split(",")
        }

        common_days = (
            target_days
            .intersection(
                registered_days
            )
        )

        if (
            common_days
            and
            target_course["start_time"]
            <
            registered_course["end_time"]
            and
            registered_course["start_time"]
            <
            target_course["end_time"]
        ):

            return (
                True,
                f"Timetable conflict with "
                f"{registered_course['course_code']} - "
                f"{registered_course['course_name']} "
                f"on {', '.join(common_days)}."
            )

    return False, ""


def check_eligibility(
    student,
    course_code
):

    course = get_course(
        course_code
    )

    if not course:

        return {
            "eligible": False,
            "reasons": [
                "Course does not exist."
            ],
            "warnings": [],
            "satisfied_prerequisites": [],
            "missing_prerequisites": [],
            "current_credits": 0,
            "new_total_credits": 0
        }

    reasons = []
    warnings = []

    # Already registered
    if course_exists_in_registration(
        student["student_id"],
        course_code
    ):

        reasons.append(
            "You are already registered for this course."
        )

    # Already completed
    completed = get_completed_courses(
        student["student_id"]
    )

    completed_codes = {
        item["course_code"]
        for item in completed
    }

    if course_code in completed_codes:

        reasons.append(
            "You have already completed this course."
        )

    # Semester warning
    if course["semester"] > student["semester"]:

        warnings.append(
            f"This course is normally offered "
            f"for semester {course['semester']}, "
            f"while you are in semester "
            f"{student['semester']}."
        )

    # Prerequisites
    missing, satisfied = check_prerequisites(
        student["student_id"],
        course_code
    )

    for item in missing:

        reasons.append(
            f"Missing prerequisite: "
            f"{item['course_code']} - "
            f"{item['course_name']} "
            f"({item['reason']})"
        )

    # Capacity
    if course["enrolled"] >= course["capacity"]:

        reasons.append(
            "The course is currently full."
        )

    # Timetable
    conflict, message = check_timetable_conflict(
        student["student_id"],
        course_code
    )

    if conflict:

        reasons.append(message)

    # Credit limit
    current_credits = sum(
        item["credits"]
        for item in get_registered_courses(
            student["student_id"]
        )
    )

    new_total = (
        current_credits
        + course["credits"]
    )

    if new_total > student["max_credits"]:

        reasons.append(
            f"Credit limit exceeded. "
            f"Current: {current_credits}, "
            f"course: {course['credits']}, "
            f"maximum: {student['max_credits']}."
        )

    return {
        "eligible":
            len(reasons) == 0,

        "reasons":
            reasons,

        "warnings":
            warnings,

        "satisfied_prerequisites":
            satisfied,

        "missing_prerequisites":
            missing,

        "current_credits":
            current_credits,

        "new_total_credits":
            new_total
    }
