# 🎓 Clariva AI Smart Tutor
An AI-powered educational assistant developed using Advanced Prompt Engineering Techniques and the Gemini API. This project aims to provide personalized learning support through intelligent tutoring, study planning, quiz generation, answer evaluation, and prompt comparison.

## 📌 Project Overview
Clariva AI Smart Tutor is designed to help learners improve their understanding of various topics through adaptive AI interactions. The system leverages multiple prompt engineering techniques to deliver structured, accurate, and educationally effective responses.
The project was developed as part of the AI Prompt Engineering Capstone Project.

## ✨ Key Features
### 🤖 AI Tutor
Provides clear and structured explanations for any learning topic.
### 📚 Study Plan Generator
Creates personalized study plans based on:
- Learning topic
- Current skill level
- Learning goals
- Study duration
- Daily study time
### 📝 Quiz Generator
Generates multiple-choice quizzes tailored to different learner levels:
- Beginner
- Intermediate
- Advanced
### 🎯 Answer Evaluator
Evaluates student answers using rubric-based assessment and provides constructive feedback.
### 🔍 Prompt Comparison Engine
Compares multiple prompt engineering techniques to analyze response quality and effectiveness.

## 🧠 Prompt Engineering Techniques Implemented
### Zero-Shot Prompting
Generates responses without examples, relying solely on instructions.
### Few-Shot Prompting
Uses example-based prompting to improve response quality and consistency.
### Chain-of-Thought (CoT) Prompting
Encourages step-by-step reasoning before generating the final answer.
### Role-Based Prompting
Assigns expert roles such as:
- EduMind Tutor
- EduMind Examiner
- EduMind Study Coach
### Rubric-Based Prompting
Applies structured assessment criteria for educational evaluation.

## 🏗️ System Architecture
User Input
↓
Streamlit Interface
↓
Prompt Builder Modules
↓
Gemini API
↓
AI Response Processing
↓
Output Display

## 📂 Project Structure
```plaintext
AI-SMART-FIRST/
│
├── app.py
├── style.css
├── .gitignore
│
├── prompts/
│   ├── tutor_prompt.py
│   ├── studyplan_prompt.py
│   ├── quiz_prompt.py
│   ├── evaluator_prompt.py
│   └── comparison_prompt.py
│
├── services/
│   └── gemini_service.py
│
└── assets/
```

## ⚙️ Technologies Used
- Python
- Streamlit
- Google Gemini API
- Prompt Engineering
- HTML/CSS
- Git & GitHub

## 🚀 Installation
### Clone Repository
```bash
git clone https://github.com/ErsaDaraAprillia/Capstone-Clariva-AI-Smart-Tutor.git
```

### Navigate to Project Folder
```bash
cd Capstone-Clariva-AI-Smart-Tutor
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment Variables
Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

### Run Application
```bash
streamlit run app.py
```

## 🎥 Demo Video
👉 [Watch Demo Video](https://drive.google.com/file/d/1CmXtvUvzxFo-j9fGkJFCAnlbcaaFCQ6p/view?usp=drive_link)

## 📊 Presentation Slides
👉 [View Presentation](https://drive.google.com/file/d/1Cvn3XGK30xuQsNrUrkyVE-NCz4jxbaTv/view?usp=drive_link)

## 📑 Project Report
👉 [Read Full Report](https://drive.google.com/file/d/17Ulmq_n7mC48lFGIkdUV6UldS8PUXQaw/view?usp=drive_link)

## 👩‍💻 Developer
**Ersa Dara Aprillia**
AI Prompt Engineering Capstone Project

## 🎯 Project Goal
To demonstrate the practical application of advanced prompt engineering techniques in building an intelligent educational assistant capable of supporting personalized learning experiences.

## 📜 License
This project was developed for educational and academic purposes.
