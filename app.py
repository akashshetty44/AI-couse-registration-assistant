import streamlit as st
import pandas as pd
import hashlib

from database import (
    init_database,
    get_student,
    get_all_courses,
    get_completed_courses,
    get_registered_courses,
    get_course,
    add_course,
)
from eligibility import check_eligibility
from recommender import recommend_courses
from registration import register_course, drop_course
from chatbot import answer_question


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI Course Registration Assistant",
    page_icon="🎓",
    layout="wide"
)

init_database()


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "student_id" not in st.session_state:
    st.session_state.student_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

if not st.session_state.logged_in:

    st.title("🎓 AI-Powered Course Registration Assistant")

    st.caption(
        "Intelligent course selection, eligibility checking "
        "and registration guidance"
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.subheader("🔐 Student Login")

        student_id = st.text_input(
            "Student ID",
            placeholder="STU001"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="1234"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            student = get_student(
                student_id.strip().upper()
            )

            if student:

                entered_password = hashlib.sha256(
                    password.encode()
                ).hexdigest()

                if student["password"] == entered_password:

                    st.session_state.logged_in = True
                    st.session_state.student_id = student["student_id"]

                    st.rerun()

                else:
                    st.error("Incorrect password.")

            else:
                st.error("Student ID not found.")

        st.info(
            "Demo Login\n\n"
            "Student ID: STU001\n\n"
            "Password: 1234"
        )

    st.stop()


# --------------------------------------------------
# LOAD STUDENT
# --------------------------------------------------

student = get_student(
    st.session_state.student_id
)

courses = get_all_courses()

completed = get_completed_courses(
    student["student_id"]
)

registered = get_registered_courses(
    student["student_id"]
)

current_credits = sum(
    course["credits"]
    for course in registered
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("🎓 Registration Assistant")

    st.write(
        f"**Student:** {student['name']}"
    )

    st.write(
        f"**ID:** {student['student_id']}"
    )

    st.write(
        f"**Program:** {student['program']}"
    )

    st.write(
        f"**Semester:** {student['semester']}"
    )

    st.metric(
        "Registered Credits",
        f"{current_credits}/{student['max_credits']}"
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.student_id = None
        st.session_state.messages = []

        st.rerun()


# --------------------------------------------------
# MAIN TITLE
# --------------------------------------------------

st.title("🎓 AI Course Registration Assistant")

st.caption(
    "Your intelligent academic registration companion"
)


# --------------------------------------------------
# DASHBOARD METRICS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "📚 Completed Courses",
    len(completed)
)

col2.metric(
    "📝 Registered Courses",
    len(registered)
)

col3.metric(
    "🎯 Current Credits",
    current_credits
)

col4.metric(
    "⭐ CGPA",
    student["cgpa"]
)


# --------------------------------------------------
# TABS
# --------------------------------------------------

(
    chat_tab,
    courses_tab,
    eligibility_tab,
    recommendation_tab,
    registration_tab,
    profile_tab,
    admin_tab
) = st.tabs(
    [
        "🤖 AI Assistant",
        "📚 Courses",
        "✅ Eligibility",
        "⭐ Recommendations",
        "📝 Registration",
        "👤 My Profile",
        "⚙️ Admin"
    ]
)


# ==================================================
# AI ASSISTANT
# ==================================================

with chat_tab:

    st.header("🤖 AI Registration Assistant")

    st.write(
        "Ask questions about courses, eligibility, "
        "prerequisites and registration."
    )

    suggestions = [
        "Can I register for Machine Learning?",
        "Recommend courses for me.",
        "Show my completed courses.",
        "Show my registered courses.",
        "Tell me about Artificial Intelligence."
    ]

    columns = st.columns(3)

    for i, suggestion in enumerate(suggestions):

        if columns[i % 3].button(
            suggestion,
            key=f"suggestion_{i}",
            use_container_width=True
        ):

            st.session_state.messages.append(
                ("user", suggestion)
            )

            response = answer_question(
                student,
                suggestion
            )

            st.session_state.messages.append(
                ("assistant", response)
            )

            st.rerun()

    for role, message in st.session_state.messages:

        with st.chat_message(role):
            st.markdown(message)

    question = st.chat_input(
        "Ask about course registration..."
    )

    if question:

        st.session_state.messages.append(
            ("user", question)
        )

        response = answer_question(
            student,
            question
        )

        st.session_state.messages.append(
            ("assistant", response)
        )

        st.rerun()


# ==================================================
# COURSES
# ==================================================

with courses_tab:

    st.header("📚 Available Courses")

    search = st.text_input(
        "🔎 Search course"
    )

    departments = ["All"] + sorted(
        set(
            course["department"]
            for course in courses
        )
    )

    department = st.selectbox(
        "Department",
        departments
    )

    rows = []

    for course in courses:

        matches_search = (
            not search
            or search.lower() in course["course_code"].lower()
            or search.lower() in course["course_name"].lower()
            or search.lower() in course["department"].lower()
        )

        matches_department = (
            department == "All"
            or course["department"] == department
        )

        if matches_search and matches_department:

            rows.append(
                {
                    "Code": course["course_code"],
                    "Course": course["course_name"],
                    "Department": course["department"],
                    "Credits": course["credits"],
                    "Semester": course["semester"],
                    "Seats Available": (
                        course["capacity"]
                        - course["enrolled"]
                    ),
                    "Schedule": (
                        f"{course['days']} "
                        f"{course['start_time']}-"
                        f"{course['end_time']}"
                    )
                }
            )

    if rows:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "No courses found."
        )


# ==================================================
# ELIGIBILITY
# ==================================================

with eligibility_tab:

    st.header("✅ Course Eligibility Checker")

    course_options = [
        f"{course['course_code']} - "
        f"{course['course_name']}"
        for course in courses
    ]

    selected_course = st.selectbox(
        "Select a course",
        course_options
    )

    course_code = selected_course.split(" - ")[0]

    if st.button(
        "Check Eligibility",
        type="primary"
    ):

        result = check_eligibility(
            student,
            course_code
        )

        course = get_course(
            course_code
        )

        if result["eligible"]:

            st.success(
                f"✅ You are eligible for "
                f"{course['course_code']} - "
                f"{course['course_name']}"
            )

            st.write(
                f"Current credits: "
                f"**{result['current_credits']}**"
            )

            st.write(
                f"After registration: "
                f"**{result['new_total_credits']}**"
            )

        else:

            st.error(
                "❌ You are currently not eligible."
            )

            for reason in result["reasons"]:

                st.write(
                    f"❌ {reason}"
                )

        for warning in result["warnings"]:

            st.warning(warning)


# ==================================================
# RECOMMENDATIONS
# ==================================================

with recommendation_tab:

    st.header("⭐ AI Course Recommendations")

    st.write(
        "Recommendations are based on your "
        "program, semester, eligibility, "
        "availability and academic profile."
    )

    if st.button(
        "Generate Recommendations",
        type="primary"
    ):

        recommendations = recommend_courses(
            student
        )

        if recommendations:

            for course in recommendations[:8]:

                with st.container(border=True):

                    st.subheader(
                        f"{course['course_code']} - "
                        f"{course['course_name']}"
                    )

                    st.write(
                        f"Credits: {course['credits']} "
                        f"| Recommendation Score: "
                        f"{course['score']}"
                    )

                    for reason in course["reasons"]:

                        st.write(
                            f"✓ {reason}"
                        )

        else:

            st.warning(
                "No eligible courses found."
            )


# ==================================================
# REGISTRATION
# ==================================================

with registration_tab:

    st.header("📝 Course Registration")

    registered = get_registered_courses(
        student["student_id"]
    )

    if registered:

        registration_data = []

        for course in registered:

            registration_data.append(
                {
                    "Code": course["course_code"],
                    "Course": course["course_name"],
                    "Credits": course["credits"],
                    "Schedule": (
                        f"{course['days']} "
                        f"{course['start_time']}-"
                        f"{course['end_time']}"
                    )
                }
            )

        st.dataframe(
            pd.DataFrame(registration_data),
            use_container_width=True,
            hide_index=True
        )

        drop_options = [
            f"{course['course_code']} - "
            f"{course['course_name']}"
            for course in registered
        ]

        course_to_drop = st.selectbox(
            "Course to drop",
            drop_options
        )

        if st.button(
            "Drop Course"
        ):

            drop_course(
                student["student_id"],
                course_to_drop.split(" - ")[0]
            )

            st.success(
                "Course dropped successfully."
            )

            st.rerun()

    else:

        st.info(
            "You have not registered for any courses."
        )

    st.divider()

    registration_options = [
        f"{course['course_code']} - "
        f"{course['course_name']}"
        for course in courses
    ]

    course_selection = st.selectbox(
        "Select course to register",
        registration_options,
        key="registration_course"
    )

    course_code = course_selection.split(" - ")[0]

    course = get_course(course_code)

    st.write(
        f"**Description:** "
        f"{course['description']}"
    )

    if st.button(
        "Check Before Registration"
    ):

        result = check_eligibility(
            student,
            course_code
        )

        if result["eligible"]:

            st.success(
                "✅ All registration checks passed."
            )

        else:

            st.error(
                "❌ Registration cannot proceed."
            )

            for reason in result["reasons"]:

                st.write(
                    f"❌ {reason}"
                )

    if st.button(
        "Register Course",
        type="primary"
    ):

        success, result = register_course(
            student,
            course_code
        )

        if success:

            st.success(
                "🎉 Course registered successfully!"
            )

            st.balloons()

            st.rerun()

        else:

            st.error(
                "❌ Registration failed."
            )

            for reason in result:

                st.write(
                    f"❌ {reason}"
                )


# ==================================================
# PROFILE
# ==================================================

with profile_tab:

    st.header("👤 My Student Profile")

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Student ID:** "
            f"{student['student_id']}"
        )

        st.write(
            f"**Name:** "
            f"{student['name']}"
        )

        st.write(
            f"**Email:** "
            f"{student['email']}"
        )

        st.write(
            f"**Program:** "
            f"{student['program']}"
        )

    with col2:

        st.write(
            f"**Semester:** "
            f"{student['semester']}"
        )

        st.write(
            f"**CGPA:** "
            f"{student['cgpa']}"
        )

        st.write(
            f"**Completed Credits:** "
            f"{student['completed_credits']}"
        )

        st.write(
            f"**Maximum Credits:** "
            f"{student['max_credits']}"
        )

    st.subheader(
        "📚 Completed Courses"
    )

    completed_data = []

    for course in completed:

        completed_data.append(
            {
                "Code": course["course_code"],
                "Course": course["course_name"],
                "Credits": course["credits"],
                "Grade": course["grade"]
            }
        )

    if completed_data:

        st.dataframe(
            pd.DataFrame(completed_data),
            use_container_width=True,
            hide_index=True
        )


# ==================================================
# ADMIN
# ==================================================

with admin_tab:

    st.header("⚙️ Admin Course Management")

    st.warning(
        "Demo admin module. "
        "Production systems should use "
        "administrator authentication."
    )

    with st.form("add_course_form"):

        col1, col2 = st.columns(2)

        with col1:

            code = st.text_input(
                "Course Code"
            )

            name = st.text_input(
                "Course Name"
            )

            department = st.text_input(
                "Department",
                "Computer Science"
            )

            credits = st.number_input(
                "Credits",
                min_value=1,
                max_value=10,
                value=3
            )

            semester = st.number_input(
                "Semester",
                min_value=1,
                max_value=8,
                value=6
            )

        with col2:

            capacity = st.number_input(
                "Capacity",
                min_value=1,
                max_value=500,
                value=60
            )

            days = st.text_input(
                "Days",
                "Mon,Wed"
            )

            start_time = st.text_input(
                "Start Time",
                "10:00"
            )

            end_time = st.text_input(
                "End Time",
                "11:00"
            )

            description = st.text_area(
                "Description"
            )

        submitted = st.form_submit_button(
            "Add Course"
        )

        if submitted:

            try:

                add_course(
                    code.upper(),
                    name,
                    department,
                    credits,
                    semester,
                    capacity,
                    description,
                    days,
                    start_time,
                    end_time
                )

                st.success(
                    "Course added successfully."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Unable to add course: {error}"
                )

    st.subheader(
        "Current Course Database"
    )

    admin_data = []

    for course in courses:

        admin_data.append(
            {
                "Code": course["course_code"],
                "Course": course["course_name"],
                "Credits": course["credits"],
                "Semester": course["semester"],
                "Capacity": course["capacity"],
                "Enrolled": course["enrolled"],
                "Available": (
                    course["capacity"]
                    - course["enrolled"]
                )
            }
        )

    st.dataframe(
        pd.DataFrame(admin_data),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "AI-Powered Course Registration Assistant | "
    "Student Academic Support System"
)
