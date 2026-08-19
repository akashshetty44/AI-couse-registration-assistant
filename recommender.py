from database import (
    get_all_courses,
    get_completed_courses,
    get_registered_courses
)

from eligibility import check_eligibility


def calculate_course_score(
    student,
    course
):

    score = 0

    reasons = []

    # Program match
    if (
        course["department"].lower()
        in
        student["program"].lower()
    ):

        score += 30

        reasons.append(
            "Matches your academic program."
        )

    # Semester match
    if (
        course["semester"]
        ==
        student["semester"]
    ):

        score += 25

        reasons.append(
            "Recommended for your current semester."
        )

    elif (
        course["semester"]
        ==
        student["semester"] + 1
    ):

        score += 10

    # Seat availability
    available_seats = (
        course["capacity"]
        -
        course["enrolled"]
    )

    if available_seats > 10:

        score += 10

        reasons.append(
            "Good seat availability."
        )

    elif available_seats > 0:

        score += 5

    # Course level
    if (
        course["semester"]
        <=
        student["semester"]
    ):

        score += 10

    # Keyword relevance
    text = (
        course["course_name"]
        + " "
        + course["description"]
    ).lower()

    keywords = [
        "machine learning",
        "artificial intelligence",
        "cloud",
        "security",
        "network",
        "database",
        "programming"
    ]

    for keyword in keywords:

        if keyword in text:

            score += 3

    return score, reasons


def recommend_courses(student):

    completed = {
        course["course_code"]
        for course in
        get_completed_courses(
            student["student_id"]
        )
    }

    registered = {
        course["course_code"]
        for course in
        get_registered_courses(
            student["student_id"]
        )
    }

    recommendations = []

    for course in get_all_courses():

        if course["course_code"] in completed:
            continue

        if course["course_code"] in registered:
            continue

        eligibility = check_eligibility(
            student,
            course["course_code"]
        )

        if not eligibility["eligible"]:
            continue

        score, reasons = calculate_course_score(
            student,
            course
        )

        recommendations.append(
            {
                "course_code":
                    course["course_code"],

                "course_name":
                    course["course_name"],

                "credits":
                    course["credits"],

                "department":
                    course["department"],

                "score":
                    score,

                "reasons":
                    reasons
            }
        )

    return sorted(
        recommendations,
        key=lambda item: item["score"],
        reverse=True
    )
