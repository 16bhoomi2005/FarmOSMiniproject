import pandas as pd
import numpy as np
import os
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ─── Configuration ────────────────────────────────────────────────────────────
DATA_FILE = 'training_dataset.csv'
MODEL_FILE = 'models/rice_risk_model.pkl'
MIN_SAMPLES = 20  # You need at least this many rows to start training

def train_risk_engine():
    """
    Trains a Random Forest classifier based on historical field data.
    Features used: NDVI, Temp, Humidity, Growth Stage, Days After Transplant.
    Target: Condition Label.
    """
    if not os.path.exists(DATA_FILE):
        print(f"❌ Dataset not found at {DATA_FILE}. Start loggging observations first!")
        return

    df = pd.read_csv(DATA_FILE)
    
    if len(df) < MIN_SAMPLES:
        print(f"⚠️ Not enough data yet ({len(df)}/{MIN_SAMPLES} samples). Continue logging field observations daily.")
        return

    print(f"🤖 Training Level 3 Intelligence Engine on {len(df)} samples...")

    # 1. Preprocessing: Convert categorical data to numbers
    # We use simpler encoding for this starter template
    df['stage_code'] = df['growth_stage'].astype('category').cat.codes
    
    # Feature selection
    features = ['ndvi', 'temp', 'humidity', 'days_after_transplant', 'stage_code']
    X = df[features]
    y = df['label']

    # 2. Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Train Model
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # 4. Evaluate
    y_pred = model.predict(X_test)
    print("\n📊 Model Performance:")
    print(classification_report(y_test, y_pred))

    # 5. Save Model
    os.makedirs('models', exist_ok=True)
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"\n✅ Level 3 Model saved to: {MODEL_FILE}")
    print("Dashboard will now use this model for real-time predictions!")

if __name__ == "__main__":
    train_risk_engine()
