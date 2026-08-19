from database import (
    get_all_courses,
    get_completed_courses,
    get_registered_courses
)

from eligibility import check_eligibility

from recommender import recommend_courses


def normalize(text):

    return text.lower().strip()


def find_course_in_text(text):

    text = normalize(text)

    for course in get_all_courses():

        course_code = course[
            "course_code"
        ].lower()

        course_name = course[
            "course_name"
        ].lower()

        if course_code in text:

            return course

        if course_name in text:

            return course

        words = course_name.split()

        if (
            len(words) >= 2
            and
            all(word in text for word in words)
        ):

            return course

    return None


def answer_question(
    student,
    question
):

    question_lower = normalize(
        question
    )

    # -----------------------------------------
    # Greeting
    # -----------------------------------------

    if any(
        word in question_lower
        for word in [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening"
        ]
    ):

        return (
            f"Hello {student['name']}! 👋\n\n"
            "I can help you check eligibility, "
            "find courses, recommend electives, "
            "and explain registration rules."
        )

    # -----------------------------------------
    # Profile
    # -----------------------------------------

    if (
        "my profile" in question_lower
        or
        "my details" in question_lower
    ):

        return f"""
### 👤 Student Profile

**Name:** {student['name']}

**Student ID:** {student['student_id']}

**Program:** {student['program']}

**Semester:** {student['semester']}

**CGPA:** {student['cgpa']}

**Completed Credits:** {student['completed_credits']}

**Maximum Credits:** {student['max_credits']}
"""

    # -----------------------------------------
    # Completed courses
    # -----------------------------------------

    if (
        "completed courses"
        in question_lower
        or
        "courses i completed"
        in question_lower
    ):

        courses = get_completed_courses(
            student["student_id"]
        )

        if not courses:

            return (
                "You have no completed courses "
                "recorded in the system."
            )

        result = "### 📚 Completed Courses\n\n"

        for course in courses:

            result += (
                f"- **{course['course_code']}** - "
                f"{course['course_name']} "
                f"(Grade: {course['grade']})\n"
            )

        return result

    # -----------------------------------------
    # Registered courses
    # -----------------------------------------

    if (
        "registered courses"
        in question_lower
        or
        "my registration"
        in question_lower
    ):

        courses = get_registered_courses(
            student["student_id"]
        )

        if not courses:

            return (
                "You have not registered for "
                "any courses yet."
            )

        result = "### 📝 Registered Courses\n\n"

        for course in courses:

            result += (
                f"- **{course['course_code']}** - "
                f"{course['course_name']} "
                f"({course['credits']} credits)\n"
            )

        return result

    # -----------------------------------------
    # Recommendations
    # -----------------------------------------

    if (
        "recommend" in question_lower
        or
        "suggest" in question_lower
        or
        "best courses" in question_lower
    ):

        recommendations = recommend_courses(
            student
        )

        if not recommendations:

            return (
                "I could not find any currently "
                "eligible courses for you."
            )

        result = "### ⭐ Recommended Courses\n\n"

        for course in recommendations[:5]:

            result += (
                f"**{course['course_code']} - "
                f"{course['course_name']}**\n"
            )

            result += (
                f"- Credits: {course['credits']}\n"
            )

            result += (
                f"- Recommendation Score: "
                f"{course['score']}\n"
            )

            if course["reasons"]:

                result += (
                    "- "
                    + ", ".join(
                        course["reasons"]
                    )
                    + "\n\n"
                )

        return result

    # -----------------------------------------
    # Course detection
    # -----------------------------------------

    course = find_course_in_text(
        question
    )

    if course:

        eligibility = check_eligibility(
            student,
            course["course_code"]
        )

        # -------------------------------------
        # Eligibility question
        # -------------------------------------

        if (
            "eligible" in question_lower
            or
            "can i" in question_lower
            or
            "register" in question_lower
        ):

            if eligibility["eligible"]:

                return f"""
### ✅ You are eligible

You can register for:

**{course['course_code']} - {course['course_name']}**

**Credits:** {course['credits']}

**Schedule:** {course['days']} {course['start_time']} - {course['end_time']}

Your registered credits would become:

**{eligibility['new_total_credits']}**
"""

            result = (
                "### ❌ You are not currently eligible\n\n"
            )

            for reason in eligibility["reasons"]:

                result += (
                    f"- {reason}\n"
                )

            return result

        # -------------------------------------
        # Course information
        # -------------------------------------

        return f"""
### 📚 {course['course_code']} - {course['course_name']}

**Department:** {course['department']}

**Credits:** {course['credits']}

**Semester:** {course['semester']}

**Schedule:** {course['days']} {course['start_time']} - {course['end_time']}

**Available Seats:** {course['capacity'] - course['enrolled']}

**Description:** {course['description']}
"""

    # -----------------------------------------
    # Default response
    # -----------------------------------------

    return """
I couldn't completely understand your question.

Try asking:

- **Can I register for Machine Learning?**
- **Recommend courses for me.**
- **Show my completed courses.**
- **Show my registered courses.**
- **Tell me about Artificial Intelligence.**
"""
