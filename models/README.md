# ML Models Directory

This directory contains the trained machine learning models for the crop monitoring system.

## Required Model Files:

1. **crop_health_classifier.pkl** - RandomForest classifier for crop health prediction
   - Classes: ['Healthy', 'Stressed', 'Critical', 'Dead']
   - Features: 13 environmental and temporal parameters
   - Input: Feature vector (1, 13)
   - Output: Class prediction + probabilities

2. **yield_regressor.pkl** - RandomForest regressor for yield prediction
   - Target: Crop yield (units per area)
   - Features: 13 environmental and temporal parameters
   - Input: Feature vector (1, 13)
   - Output: Yield estimate + uncertainty

3. **feature_scaler.pkl** - Feature preprocessing scaler (optional)
   - Type: StandardScaler or MinMaxScaler
   - Purpose: Normalize features for model consistency
   - Input: Raw feature vector
   - Output: Scaled feature vector

## Feature Engineering:

The models expect these 13 features in this exact order:

1. temperature (°C) - Current air temperature
2. humidity (%) - Relative humidity
3. rainfall (mm) - Daily rainfall amount
4. soil_moisture (%) - Volumetric water content
5. soil_temperature (°C) - Root zone temperature
6. soil_ph - Soil pH level
7. soil_ec (dS/m) - Electrical conductivity
8. ndvi - Normalized Difference Vegetation Index
9. wind_speed (m/s) - Wind velocity
10. solar_radiation (W/m²) - Solar energy
11. day_of_year (1-365) - Temporal feature
12. growth_stage (0-1) - Crop phenological stage
13. historical_stress (0-1) - Previous stress index

## Model Training:

Models should be trained with:
- RandomForestClassifier (n_estimators=100, random_state=42)
- RandomForestRegressor (n_estimators=100, random_state=42)
- Cross-validation with time series split
- Feature importance analysis
- Performance metrics: accuracy, F1-score, RMSE

## Deployment:

- Models are loaded using joblib.load()
- Fallback logic handles missing models gracefully
- Feature validation ensures input consistency
- Error handling prevents system crashes
