
import numpy as np, pandas as pd
from scipy.stats import norm
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LinearRegression

numeric_features = ["Hours Studied", "Previous Scores", "Sleep Hours", "Sample Question Papers Practiced"]
categorical_features = ["Extracurricular Activities"]
features = numeric_features + categorical_features


class RegressionThresholdClassifier(BaseEstimator, ClassifierMixin):
    """Predict the score with linear regression, then cut it at low / high into 3 categories."""
    def __init__(self, pi_lookup=None, low=40, high=70):
        self.pi_lookup, self.low, self.high = pi_lookup, low, high
    def _prep(self, X):
        Z = X[numeric_features].astype(float).copy()
        Z["Extracurricular"] = (X["Extracurricular Activities"] == "Yes").astype(float)
        return Z
    def fit(self, X, y=None):
        Z = self._prep(X)
        target = self.pi_lookup.loc[X.index].values
        self.reg_ = LinearRegression().fit(Z, target)
        self.sigma_ = (target - self.reg_.predict(Z)).std(ddof=Z.shape[1] + 1)
        self.classes_ = np.array(["At Risk", "Average", "High Performance"])
        self.feat_names_ = list(Z.columns)
        w = np.abs(self.reg_.coef_ * Z.std().values)
        self.feature_importances_ = w / w.sum()
        return self
    def predict_proba(self, X):
        mu = self.reg_.predict(self._prep(X))
        p_low = norm.cdf((self.low - mu) / self.sigma_)
        p_high = 1 - norm.cdf((self.high - mu) / self.sigma_)
        return np.column_stack([p_low, 1 - p_low - p_high, p_high])
    def predict(self, X):
        mu = self.reg_.predict(self._prep(X))
        return np.where(mu < self.low, "At Risk", np.where(mu < self.high, "Average", "High Performance"))


def priority(p):
    return "High" if p >= 0.85 else ("Medium" if p >= 0.6 else "Watch")


def recommend(r):
    s, why = [], []
    if r["Previous Scores"] < 60: s.append("Extra tutoring"); why.append("low previous scores")
    if r["Hours Studied"] < 4: s.append("Personalized study plan"); why.append("low study hours")
    if r["Sample Question Papers Practiced"] < 3: s.append("Assign practice questions"); why.append("little practice")
    if r["Sleep Hours"] < 6: s.append("Academic advising (sleep / time management)"); why.append("short sleep")
    if not s: s, why = ["Academic advising"], ["borderline profile"]
    return pd.Series({"Recommended_Support": "; ".join(s), "Key_Risk_Factors": ", ".join(why)})


def predict_student(model, row: dict):
    """row = {"Hours Studied":..,"Previous Scores":..,"Sleep Hours":..,
              "Sample Question Papers Practiced":..,"Extracurricular Activities":"Yes"/"No"}
       returns dict with category, probabilities, priority, support, factors."""
    X = pd.DataFrame([row])[features]
    proba = model.predict_proba(X)[0]
    classes = list(model.classes_)
    p_risk = float(proba[classes.index("At Risk")])
    cat = str(classes[int(np.argmax(proba))])
    rec = recommend(X.iloc[0])
    return {"category": cat, "risk_probability": round(p_risk, 3),
            "probabilities": {str(c): round(float(p), 3) for c, p in zip(classes, proba)},
            "priority": priority(p_risk) if cat == "At Risk" else ("Watch" if p_risk >= 0.3 else "OK"),
            "recommended_support": rec["Recommended_Support"], "key_risk_factors": rec["Key_Risk_Factors"]}
