#!/usr/bin/env python3
"""
Enhanced Hybrid Crop Monitoring System
Improved model performance, additional features, and better ML models
"""

import os
import glob
import pandas as pd
import numpy as np
import rasterio
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, r2_score, mean_squared_error
import joblib

class EnhancedHybridCropMonitoringSystem:
    def __init__(self, sentinel_tile_path="Sentinel_Data", ground_sensor_data_path="sample_ground_sensor_data.csv"):
        self.sentinel_path = sentinel_tile_path
        self.ground_data_path = ground_sensor_data_path
        self.satellite_features = {}
        self.time_series_features = {}
        self.feature_dataset = None
        self.ground_sensor_data = None
        self.models = {}
        self.scaler = None
        self.feature_columns = []
        self.results = {}
        
        print("🌾 Enhanced Hybrid Crop Monitoring System Initialized")
        print("📡 Sentinel-2 Path: " + str(self.sentinel_path))
        print("🌡️ Ground Sensor Path: " + str(self.ground_data_path))
    
    def step1_satellite_feature_extraction(self):
        """Enhanced satellite feature extraction with additional vegetation indices"""
        print("\n🛰️ STEP 1: Enhanced Satellite Feature Extraction")
        print("="*60)
        
        # Find all .SAFE directories
        safe_dirs = sorted(glob.glob(os.path.join(self.sentinel_path, "*.SAFE")))
        print("📊 Found " + str(len(safe_dirs)) + " Sentinel-2 scenes")
        
        if not safe_dirs:
            print("❌ No .SAFE directories found!")
            return False
        
        processed_scenes = 0
        
        for safe_dir in safe_dirs:
            # Extract date from filename
            scene_name = os.path.basename(safe_dir)
            date_str = self._extract_date_from_filename(scene_name)
            
            print("\n📅 Processing Scene " + str(processed_scenes + 1) + "/" + str(len(safe_dirs)) + ": " + str(scene_name))
            
            # Load bands
            bands_data = self._load_sentinel_bands(safe_dir)
            
            if bands_data:
                # Calculate enhanced vegetation indices
                indices = self._calculate_enhanced_vegetation_indices(bands_data)
                
                if indices:
                    self.satellite_features[date_str] = indices
                    print("✅ Enhanced indices calculated for " + str(date_str))
                    print("   NDVI: " + str(indices['NDVI_mean']))
                    print("   SAVI: " + str(indices['SAVI_mean']))
                    print("   NDRE: " + str(indices['NDRE_mean']))
                    print("   GNDVI: " + str(indices['GNDVI_mean']))
                    print("   EVI: " + str(indices['EVI_mean']))
                    processed_scenes += 1
                else:
                    print("❌ Failed to calculate indices for " + str(date_str))
            else:
                print("❌ Failed to load bands for " + str(date_str))
        
        print("\n📈 Successfully processed " + str(processed_scenes) + " scenes")
        return processed_scenes > 0
    
    def _extract_date_from_filename(self, filename):
        """Extract date from Sentinel-2 filename"""
        parts = filename.split('_')
        for part in parts:
            if 'T' in part and len(part) == 15:
                return part[:8]
        return filename[:8]
    
    def _load_sentinel_bands(self, safe_dir):
        """Load Sentinel-2 bands with enhanced pattern matching"""
        bands_data = {}
        
        # Multiple pattern attempts for different .SAFE structures
        pattern_sets = [
            {
                'B2': f"GRANULE/*/IMG_DATA/R10m/*_B02_10m.jp2",
                'B3': f"GRANULE/*/IMG_DATA/R10m/*_B03_10m.jp2",
                'B4': f"GRANULE/*/IMG_DATA/R10m/*_B04_10m.jp2",
                'B5': f"GRANULE/*/IMG_DATA/R20m/*_B05_20m.jp2", 
                'B8': f"GRANULE/*/IMG_DATA/R10m/*_B08_10m.jp2"
            },
            {
                'B2': f"**/*_B02_10m.jp2",
                'B3': f"**/*_B03_10m.jp2",
                'B4': f"**/*_B04_10m.jp2",
                'B5': f"**/*_B05_20m.jp2", 
                'B8': f"**/*_B08_10m.jp2"
            }
        ]
        
        for pattern_set in pattern_sets:
            success = True
            for band, pattern in pattern_set.items():
                try:
                    band_files = glob.glob(os.path.join(safe_dir, pattern))
                    if band_files:
                        with rasterio.open(band_files[0]) as src:
                            bands_data[band] = src.read(1).astype(np.float32)
                        print(f"   ✅ Loaded {band}: {os.path.basename(band_files[0])}")
                    else:
                        success = False
                        break
                except Exception as e:
                    success = False
                    break
            
            if success:
                break
        
        if not bands_data:
            print(f"   ❌ No bands found in {safe_dir}")
            return None
        
        # Resample B5 to match B4/B8 resolution if needed
        if bands_data['B5'].shape != bands_data['B4'].shape:
            from scipy import ndimage
            scale_factor = 2
            bands_data['B5'] = ndimage.zoom(bands_data['B5'], scale_factor, order=1)
            print(f"   🔄 Resampled B5 to match resolution")
        
        return bands_data
    
    def _calculate_enhanced_vegetation_indices(self, bands_data):
        """Calculate enhanced vegetation indices using correct spectral bands"""
        B2 = bands_data['B2']  # Blue
        B3 = bands_data['B3']  # Green
        B4 = bands_data['B4']  # Red
        B5 = bands_data['B5']  # Red Edge
        B8 = bands_data['B8']  # NIR
        
        # Avoid division by zero
        denominator = B8 + B4
        denominator[denominator == 0] = 1e-8
        
        # NDVI
        ndvi = (B8 - B4) / denominator
        
        # SAVI
        savi_denominator = B8 + B4 + 0.5
        savi_denominator[savi_denominator == 0] = 1e-8
        savi = ((B8 - B4) / savi_denominator) * 1.5
        
        # NDRE
        ndre_denominator = B8 + B5
        ndre_denominator[ndre_denominator == 0] = 1e-8
        ndre = (B8 - B5) / ndre_denominator
        
        # GNDVI (Green NDVI) - Uses Green (B3) and NIR (B8)
        gndvi_denominator = B8 + B3
        gndvi_denominator[gndvi_denominator == 0] = 1e-8
        gndvi = (B8 - B3) / gndvi_denominator
        
        # EVI (Enhanced Vegetation Index) - Standard Formula using Blue (B2)
        # EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))
        evi_denominator = B8 + 6*B4 - 7.5*B2 + 1
        evi_denominator[evi_denominator == 0] = 1e-8
        evi = 2.5 * (B8 - B4) / evi_denominator
        
        # Valid mask
        valid_mask = (ndvi > -1) & (ndvi < 1) & (savi > -1) & (savi < 1) & \
                    (ndre > -1) & (ndre < 1) & (gndvi > -1) & (gndvi < 1) & \
                    (evi > -1) & (evi < 1)
        
        indices = {
            'NDVI_mean': np.mean(ndvi[valid_mask]),
            'NDVI_std': np.std(ndvi[valid_mask]),
            'SAVI_mean': np.mean(savi[valid_mask]),
            'NDRE_mean': np.mean(ndre[valid_mask]),
            'GNDVI_mean': np.mean(gndvi[valid_mask]),
            'EVI_mean': np.mean(evi[valid_mask])
        }
        
        # Save latest features for dashboard
        self._save_latest_features(indices)
        
        return indices

    def _save_latest_features(self, indices):
        """Save latest satellite features for dashboard display"""
        try:
            # Convert numpy types to float for JSON serialization
            serializable_indices = {k: float(v) for k, v in indices.items()}
            import json
            with open('latest_satellite_features.json', 'w') as f:
                json.dump(serializable_indices, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save latest features: {e}")
    
    def step2_enhanced_time_series_engineering(self):
        """Enhanced time-series feature engineering with temporal patterns"""
        print("\n📈 STEP 2: Enhanced Time-Series Feature Engineering")
        print("="*60)
        
        if len(self.satellite_features) < 2:
            print("❌ Need at least 2 dates for time-series analysis!")
            return False
        
        # Sort by date
        dates = sorted(self.satellite_features.keys())
        print("📅 Time range: " + str(dates[0]) + " to " + str(dates[-1]))
        
        # Extract time series for each index
        ndvi_series = [self.satellite_features[date]['NDVI_mean'] for date in dates]
        savi_series = [self.satellite_features[date]['SAVI_mean'] for date in dates]
        ndre_series = [self.satellite_features[date]['NDRE_mean'] for date in dates]
        gndvi_series = [self.satellite_features[date]['GNDVI_mean'] for date in dates]
        evi_series = [self.satellite_features[date]['EVI_mean'] for date in dates]
        
        # Enhanced temporal features
        features = {}
        
        # Basic statistics for each index
        for idx_name, series in [('NDVI', ndvi_series), ('SAVI', savi_series), 
                                ('NDRE', ndre_series), ('GNDVI', gndvi_series), 
                                ('EVI', evi_series)]:
            features[f'{idx_name}_mean'] = np.mean(series)
            features[f'{idx_name}_max'] = np.max(series)
            features[f'{idx_name}_min'] = np.min(series)
            features[f'{idx_name}_std'] = np.std(series)
        
        # NDVI-specific temporal features
        features['NDVI_slope'] = self._calculate_trend_slope(ndvi_series)
        features['NDVI_last_value'] = ndvi_series[-1]
        features['NDVI_peak_value'] = np.max(ndvi_series)
        features['Day_of_peak_NDVI'] = dates[np.argmax(ndvi_series)]
        
        # Moving averages (3-period and 7-period)
        if len(ndvi_series) >= 3:
            features['NDVI_ma3'] = np.mean(ndvi_series[-3:])
            features['NDVI_ma7'] = np.mean(ndvi_series) if len(ndvi_series) >= 7 else np.mean(ndvi_series)
        
        # Growth rate features
        features['NDVI_growth_rate'] = (ndvi_series[-1] - ndvi_series[0]) / len(ndvi_series)
        features['NDVI_volatility'] = np.std(np.diff(ndvi_series))
        
        # Multi-index correlations
        features['NDVI_SAVI_correlation'] = np.corrcoef(ndvi_series, savi_series)[0,1] if len(ndvi_series) > 1 else 0
        features['NDVI_EVI_correlation'] = np.corrcoef(ndvi_series, evi_series)[0,1] if len(ndvi_series) > 1 else 0
        
        self.time_series_features = features
        
        print(f"📈 Enhanced Time-Series Features:")
        for feature, value in features.items():
            if isinstance(value, (int, float)):
                print(f"  {feature}: {value:.4f}")
            else:
                print(f"  {feature}: {value}")
        
        return True
    
    def _calculate_trend_slope(self, series):
        """Calculate linear trend slope"""
        if len(series) < 2:
            return 0
        x = np.arange(len(series))
        return np.polyfit(x, series, 1)[0]
    
    def step3_merge_with_ground_sensors(self):
        """Merge enhanced satellite features with ground sensor data"""
        print("\n🌡️ STEP 3: Enhanced Ground Sensor Integration")
        print("="*60)
        
        # Load ground sensor data
        try:
            self.ground_sensor_data = pd.read_csv(self.ground_data_path)
            print("📊 Ground sensor data shape: " + str(self.ground_sensor_data.shape))
            print("📋 Columns: " + str(list(self.ground_sensor_data.columns)))
        except Exception as e:
            print("❌ Error loading ground sensor data: " + str(e))
            return False
        
        # Calculate enhanced ground sensor features
        ground_features = {
            'Temperature_mean': self.ground_sensor_data['Temperature'].mean(),
            'Temperature_std': self.ground_sensor_data['Temperature'].std(),
            'Temperature_max': self.ground_sensor_data['Temperature'].max(),
            'Temperature_min': self.ground_sensor_data['Temperature'].min(),
            'Humidity_mean': self.ground_sensor_data['Humidity'].mean(),
            'Humidity_std': self.ground_sensor_data['Humidity'].std(),
            'Soil_Moisture_mean': self.ground_sensor_data['Soil_Moisture'].mean(),
            'Soil_Moisture_std': self.ground_sensor_data['Soil_Moisture'].std(),
            'Soil_Moisture_max': self.ground_sensor_data['Soil_Moisture'].max(),
            'Soil_Moisture_min': self.ground_sensor_data['Soil_Moisture'].min(),
            # New Season 2 Sensors
            'Soil_pH_mean': self.ground_sensor_data['Soil_pH'].mean(),
            'Soil_pH_std': self.ground_sensor_data['Soil_pH'].std(),
            'Soil_Temperature_mean': self.ground_sensor_data['Soil_Temperature'].mean(),
            'Soil_Temperature_std': self.ground_sensor_data['Soil_Temperature'].std(),
            'Light_Intensity_mean': self.ground_sensor_data['Light_Intensity'].mean(),
            'Light_Intensity_std': self.ground_sensor_data['Light_Intensity'].std()
        }
        
        print("\n🌡️ Enhanced Ground Sensor Features:")
        for feature, value in ground_features.items():
            if isinstance(value, (int, float)):
                print(f"  {feature}: {value:.2f}")
            else:
                print(f"  {feature}: {value}")
        
        # Ensure time_series_features exists
        if not hasattr(self, 'time_series_features'):
            print("⚠️ No satellite features found, creating enhanced synthetic data...")
            self.time_series_features = self._create_enhanced_synthetic_features()
        
        # Combine all features
        all_features = {**ground_features, **self.time_series_features}
        
        # Create feature dataset
        self.feature_dataset = pd.DataFrame([all_features])
        
        # Add targets
        if 'Crop_Health' in self.ground_sensor_data.columns:
            self.feature_dataset['Crop_Health'] = self.ground_sensor_data['Crop_Health'].iloc[0]
        
        if 'Yield' in self.ground_sensor_data.columns:
            self.feature_dataset['Yield'] = self.ground_sensor_data['Yield'].iloc[0]
        
        print("\n✅ Enhanced feature dataset shape: " + str(self.feature_dataset.shape))
        print("📋 Total features: " + str(len(all_features)))
        
        return True
    
    def _create_enhanced_synthetic_features(self):
        """Create enhanced synthetic features for testing"""
        features = {}
        
        # Vegetation indices
        for idx in ['NDVI', 'SAVI', 'NDRE', 'GNDVI', 'EVI']:
            base_val = np.random.normal(0.6, 0.1)
            features[f'{idx}_mean'] = base_val
            features[f'{idx}_max'] = base_val + np.random.normal(0.2, 0.05)
            features[f'{idx}_min'] = base_val - np.random.normal(0.2, 0.05)
            features[f'{idx}_std'] = np.random.normal(0.1, 0.02)
        
        # Temporal features
        features['NDVI_slope'] = np.random.normal(0.01, 0.005)
        features['NDVI_last_value'] = np.random.normal(0.65, 0.08)
        features['NDVI_peak_value'] = np.random.normal(0.75, 0.06)
        features['Day_of_peak_NDVI'] = np.random.randint(100, 200)
        features['NDVI_ma3'] = np.random.normal(0.6, 0.08)
        features['NDVI_ma7'] = np.random.normal(0.6, 0.08)
        features['NDVI_growth_rate'] = np.random.normal(0.01, 0.005)
        features['NDVI_volatility'] = np.random.normal(0.05, 0.01)
        features['NDVI_SAVI_correlation'] = np.random.normal(0.8, 0.1)
        features['NDVI_EVI_correlation'] = np.random.normal(0.7, 0.1)
        
        return features
    
    def step4_enhanced_model_training(self):
        """Enhanced model training with hyperparameter tuning"""
        print("\n🤖 STEP 4: Enhanced Model Training with Hyperparameter Tuning")
        print("="*60)
        
        if self.feature_dataset is None or len(self.feature_dataset) == 0:
            print("❌ No feature dataset available!")
            return False
        
        # Prepare features and targets
        feature_cols = [col for col in self.feature_dataset.columns 
                      if col not in ['Crop_Health', 'Yield']]
        
        X = self.feature_dataset[feature_cols]
        y_health = self.feature_dataset.get('Crop_Health')
        y_yield = self.feature_dataset.get('Yield')
        
        # Create expanded synthetic dataset for better training
        print("📊 Creating expanded synthetic training dataset...")
        X_expanded, y_health_expanded, y_yield_expanded = self._create_expanded_dataset(X, y_health, y_yield)
        
        print("📊 Training set size: " + str(len(X_expanded)))
        
        # Split data
        X_train, X_test, y_h_train, y_h_test = train_test_split(
            X_expanded, y_health_expanded, test_size=0.2, random_state=42, stratify=y_health_expanded)
        
        X_train_r, X_test_r, y_y_train, y_y_test = train_test_split(
            X_expanded, y_yield_expanded, test_size=0.2, random_state=42)
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        X_train_r_scaled = self.scaler.transform(X_train_r)
        X_test_r_scaled = self.scaler.transform(X_test_r)
        
        # Enhanced Crop Health Classifier with hyperparameter tuning
        print("\n🌾 Training Enhanced Crop Health Classifier...")
        health_model = self._train_health_classifier(X_train_scaled, y_h_train, X_test_scaled, y_h_test)
        
        # Enhanced Yield Regressor with hyperparameter tuning
        print("\n📊 Training Enhanced Yield Regressor...")
        yield_model = self._train_yield_regressor(X_train_r_scaled, y_y_train, X_test_r_scaled, y_y_test)
        
        # Store models and results
        self.models = {
            'health_classifier': health_model,
            'yield_regressor': yield_model
        }
        
        self.feature_columns = feature_cols
        
        # Save models
        self._save_enhanced_models()
        
        return True
    
    def _create_expanded_dataset(self, X, y_health, y_yield):
        """Create expanded synthetic dataset for better model training"""
        np.random.seed(42)
        n_samples = 200  # Much larger dataset
        
        X_expanded = []
        y_health_expanded = []
        y_yield_expanded = []
        
        # Create synthetic variations using robust approach
        for _ in range(n_samples):
            sample = {}
            for col in X.columns:
                # Convert to numeric numpy array with explicit dtype
                col_array = np.array(X[col], dtype=float)
                noise_factor = 0.1 if 'std' in col else 0.05
                # Create element-wise noise for each element
                noise = np.random.normal(1.0, noise_factor, size=col_array.shape)
                sample[col] = col_array * noise  # element-wise multiplication
            
            X_expanded.append(pd.DataFrame(sample))
            if y_health is not None:
                y_health_expanded.append(y_health.copy())
            if y_yield is not None:
                y_yield_expanded.append(y_yield.copy())
        
        # Concatenate all expanded samples into single dataframe/series
        X_expanded = pd.concat(X_expanded, ignore_index=True)
        if y_health is not None:
            y_health_expanded = pd.concat(y_health_expanded, ignore_index=True)
        else:
            y_health_expanded = None
        if y_yield is not None:
            y_yield_expanded = pd.concat(y_yield_expanded, ignore_index=True)
        else:
            y_yield_expanded = None
        
        # Generate synthetic targets
        if y_health is not None:
            # Create realistic crop health classes based on NDVI and other indicators
            health_scores = []
            for _, row in X_expanded.iterrows():
                ndvi = row.get('NDVI_mean', 0.5)
                savi = row.get('SAVI_mean', 0.5)
                evi = row.get('EVI_mean', 0.5)
                
                # Simple health classification logic
                health_score = (ndvi + savi + evi) / 3
                if health_score > 0.7:
                    health_scores.append(3)  # Excellent
                elif health_score > 0.5:
                    health_scores.append(2)  # Good
                elif health_score > 0.3:
                    health_scores.append(1)  # Fair
                else:
                    health_scores.append(0)  # Poor
            
            y_health_expanded = health_scores
        else:
            y_health_expanded = None
        
        if y_yield is not None:
            # Create realistic yield based on vegetation indices and conditions
            yield_scores = []
            for _, row in X_expanded.iterrows():
                ndvi = row.get('NDVI_mean', 0.5)
                temp = row.get('Temperature_mean', 25)
                moisture = row.get('Soil_Moisture_mean', 50)
                
                # Simple yield model
                base_yield = 60
                ndvi_factor = (ndvi - 0.3) * 100  # NDVI contribution
                temp_factor = max(0, 1 - abs(temp - 25) / 20)  # Optimal temp ~25°C
                moisture_factor = moisture / 100  # Moisture contribution
                
                yield_score = base_yield + ndvi_factor * 10 + temp_factor * 20 + moisture_factor * 15
                yield_score += np.random.normal(0, 5)  # Natural variation
                
                # Fixed: remove extra parenthesis
                final_yield = max(20, min(100, yield_score))
                yield_scores.append(final_yield)
            
            y_yield_expanded = yield_scores
        else:
            y_yield_expanded = None
        
        return X_expanded, y_health_expanded, y_yield_expanded
    
    def _train_health_classifier(self, X_train, y_train, X_test, y_test):
        """Train enhanced crop health classifier with hyperparameter tuning"""
        # Define parameter grid
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        # Create and tune Random Forest
        rf = RandomForestClassifier(random_state=42)
        grid_search = GridSearchCV(rf, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        
        # Evaluate
        y_pred = best_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print("✅ Best parameters: " + str(grid_search.best_params_))
        print("✅ Crop Health Accuracy: " + str(accuracy))
        print("📋 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        self.results['health_accuracy'] = accuracy
        self.results['health_best_params'] = grid_search.best_params_
        
        return best_model
    
    def _train_yield_regressor(self, X_train, y_train, X_test, y_test):
        """Train enhanced yield regressor with hyperparameter tuning"""
        # Define parameter grid
        param_grid = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7]
        }
        
        # Create and tune Gradient Boosting
        gb = GradientBoostingRegressor(random_state=42)
        grid_search = GridSearchCV(gb, param_grid, cv=3, scoring='r2', n_jobs=-1)
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        
        # Evaluate
        y_pred = best_model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        print("✅ Best parameters: " + str(grid_search.best_params_))
        print("✅ Yield R² Score: " + str(r2))
        print("✅ Yield RMSE: " + str(rmse))
        
        self.results['yield_r2'] = r2
        self.results['yield_rmse'] = rmse
        self.results['yield_best_params'] = grid_search.best_params_
        
        return best_model
    
    def _save_enhanced_models(self):
        """Save enhanced models and metadata"""
        os.makedirs('models', exist_ok=True)
        
        # Save models
        joblib.dump(self.models['health_classifier'], 'models/enhanced_health_classifier.pkl')
        joblib.dump(self.models['yield_regressor'], 'models/enhanced_yield_regressor.pkl')
        joblib.dump(self.scaler, 'models/enhanced_feature_scaler.pkl')
        
        # Save feature columns and results
        with open('models/enhanced_feature_columns.txt', 'w') as f:
            for col in self.feature_columns:
                f.write(f"{col}\n")
        
        # Save results summary
        with open('models/enhanced_model_results.txt', 'w') as f:
            f.write("Enhanced Model Results\n")
            f.write("="*30 + "\n")
            for key, value in self.results.items():
                f.write(f"{key}: {value}\n")
        
        print("\n💾 Enhanced models saved to models/")
        print("   - enhanced_health_classifier.pkl")
        print("   - enhanced_yield_regressor.pkl")
        print("   - enhanced_feature_scaler.pkl")
        print("   - enhanced_feature_columns.txt")
        print("   - enhanced_model_results.txt")

def create_sample_data():
    """Create enhanced sample ground sensor data"""
    np.random.seed(42)
    dates = pd.date_range('2023-03-01', periods=100, freq='D')
    
    data = {
        'Date': dates,
        'Temperature': np.random.normal(28, 5, 100),
        'Humidity': np.random.normal(65, 15, 100),
        'Soil_Moisture': np.random.normal(55, 10, 100),
        'Crop_Health': np.random.randint(0, 4, 100),
        'Yield': np.random.normal(60, 15, 100),
        # New Season 2 Sensors
        'Soil_pH': np.random.normal(6.5, 0.5, 100),
        'Soil_Temperature': np.random.normal(22, 5, 100),
        'Light_Intensity': np.random.normal(800, 100, 100)
    }
    
    df = pd.DataFrame(data)
    df['Temperature'] = np.clip(df['Temperature'], 15, 40)
    df['Humidity'] = np.clip(df['Humidity'], 30, 90)
    df['Soil_Moisture'] = np.clip(df['Soil_Moisture'], 10, 80)
    df['Yield'] = np.clip(df['Yield'], 20, 100)
    df['Soil_pH'] = np.clip(df['Soil_pH'], 5.0, 8.5)
    df['Soil_Temperature'] = np.clip(df['Soil_Temperature'], 10, 35)
    df['Light_Intensity'] = np.clip(df['Light_Intensity'], 200, 1200)
    
    df.to_csv('sample_ground_sensor_data.csv', index=False)
    print("✅ Enhanced sample ground sensor data saved to 'sample_ground_sensor_data.csv'")

def main():
    """Main function to run the enhanced hybrid crop monitoring system"""
    print("🌾 ENHANCED FUTURE-READY HYBRID CROP MONITORING SYSTEM")
    print("="*70)
    print("Combining Sentinel-2 satellite data with ground sensors")
    print("Enhanced with additional vegetation indices and improved ML models")
    print("="*70)
    
    # Create sample data
    create_sample_data()
    
    # Initialize enhanced system
    system = EnhancedHybridCropMonitoringSystem(
        sentinel_tile_path="Sentinel_Data",
        ground_sensor_data_path="sample_ground_sensor_data.csv"
    )
    
    # Run enhanced pipeline
    success = True
    
    # Step 1: Enhanced satellite feature extraction
    if not system.step1_satellite_feature_extraction():
        success = False
    
    # Step 2: Enhanced time-series engineering
    if not system.step2_enhanced_time_series_engineering():
        success = False
    
    # Step 3: Enhanced ground sensor integration
    if not system.step3_merge_with_ground_sensors():
        success = False
    
    # Step 4: Enhanced model training
    if not system.step4_enhanced_model_training():
        success = False
    
    if success:
        print("\n" + "="*70)
        print("🎉 ENHANCED HYBRID CROP MONITORING SYSTEM - SUCCESS!")
        print("🚀 Improved models ready for agricultural deployment!")
        print("="*70)
        
        print("\n📊 Enhanced Results Summary:")
        if 'health_accuracy' in system.results:
            print("   🌾 Crop Health Accuracy: " + str(system.results['health_accuracy']))
        if 'yield_r2' in system.results:
            print("   📊 Yield R² Score: " + str(system.results['yield_r2']))
        if 'yield_rmse' in system.results:
            print("   📏 Yield RMSE: " + str(system.results['yield_rmse']))
        
        print("\n🔧 Enhanced Features:")
        print("   🛰️ 5 Vegetation Indices: NDVI, SAVI, NDRE, GNDVI, EVI")
        print("   📈 Temporal Patterns: Moving averages, growth rates, volatility")
        print("   🌡️ Enhanced Ground Features: Temp, Moisture, pH, Soil Temp, Light")
        print("   🤖 Hyperparameter Tuning: Optimized Random Forest & Gradient Boosting")
        
    else:
        print("\n❌ Enhanced system encountered errors during execution")

if __name__ == "__main__":
    main()
