from database import (
    add_registration,
    remove_registration
)

from eligibility import check_eligibility


def register_course(
    student,
    course_code
):

    result = check_eligibility(
        student,
        course_code
    )

    if not result["eligible"]:

        return False, result["reasons"]

    registration_id = add_registration(
        student["student_id"],
        course_code
    )

    return True, registration_id


def drop_course(
    student_id,
    course_code
):

    remove_registration(
        student_id,
        course_code
    )

    return True
