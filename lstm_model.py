import numpy as np
import streamlit as st

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

def create_sequences(data, look_back=4):
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:i+look_back])
        y.append(data[i+look_back])
    return np.array(X), np.array(y)

def build_lstm():
    if not TF_AVAILABLE:
        raise ImportError("Tensorflow is not available")
    model = keras.Sequential([
        layers.LSTM(32, input_shape=(4, 1), return_sequences=False),
        layers.Dense(16, activation='relu'),
        layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

@st.cache_data(hash_funcs={np.ndarray: lambda x: x.tobytes()})
def train_and_forecast(history: np.ndarray, field: str, metric: str) -> dict:
    """
    history: 12-element numpy array (normalized 0-1)
    Returns: dict with keys:
      forecast: 4-element array (weeks 13-16)
      upper: upper 90% CI
      lower: lower 90% CI
      train_loss: final training loss
      epochs: int
    """
    if not TF_AVAILABLE:
        # Fallback if TF is missing (graceful degradation)
        hist_list = history.tolist()
        preds = []
        c = hist_list[-1]
        for _ in range(4):
            c = c * 0.95
            preds.append(c)
        preds_real = np.array(preds)
        return {
            "forecast": preds_real,
            "upper": preds_real * 1.05,
            "lower": preds_real * 0.95,
            "train_loss": 0.0,
            "epochs": 0
        }
        
    # Normalize
    mn, mx = history.min(), history.max()
    norm = (history - mn) / (mx - mn + 1e-8)
    
    # Augment: create 50 synthetic variants by adding small gaussian noise
    augmented = []
    for _ in range(50):
        noise = np.random.normal(0, 0.02, norm.shape)
        augmented.append(np.clip(norm + noise, 0, 1))
    augmented = np.array(augmented).flatten()
    full = np.concatenate([norm, augmented])
    
    X, y = create_sequences(full, look_back=4)
    if len(X) == 0:
        return {"forecast": np.array([history[-1]]*4), "upper": np.array([history[-1]]*4), "lower": np.array([history[-1]]*4), "train_loss": 0, "epochs": 0}
        
    X = X.reshape(X.shape[0], X.shape[1], 1)
    
    model = build_lstm()
    history_cb = model.fit(X, y, epochs=80, batch_size=16, verbose=0)
    
    # Forecast 4 steps ahead
    window = list(norm[-4:])
    preds = []
    for _ in range(4):
        inp = np.array(window[-4:]).reshape(1,4,1)
        p = model.predict(inp, verbose=0)[0][0]
        preds.append(p)
        window.append(p)
    
    # Denormalize
    preds_real = np.array(preds) * (mx-mn) + mn
    
    # Monte Carlo uncertainty: run 20 forward passes with slight input noise for CI bands
    mc_runs = []
    for _ in range(20):
        window2 = list(norm[-4:])
        run = []
        for _ in range(4):
            noise = np.random.normal(0, 0.01, (1,4,1))
            inp = np.array(window2[-4:]).reshape(1,4,1) + noise
            p = model.predict(inp, verbose=0)[0][0]
            run.append(p)
            window2.append(p)
        mc_runs.append(np.array(run) * (mx-mn) + mn)
    
    mc_runs = np.array(mc_runs)
    # Using 90% CI as requested in user's comment (though code had 95/5, I will use exactly what they provided)
    upper = np.percentile(mc_runs, 95, axis=0)
    lower = np.percentile(mc_runs, 5, axis=0)
    
    return {
        "forecast": preds_real,
        "upper": upper,
        "lower": lower,
        "train_loss": history_cb.history['loss'][-1],
        "epochs": 80
    }
