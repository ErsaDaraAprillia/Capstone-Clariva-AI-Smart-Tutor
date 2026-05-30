import re
import streamlit as st
import markdown as md
from fpdf import FPDF
from services.gemini_service import generate_response
from prompts.tutor_prompt import build_tutor_prompt
from prompts.quiz_prompt import build_quiz_prompt
from prompts.studyplan_prompt import build_studyplan_prompt
from prompts.evaluator_prompt import build_evaluator_prompt
from prompts.comparison_prompt import build_comparison_prompts
from datetime import datetime

# ========================================
# PAGE CONFIG
# ========================================
st.set_page_config(
    page_title="Clariva AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# SESSION STATE
# ========================================
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'total_quizzes' not in st.session_state:
    st.session_state.total_quizzes = 0
if 'total_plans' not in st.session_state:
    st.session_state.total_plans = 0
if 'total_evaluations' not in st.session_state:
    st.session_state.total_evaluations = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ========================================
# CSS
# ========================================
def load_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ style.css not found. Using default styles.")

load_css()

# ========================================
# HELPER — render AI response properly
# ========================================
def sanitize_for_pdf(text):
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    text = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2212': '-',
        '\u2026': '...', '\u22ef': '...',
        '\u2022': '*', '\u25e6': '-', '\u25aa': '-', '\u25a0': '*',
        '\u2192': '->', '\u2190': '<-', '\u2194': '<->', '\u27f9': '=>',
        '\u2193': 'v', '\u2191': '^',
        '\xd7': 'x', '\xf7': '/', '\u2248': '~=', '\u2260': '!=',
        '\u2264': '<=', '\u2265': '>=', '\u221e': 'inf',
        '\xa9': '(C)', '\xae': '(R)', '\u2122': '(TM)',
        '\xb0': 'deg', '\xa7': 'S', '\xb6': 'P',
    }
    for special, replacement in replacements.items():
        text = text.replace(special, replacement)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def strip_emoji(text):
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    try:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f900-\U0001f9ff"
            "\U0001fa00-\U0001fa6f"
            "]", flags=re.UNICODE
        )
        return emoji_pattern.sub('', text).strip()
    except Exception:
        return text

def safe_text(text, max_length=None):
    text = sanitize_for_pdf(strip_emoji(str(text)))
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text

# Render AI response to Streamlit safely
def render_response(response):
    if response is None:
        st.info("No response available.")
        return

    text = str(response).strip()
    if not text:
        st.info("No response available.")
        return

    try:
        st.markdown(text)
    except Exception:
        st.write(text)

# Font paths — LiberationSans (confirmed ada di sistem)
FONT_REGULAR = "C:/Windows/Fonts/times.ttf"
FONT_BOLD    = "C:/Windows/Fonts/timesbd.ttf"
FONT_ITALIC  = "C:/Windows/Fonts/timesi.ttf"

def generate_pdf(title, content_dict):
    try:
        pdf = FPDF()
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # Register Unicode font
        pdf.add_font("Sans", style="",  fname=FONT_REGULAR, uni=True)
        pdf.add_font("Sans", style="B", fname=FONT_BOLD,    uni=True)
        pdf.add_font("Sans", style="I", fname=FONT_ITALIC,  uni=True)

        title_clean = safe_text(title, 80)

        # ── Purple header bar ──────────────────────────────────
        pdf.set_fill_color(99, 102, 241)
        pdf.rect(0, 0, 210, 30, 'F')

        pdf.set_font("Sans", "B", 20)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, 7)
        pdf.cell(120, 10, "Clariva AI", ln=False)

        pdf.set_font("Sans", "I", 9)
        pdf.set_xy(15, 19)
        pdf.cell(0, 6,
            f"Generated on {datetime.now().strftime('%B %d, %Y  %H:%M')}",
            ln=True)

        # ── Title section ──────────────────────────────────────
        pdf.set_xy(15, 38)
        pdf.set_font("Sans", "B", 17)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 9, title_clean)
        pdf.ln(2)

        # ── Purple underline ───────────────────────────────────
        pdf.set_draw_color(99, 102, 241)
        pdf.set_line_width(1.0)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

        # ── Meta info table ────────────────────────────────────
        for label, value in content_dict.items():
            if label == "content":
                continue
            label_clean = safe_text(str(label), 35)
            value_clean = safe_text(str(value), 120)

            # Label column — purple bg
            pdf.set_fill_color(238, 240, 255)
            pdf.set_font("Sans", "B", 9)
            pdf.set_text_color(67, 56, 202)
            pdf.cell(42, 8, f"  {label_clean}", border=0, ln=False, fill=True)

            # Value column — white bg
            pdf.set_fill_color(252, 252, 254)
            pdf.set_font("Sans", "", 9)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, 8, f"  {value_clean}", border=0, ln=True, fill=True)
            pdf.ln(1)

        # ── Content divider ────────────────────────────────────
        pdf.ln(3)
        pdf.set_draw_color(200, 200, 220)
        pdf.set_line_width(0.3)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)

        # ── Main content ───────────────────────────────────────
        content_raw = content_dict.get("content", "")
        content = safe_text(content_raw)

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                pdf.ln(2)
                continue

            try:
                # H1
                if line.startswith("# ") and not line.startswith("## "):
                    pdf.ln(3)
                    pdf.set_fill_color(99, 102, 241)
                    pdf.set_font("Sans", "B", 13)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(0, 9, f"  {line[2:]}", ln=True, fill=True)
                    pdf.ln(2)
                    pdf.set_text_color(30, 41, 59)

                # H2
                elif line.startswith("## ") and not line.startswith("### "):
                    pdf.ln(3)
                    pdf.set_fill_color(238, 240, 255)
                    pdf.set_font("Sans", "B", 12)
                    pdf.set_text_color(67, 56, 202)
                    pdf.cell(0, 8, f"  {line[3:]}", ln=True, fill=True)
                    pdf.ln(2)
                    pdf.set_text_color(30, 41, 59)

                # H3
                elif line.startswith("### "):
                    pdf.ln(2)
                    pdf.set_font("Sans", "B", 11)
                    pdf.set_text_color(99, 102, 241)
                    pdf.multi_cell(0, 7, line[4:])
                    # underline
                    pdf.set_draw_color(200, 210, 255)
                    pdf.set_line_width(0.3)
                    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                    pdf.ln(3)
                    pdf.set_text_color(30, 41, 59)

                # Horizontal rule
                elif line.startswith("---"):
                    pdf.ln(2)
                    pdf.set_draw_color(220, 220, 235)
                    pdf.set_line_width(0.4)
                    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                    pdf.ln(4)

                # Bullet
                elif line.startswith("- ") or line.startswith("* "):
                    pdf.set_font("Sans", "", 10)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_x(20)
                    pdf.cell(6, 6, "-", ln=False)
                    pdf.multi_cell(0, 6, line[2:])

                # Numbered list
                elif len(line) > 2 and line[0].isdigit() and line[1] in ".)":
                    pdf.set_font("Sans", "", 10)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_x(20)
                    pdf.multi_cell(0, 6, line)

                # Bold-only line
                elif line.startswith("**") and line.endswith("**") and len(line) > 4:
                    pdf.set_font("Sans", "B", 10)
                    pdf.set_text_color(30, 41, 59)
                    pdf.multi_cell(0, 6, line[2:-2])

                # Normal paragraph
                else:
                    pdf.set_font("Sans", "", 10)
                    pdf.set_text_color(50, 60, 80)
                    pdf.multi_cell(0, 6, line)

            except Exception:
                try:
                    pdf.set_font("Sans", "", 10)
                    pdf.multi_cell(0, 6, "[content]")
                except Exception:
                    pass

        # ── Footer ─────────────────────────────────────────────
        pdf.set_y(-16)
        pdf.set_fill_color(99, 102, 241)
        pdf.rect(0, pdf.get_y() - 1, 210, 20, 'F')
        pdf.set_font("Sans", "", 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8,
            "Clariva AI  |  Powered by Google Gemini  |  Advanced Prompt Engineering Capstone 2026",
            align="C")

        return bytes(pdf.output())

    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None
    
# ========================================
# SIDEBAR
# ========================================
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    default_level = st.selectbox(
        "Default Learning Level:",
        ["Beginner", "Intermediate", "Advanced"],
        index=0,
        help="Set your preferred explanation level"
    )

    st.markdown("---")

    st.markdown("## 📊 Your Stats")
    st.markdown(f"**📚 Questions Asked:** {st.session_state.total_questions}")
    st.markdown(f"**📝 Quizzes Generated:** {st.session_state.total_quizzes}")
    st.markdown(f"**📅 Study Plans:** {st.session_state.total_plans}")
    st.markdown(f"**✅ Evaluations:** {st.session_state.total_evaluations}")

    st.markdown("---")

    st.markdown("## 💡 Quick Tips")
    st.info("💡 Use tabs to navigate between features easily!")
    st.info("🎯 Try Prompt Comparison to see different AI strategies!")
    st.info("📥 Download your results for offline study!")

    st.markdown("---")

    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.total_questions = 0
        st.session_state.total_quizzes = 0
        st.session_state.total_plans = 0
        st.session_state.total_evaluations = 0
        st.session_state.chat_history = []
        st.success("✅ All data cleared!")
        st.rerun()

# ========================================
# HEADER
# ========================================
st.markdown("""
<div class="header-card">
    <h1>🎓 Clariva</h1>
    <p>Your Intelligent Learning Companion</p>
</div>
""", unsafe_allow_html=True)

# ========================================
# STATS DASHBOARD
# ========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <p class="stat-number">{st.session_state.total_questions}</p>
        <p class="stat-label">Questions</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <p class="stat-number">{st.session_state.total_quizzes}</p>
        <p class="stat-label">Quizzes</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <p class="stat-number">{st.session_state.total_plans}</p>
        <p class="stat-label">Study Plans</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <p class="stat-number">{st.session_state.total_evaluations}</p>
        <p class="stat-label">Evaluations</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========================================
# TABS
# ========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Ask Tutor",
    "📝 Quiz Generator",
    "📚 Study Plan",
    "✅ Answer Evaluator",
    "🔍 Prompt Comparison"
])

# ========================================
# TAB 1: ASK TUTOR
# ========================================
with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 💬 Ask Your AI Tutor")
    st.markdown("""
    <div class="info-box">
        💡 Ask any educational question and get detailed explanations tailored to your level!
    </div>
    """, unsafe_allow_html=True)

    question = st.text_area(
        "📝 Your Question:",
        placeholder="e.g., Explain how photosynthesis works",
        height=120,
        help="Type your question here"
    )

    level = st.selectbox(
        "📊 Explanation Level:",
        ["Beginner", "Intermediate", "Advanced"],
        index=["Beginner", "Intermediate", "Advanced"].index(default_level),
        help="Choose how detailed you want the explanation"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Generate Answer", use_container_width=True, key="ask_btn"):
            if question:
                try:
                    with st.spinner("🤔 Clariva is thinking..."):
                        prompt = build_tutor_prompt(question, level)
                        response = generate_response(prompt)

                        st.session_state.total_questions += 1
                        st.session_state.chat_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "question": question,
                            "level": level,
                            "answer": response
                        })

                        st.markdown("---")
                        st.markdown("""
                        <div class="success-box">
                            ✅ Answer generated successfully!
                        </div>
                        """, unsafe_allow_html=True)

                        render_response(response)

                        pdf_bytes = generate_pdf(
                            title="AI Tutor Answer",
                            content_dict={
                                "Topic": question[:80],
                                "Level": level,
                                "Date": datetime.now().strftime("%B %d, %Y"),
                                "content": response
                            }
                        )
                        
                        if pdf_bytes:
                            st.download_button(
                                "📥 Download Answer (PDF)",
                                data=pdf_bytes,
                                file_name=f"clariva_answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Please check your API configuration or try again.")
            else:
                st.warning("⚠️ Please enter a question!")

    with col2:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_tutor"):
            st.rerun()

    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 📜 Recent Questions")
        for chat in reversed(st.session_state.chat_history[-3:]):
            with st.expander(f"🕐 {chat['timestamp']} - {chat['level']} Level"):
                st.markdown(f"**Q:** {chat['question']}")
                st.markdown(chat['answer'])

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# TAB 2: QUIZ GENERATOR
# ========================================
with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Quiz Generator")
    st.markdown("""
    <div class="info-box">
        📝 Generate adaptive multiple-choice quizzes tailored to your learning level!
    </div>
    """, unsafe_allow_html=True)

    quiz_topic = st.text_input(
        "📖 Quiz Topic:",
        placeholder="e.g., Python Functions, World War II, Cell Biology",
        help="Enter the topic you want to create a quiz about"
    )

    col_q, col_l = st.columns(2)
    with col_q:
        num_questions = st.slider(
            "🔢 Number of Questions:",
            min_value=1,
            max_value=10,
            value=5,
            help="Select how many questions you want"
        )
    with col_l:
        quiz_level = st.selectbox(
            "📊 Difficulty Level:",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(default_level),
            help="Beginner = basic recall | Intermediate = application | Advanced = analysis"
        )

    badge_colors = {
        "Beginner":     ("🟢", "#d1fae5", "#065f46"),
        "Intermediate": ("🔵", "#dbeafe", "#1e3a8a"),
        "Advanced":     ("🟣", "#ede9fe", "#4c1d95"),
    }
    icon, bg, fg = badge_colors[quiz_level]
    st.markdown(f"""
    <div style="background:{bg}; color:{fg}; padding:10px 16px;
                border-radius:10px; font-weight:600; font-size:0.9rem;
                margin-bottom:8px; display:inline-block;">
        {icon} {quiz_level} Mode -
        {'Basic definitions and recall questions' if quiz_level == 'Beginner'
         else 'Application and understanding questions' if quiz_level == 'Intermediate'
         else 'Analysis, edge cases, and scenario-based questions'}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎲 Generate Quiz", use_container_width=True, key="gen_quiz"):
        if quiz_topic:
            try:
                with st.spinner(f"🎯 Generating {quiz_level} quiz on {quiz_topic}..."):
                    quiz_prompt = build_quiz_prompt(quiz_topic, num_questions, quiz_level)
                    quiz_response = generate_response(quiz_prompt)

                    st.session_state.total_quizzes += 1

                    st.markdown("---")
                    st.markdown("""
                    <div class="success-box">
                        ✅ Quiz generated successfully!
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"### 📋 {quiz_level} Quiz: {quiz_topic}")
                    render_response(quiz_response)

                    pdf_bytes = generate_pdf(
                        title=f"{quiz_level} Quiz: {quiz_topic}",
                        content_dict={
                            "Topic": quiz_topic,
                            "Level": quiz_level,
                            "Questions": str(num_questions),
                            "Date": datetime.now().strftime("%B %d, %Y"),
                            "content": quiz_response
                        }
                    )
                    
                    if pdf_bytes:
                        st.download_button(
                            "📥 Download Quiz (PDF)",
                            data=pdf_bytes,
                            file_name=f"clariva_quiz_{quiz_topic.replace(' ','_')}_{quiz_level}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Please check your API configuration or try again.")
        else:
            st.warning("⚠️ Please enter a quiz topic!")

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# TAB 3: STUDY PLAN
# ========================================
with tab3:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 📚 Study Plan Generator")
    st.markdown("""
    <div class="info-box">
        📚 Get a fully personalized study roadmap - tailored to your level,
        goal, and available time every day!
    </div>
    """, unsafe_allow_html=True)

    study_topic = st.text_input(
        "📖 What do you want to learn?",
        placeholder="e.g., Python Programming, Calculus, Spanish, Machine Learning...",
        help="Enter the subject or skill you want to master"
    )

    study_goal = st.text_input(
        "🎯 What is your goal?",
        placeholder="e.g., Pass my exam, Build a project, Get a job, Personal interest...",
        help="Having a clear goal helps the AI create a more focused plan"
    )

    col_lv, col_dur = st.columns(2)
    with col_lv:
        plan_level = st.selectbox(
            "📊 Your Current Level:",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(default_level),
            help="How much do you already know about this topic?"
        )
    with col_dur:
        study_duration = st.slider(
            "📅 Study Duration (Days):",
            min_value=3,
            max_value=30,
            value=7,
            help="How many days do you want to complete this plan?"
        )

    daily_time = st.select_slider(
        "⏰ How much time can you study per day?",
        options=["30 minutes", "1 hour", "1.5 hours", "2 hours", "3+ hours"],
        value="1 hour",
        help="Be realistic - consistency beats intensity!"
    )

    if study_topic:
        st.markdown(f"""
        <div style="background:#1e293b; border:2px dashed #667eea; border-radius:12px;
                    padding:14px 18px; margin:12px 0; color:#cbd5e1; font-size:0.92rem;">
            📋 <b>Plan Preview:</b> &nbsp;
            <b>{study_duration}-day</b> &nbsp;|&nbsp;
            <b>{plan_level}</b> level &nbsp;|&nbsp;
            <b>{daily_time}/day</b> &nbsp;|&nbsp;
            Goal: <b>{study_goal if study_goal else 'Master the topic'}</b>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🗓️ Create My Study Plan", use_container_width=True, key="gen_plan"):
        if not study_topic:
            st.warning("⚠️ Please enter a topic to study!")
        else:
            try:
                with st.spinner(f"📝 Building your {study_duration}-day {plan_level} plan..."):
                    study_prompt = build_studyplan_prompt(
                        topic=study_topic,
                        duration=study_duration,
                        level=plan_level,
                        goal=study_goal if study_goal else "Master the topic thoroughly",
                        daily_time=daily_time
                    )
                    study_response = generate_response(study_prompt)

                    st.session_state.total_plans += 1

                    st.markdown("---")
                    st.markdown("""
                    <div class="success-box">
                        ✅ Your personalized study plan is ready!
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"### 📅 {study_duration}-Day {plan_level} Plan: {study_topic}")
                    render_response(study_response)

                    pdf_bytes = generate_pdf(
                        title=f"Study Plan: {study_topic}",
                        content_dict={
                            "Topic": study_topic,
                            "Level": plan_level,
                            "Duration": f"{study_duration} days",
                            "Daily Time": daily_time,
                            "Goal": study_goal or "Master the topic",
                            "Date": datetime.now().strftime("%B %d, %Y"),
                            "content": study_response
                        }
                    )
                    
                    if pdf_bytes:
                        st.download_button(
                            "📥 Download Study Plan (PDF)",
                            data=pdf_bytes,
                            file_name=f"clariva_studyplan_{study_topic.replace(' ','_')}_{plan_level}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Please check your API configuration or try again.")

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# TAB 4: ANSWER EVALUATOR
# ========================================
with tab4:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### ✅ AI Answer Evaluator")
    st.markdown("""
    <div class="info-box">
        ✅ Submit your answer to a question and get detailed rubric-based scoring
        with strengths, weaknesses, and improvement tips!
    </div>
    """, unsafe_allow_html=True)

    eval_topic = st.text_input(
        "📖 Topic / Subject:",
        placeholder="e.g., Biology, Python Programming, World War II",
        help="What subject does this question belong to?"
    )

    eval_question = st.text_area(
        "❓ Original Question:",
        placeholder="e.g., Explain how the immune system responds to a virus.",
        height=80,
        help="Paste the question you are answering"
    )

    eval_level = st.selectbox(
        "📊 Your Learning Level:",
        ["Beginner", "Intermediate", "Advanced"],
        index=["Beginner", "Intermediate", "Advanced"].index(default_level),
        help="This adjusts the rubric and feedback style"
    )

    user_answer = st.text_area(
        "✍️ Your Answer:",
        placeholder="Write or paste your answer here...",
        height=150,
        help="Enter the answer you want to be evaluated"
    )

    if st.button("🎯 Evaluate My Answer", use_container_width=True, key="eval_btn"):
        if not eval_topic:
            st.warning("⚠️ Please enter the topic/subject!")
        elif not eval_question:
            st.warning("⚠️ Please enter the original question!")
        elif not user_answer:
            st.warning("⚠️ Please enter your answer!")
        else:
            try:
                with st.spinner("🔍 Evaluating your answer with rubric..."):
                    evaluator_prompt = build_evaluator_prompt(
                        question=eval_question,
                        topic=eval_topic,
                        user_answer=user_answer,
                        level=eval_level
                    )
                    evaluation_response = generate_response(evaluator_prompt)

                    st.session_state.total_evaluations += 1

                    st.markdown("---")
                    st.markdown("""
                    <div class="success-box">
                        ✅ Evaluation completed!
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### 📊 Evaluation Results")
                    render_response(evaluation_response)

                    pdf_bytes = generate_pdf(
                        title="Answer Evaluation Report",
                        content_dict={
                            "Topic": eval_topic,
                            "Level": eval_level,
                            "Question": eval_question[:100],
                            "Date": datetime.now().strftime("%B %d, %Y"),
                            "content": evaluation_response
                        }
                    )
                    
                    if pdf_bytes:
                        st.download_button(
                            "📥 Download Evaluation (PDF)",
                            data=pdf_bytes,
                            file_name=f"clariva_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Please check your API configuration or try again.")

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# TAB 5: PROMPT COMPARISON
# ========================================
with tab5:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Prompt Strategy Comparison Engine")
    st.markdown("""
    <div class="warning-box">
        🔬 <b>Compare 3 Advanced Prompt Engineering Techniques side by side!</b><br>
        Enter any topic - the AI auto-detects the domain and generates
        domain-relevant few-shot examples dynamically.
    </div>
    """, unsafe_allow_html=True)

    col_z, col_f, col_c = st.columns(3)
    with col_z:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.1); border:2px solid #10b981;
                    border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.5rem;">🟢</div>
            <div style="font-weight:700; color:#10b981; margin:6px 0;">Zero-Shot</div>
            <div style="font-size:0.82rem; color:#6ee7b7;">
                No examples given.<br>Raw question only.<br>
                <b>Tests baseline AI</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_f:
        st.markdown("""
        <div style="background:rgba(99,102,241,0.1); border:2px solid #6366f1;
                    border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.5rem;">🔵</div>
            <div style="font-weight:700; color:#818cf8; margin:6px 0;">Few-Shot</div>
            <div style="font-size:0.82rem; color:#a5b4fc;">
                2 domain examples given.<br>AI pattern-matches style.<br>
                <b>Dynamic per topic</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
        <div style="background:rgba(139,92,246,0.1); border:2px solid #8b5cf6;
                    border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.5rem;">🟣</div>
            <div style="font-weight:700; color:#a78bfa; margin:6px 0;">Chain-of-Thought</div>
            <div style="font-size:0.82rem; color:#c4b5fd;">
                5 explicit reasoning steps.<br>Forces structured thinking.<br>
                <b>Deepest explanation</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    comparison_question = st.text_input(
        "💭 Topic to Compare:",
        placeholder="e.g., recursion, the French Revolution, Newton's laws, overfitting...",
        help="The AI will auto-detect the domain and pick relevant few-shot examples"
    )

    if st.button("🚀 Run Comparison", use_container_width=True, key="compare_btn"):
        if not comparison_question:
            st.warning("⚠️ Please enter a topic for comparison!")
        else:
            try:
                zero_prompt, few_prompt, cot_prompt_text, detected_domain = \
                    build_comparison_prompts(comparison_question)

                domain_icons = {
                    "programming": "💻", "history": "📜", "math": "📐",
                    "biology": "🧬", "physics": "⚛️",
                    "ai_ml": "🤖", "general": "🌐"
                }
                d_icon = domain_icons.get(detected_domain, "🌐")
                st.markdown(f"""
                <div style="background:rgba(245,158,11,0.1); border:1px solid #f59e0b;
                            border-radius:8px; padding:10px 14px; margin:8px 0;
                            color:#fcd34d; font-size:0.9rem; font-weight:600;">
                    {d_icon} Domain auto-detected: <b>{detected_domain.replace('_',' ').title()}</b>
                    - Few-shot examples will use {detected_domain.replace('_',' ')} context
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("🟢 Running Zero-Shot..."):
                    zero_response = generate_response(zero_prompt)
                with st.spinner("🔵 Running Few-Shot..."):
                    few_response = generate_response(few_prompt)
                with st.spinner("🟣 Running Chain-of-Thought..."):
                    cot_response = generate_response(cot_prompt_text)

                st.markdown("---")
                st.markdown("### 📊 Comparison Results")

                st.markdown("""
                <div class="comparison-card">
                    <div class="comparison-header">🟢 1. Zero-Shot Prompt</div>
                    <p style="color:#94a3b8; margin-bottom:0.5rem; font-size:0.9rem;">
                        <i>Minimal prompt - no examples, no structure hints.
                        Tests the AI's raw baseline knowledge.</i>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                render_response(zero_response)

                st.markdown(f"""
                <div class="comparison-card">
                    <div class="comparison-header">🔵 2. Few-Shot Prompt</div>
                    <p style="color:#94a3b8; margin-bottom:0.5rem; font-size:0.9rem;">
                        <i>2 domain-specific examples provided ({detected_domain.replace('_',' ')} context).
                        AI mirrors the example style and structure.</i>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                render_response(few_response)

                st.markdown("""
                <div class="comparison-card">
                    <div class="comparison-header">🟣 3. Chain-of-Thought Prompt</div>
                    <p style="color:#94a3b8; margin-bottom:0.5rem; font-size:0.9rem;">
                        <i>5 explicit reasoning steps forced.
                        Produces the most structured and thorough explanation.</i>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                render_response(cot_response)

                st.markdown("""
                <div class="success-box">
                    💡 <b>What to observe across the 3 responses:</b><br><br>
                    🟢 <b>Zero-Shot</b> - shortest, most direct. Good for simple facts.<br>
                    🔵 <b>Few-Shot</b> - structured and example-driven. Most consistent format.<br>
                    🟣 <b>Chain-of-Thought</b> - deepest reasoning. Best for complex topics.
                </div>
                """, unsafe_allow_html=True)

                comparison_text = f"""PROMPT COMPARISON RESULTS
Topic: {comparison_question}
Domain Detected: {detected_domain}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}
TECHNIQUE 1: ZERO-SHOT
{'='*80}
{zero_response}

{'='*80}
TECHNIQUE 2: FEW-SHOT (domain: {detected_domain})
{'='*80}
{few_response}

{'='*80}
TECHNIQUE 3: CHAIN-OF-THOUGHT
{'='*80}
{cot_response}
"""

                pdf_bytes = generate_pdf(
                    title=f"Prompt Comparison: {comparison_question}",
                    content_dict={
                        "Topic": comparison_question,
                        "Domain Detected": detected_domain.replace('_',' ').title(),
                        "Techniques": "Zero-Shot vs Few-Shot vs Chain-of-Thought",
                        "Date": datetime.now().strftime("%B %d, %Y"),
                        "content": comparison_text
                    }
                )
                
                if pdf_bytes:
                    st.download_button(
                        "📥 Download Comparison Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"clariva_comparison_{comparison_question.replace(' ','_')[:30]}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Please check your API configuration or try again.")

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem 0;">
    <p style="font-size: 1.1rem; margin: 0; font-weight: 600;">
        🎓 <b>Clariva</b> • Powered by Google Gemini
    </p>
    <p style="font-size: 0.95rem; margin-top: 0.75rem; color: #94a3b8;">
        Your Intelligent Learning Companion • All Features Implemented
        <br>
        © 2026 Ersa Dara Aprillia
    </p>
</div>
""", unsafe_allow_html=True)