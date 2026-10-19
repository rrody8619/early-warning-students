# 🎓 Early Warning for At-Risk Students

A Streamlit web app that spots students who may struggle in the exam, so advisors can offer support **before** it is too late.

🔗 **Live demo:** _add your Streamlit link here_ (e.g. `https://early-warning-students.streamlit.app`)

---

## What it does

- **Check a student**: enter a student's profile and get an instant prediction, the risk probability, a priority level, and recommended support.
- **At-risk list**: browse all flagged students, filter by priority, minimum risk probability, or student ID, and download the current view as CSV.
- **Watch-list**: see borderline students who are not flagged yet but deserve attention.
- **Dashboard summary**: total students analysed, number flagged at-risk, and size of the watch-list.

## How it works

The model is a **regression → threshold** classifier (`RegressionThresholdClassifier` in `app_utils.py`):

1. A linear regression predicts the student's **Performance Index**.
2. The predicted score is cut into three categories:
   - **At Risk**: below 40
   - **Average**: 40 to 70
   - **High Performance**: from 70
3. Class probabilities come from the regression's error (normal distribution), which gives each student a **risk probability**.

### Priority levels

| Risk probability | Priority |
|---|---|
| 0.85 or more | **High** |
| 0.60 to 0.85 | **Medium** |
| below 0.60 | **Watch** |

### Input features

| Feature | Range |
|---|---|
| Hours Studied (per day) | 1 to 9 |
| Previous Scores | 40 to 99 |
| Sleep Hours (per night) | 4 to 9 |
| Sample Question Papers Practiced | 0 to 9 |
| Extracurricular Activities | Yes / No |

### Recommended support

Based on the student's profile, the app suggests actions such as extra tutoring, a personalized study plan, practice questions, or academic advising (sleep / time management), and lists the key risk factors behind the suggestion.

## Project structure

```
.
├── App.py                      # Streamlit app (UI)
├── app_utils.py                # Model class, priority rules, recommendations
├── final_model.joblib          # Trained model
├── model_meta.json             # Model metadata
├── all_students_scored.csv     # All students with risk scores
├── at_risk_students_final.csv  # Students flagged as at-risk
├── watch_list_students.csv     # Borderline students
└── requirements.txt            # Python dependencies
```

## Run locally

```bash
# 1. Clone the repo
git clone https://github.com/rrody8619/early-warning-students.git
cd early-warning-students

# 2. (Optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the app
streamlit run App.py
```

Then open <http://localhost:8501>.

> **Note:** `app_utils.py` must stay in the same folder as `App.py`, because the saved model depends on the `RegressionThresholdClassifier` class defined there.

## Tech stack

Python · Streamlit · scikit-learn · pandas · NumPy · SciPy · joblib

## Disclaimer

This tool is meant to **support** advisors, not replace them. Predictions are statistical estimates and should be used together with human judgment when deciding how to help a student.
