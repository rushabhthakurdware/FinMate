import numpy as np
from sklearn.ensemble import RandomForestClassifier
from typing import Tuple, List, Dict
from app.schemas.risk import RiskFormInput

class RiskClassifierService:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self._train_synthetic_model()

    def _train_synthetic_model(self):
        """Train a lightweight ML model on synthetic personal finance data points."""
        np.random.seed(42)
        N = 1000
        
        # Features: [age, emi_ratio, savings_months, dependents, horizon_years]
        ages = np.random.randint(18, 65, N)
        emi_ratios = np.random.uniform(0, 0.7, N)
        savings_months = np.random.uniform(0, 24, N)
        dependents = np.random.randint(0, 5, N)
        horizons = np.random.randint(1, 30, N)

        X = np.column_stack([ages, emi_ratios, savings_months, dependents, horizons])
        y = []

        for i in range(N):
            # Rule base ground truth generation for synthetic training
            score = 50
            score -= (ages[i] - 25) * 0.5
            score -= emi_ratios[i] * 40
            score += min(savings_months[i], 12) * 2.5
            score -= dependents[i] * 5
            score += horizons[i] * 1.5

            if score < 40:
                y.append("Conservative")
            elif score < 65:
                y.append("Moderate")
            else:
                y.append("Aggressive")

        self.model.fit(X, y)

    def evaluate_risk(self, data: RiskFormInput) -> Tuple[float, str, List[str]]:
        # Compute financial ratios
        emi_ratio = data.emi_amount / data.monthly_income if data.monthly_income > 0 else 0
        savings_months = data.savings / data.monthly_income if data.monthly_income > 0 else 0
        
        # Rule-based Scoring (0 to 100 scale)
        base_score = 50.0
        factors = []

        # Age Factor
        if data.age < 30:
            base_score += 15
            factors.append("Younger age increases capacity to recover from market volatility (+15).")
        elif data.age > 50:
            base_score -= 15
            factors.append("Higher age prioritizes capital preservation (-15).")

        # EMI Debt-to-Income Factor
        if emi_ratio > 0.4:
            base_score -= 20
            factors.append(f"High debt obligations ({round(emi_ratio*100, 1)}% EMI ratio) restrict risk capacity (-20).")
        elif emi_ratio < 0.2:
            base_score += 10
            factors.append("Low debt burden allows higher equity allocation (+10).")

        # Emergency Fund Factor
        if savings_months < 3:
            base_score -= 15
            factors.append(f"Low liquidity buffer ({round(savings_months, 1)} months) reduces risk tolerance (-15).")
        elif savings_months >= 6:
            base_score += 10
            factors.append("Healthy emergency fund provides market downturn protection (+10).")

        # Horizon Factor
        if data.horizon_years >= 7:
            base_score += 15
            factors.append(f"Long time horizon ({data.horizon_years} yrs) absorbs short-term volatility (+15).")
        elif data.horizon_years <= 3:
            base_score -= 15
            factors.append("Short horizon necessitates liquidity and capital protection (-15).")

        # Clamp score between 0 and 100
        risk_score = float(np.clip(base_score, 0, 100))

        # ML Model Prediction Verification
        features = np.array([[data.age, emi_ratio, savings_months, data.dependents, data.horizon_years]])
        ml_category = self.model.predict(features)[0]

        # Final Category Decision
        if risk_score < 40:
            category = "Conservative"
        elif risk_score < 65:
            category = "Moderate"
        else:
            category = "Aggressive"

        if ml_category != category and risk_score >= 35 and risk_score <= 70:
            factors.append(f"ML Model recommendation suggests a target profile of '{ml_category}'.")

        return risk_score, category, factors

risk_service = RiskClassifierService()