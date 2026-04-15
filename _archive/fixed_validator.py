#!/usr/bin/env python3
"""
Fixed real data validator with JSON serialization fix
"""

import pandas as pd
import numpy as np
import json
import os

class FixedRealDataValidator:
    def __init__(self):
        self.validation_results = {}
        
    def validate_sentinel_data(self):
        """Validate Sentinel-2 data processing"""
        print("🛰️ VALIDATING SENTINEL-2 DATA")
        print("="*50)
        
        sentinel_file = "real_sentinel_features_fixed.csv"
        
        if not os.path.exists(sentinel_file):
            print("❌ Sentinel-2 data file not found")
            return False
        
        df = pd.read_csv(sentinel_file)
        
        # Basic validation
        validations = {
            'total_records': int(len(df)),
            'date_range': f"{df['Date'].min()} to {df['Date'].max()}",
            'vegetation_indices_present': bool(all(idx in df.columns for idx in ['NDVI_mean', 'SAVI_mean', 'NDRE_mean', 'GNDVI_mean', 'EVI_mean'])),
            'no_missing_dates': bool(df['Date'].isnull().sum() == 0),
            'reasonable_ndvi_range': bool(df['NDVI_mean'].between(-1, 1).all()),
            'positive_std_values': bool(all(df[col].ge(0).all() for col in df.columns if 'std' in col))
        }
        
        print("📊 Sentinel-2 Data Validation:")
        for key, value in validations.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        # Detailed statistics
        print("\n📈 Vegetation Index Statistics:")
        veg_indices = ['NDVI_mean', 'SAVI_mean', 'NDRE_mean', 'GNDVI_mean', 'EVI_mean']
        
        for idx in veg_indices:
            if idx in df.columns:
                data = df[idx]
                print(f"   {idx}:")
                print(f"      Mean: {data.mean():.4f}")
                print(f"      Std: {data.std():.4f}")
                print(f"      Range: {data.min():.4f} to {data.max():.4f}")
        
        self.validation_results['sentinel'] = validations
        return all(validations.values())
    
    def validate_ground_sensor_data(self):
        """Validate ground sensor data"""
        print("\n🌡️ VALIDATING GROUND SENSOR DATA")
        print("="*50)
        
        sensor_file = "enhanced_ready_data.csv"
        
        if not os.path.exists(sensor_file):
            print("❌ Ground sensor data file not found")
            return False
        
        df = pd.read_csv(sensor_file)
        
        # Basic validation
        validations = {
            'total_readings': int(len(df)),
            'date_range': f"{df['Date'].min()} to {df['Date'].max()}",
            'has_temperature': bool('Temperature' in df.columns),
            'has_humidity': bool('Humidity' in df.columns),
            'has_soil_moisture': bool('Soil_Moisture' in df.columns),
            'reasonable_temp_range': bool(df['Temperature'].between(-20, 60).all()),
            'reasonable_humidity_range': bool(df['Humidity'].between(0, 100).all()),
            'reasonable_moisture_range': bool(df['Soil_Moisture'].between(0, 100).all())
        }
        
        print("📊 Ground Sensor Data Validation:")
        for key, value in validations.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        # Sensor statistics
        print("\n📈 Sensor Statistics:")
        for col in ['Temperature', 'Humidity', 'Soil_Moisture']:
            if col in df.columns:
                data = df[col]
                print(f"   {col}:")
                print(f"      Mean: {data.mean():.2f}")
                print(f"      Std: {data.std():.2f}")
                print(f"      Range: {data.min():.2f} to {data.max():.2f}")
        
        self.validation_results['ground_sensors'] = validations
        return all(validations.values())
    
    def validate_integration(self):
        """Validate data integration"""
        print("\n🔄 VALIDATING DATA INTEGRATION")
        print("="*50)
        
        integrated_file = "enhanced_ready_data.csv"
        
        if not os.path.exists(integrated_file):
            print("❌ Integrated data file not found")
            return False
        
        df = pd.read_csv(integrated_file)
        
        # Basic validation
        validations = {
            'total_records': int(len(df)),
            'date_range': f"{df['Date'].min()} to {df['Date'].max()}",
            'has_sentinel_features': bool(all(idx in df.columns for idx in ['NDVI_mean', 'SAVI_mean', 'NDRE_mean'])),
            'has_sensor_features': bool(all(col in df.columns for col in ['Temperature', 'Humidity', 'Soil_Moisture'])),
            'no_missing_critical_data': bool(df[['NDVI_mean', 'Temperature', 'Humidity', 'Soil_Moisture']].isnull().sum().sum() == 0),
            'reasonable_feature_ranges': bool(
                df['NDVI_mean'].between(-1, 1).all() and
                df['Temperature'].between(-20, 60).all() and
                df['Humidity'].between(0, 100).all() and
                df['Soil_Moisture'].between(0, 100).all()
            )
        }
        
        print("📊 Integration Validation:")
        for key, value in validations.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        self.validation_results['integration'] = validations
        return all(validations.values())
    
    def validate_models(self):
        """Validate trained models"""
        print("\n🤖 VALIDATING TRAINED MODELS")
        print("="*50)
        
        model_files = [
            'models/enhanced_health_classifier.pkl',
            'models/enhanced_yield_regressor.pkl',
            'models/enhanced_feature_scaler.pkl'
        ]
        
        validations = {
            'health_model_exists': bool(os.path.exists(model_files[0])),
            'yield_model_exists': bool(os.path.exists(model_files[1])),
            'scaler_exists': bool(os.path.exists(model_files[2])),
            'feature_columns_exist': bool(os.path.exists('models/enhanced_feature_columns.txt')),
            'results_file_exists': bool(os.path.exists('models/enhanced_model_results.txt'))
        }
        
        print("📊 Model Validation:")
        for key, value in validations.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        # Check model results
        if validations['results_file_exists']:
            try:
                with open('models/enhanced_model_results.txt', 'r') as f:
                    results = f.read()
                print(f"\n📈 Model Performance Results:")
                print(results)
            except Exception as e:
                print(f"❌ Error reading results: {e}")
        
        self.validation_results['models'] = validations
        return all(validations.values())
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n📊 COMPREHENSIVE VALIDATION REPORT")
        print("="*60)
        
        # Run all validations
        sentinel_ok = self.validate_sentinel_data()
        ground_ok = self.validate_ground_sensor_data()
        integration_ok = self.validate_integration()
        models_ok = self.validate_models()
        
        # Overall status
        all_validations = [sentinel_ok, ground_ok, integration_ok, models_ok]
        overall_status = "✅ PASS" if all(all_validations) else "⚠️ PARTIAL PASS"
        
        print(f"\n🎯 OVERALL VALIDATION STATUS: {overall_status}")
        
        validation_summary = {
            'Sentinel-2 Data': 'PASS' if sentinel_ok else 'FAIL',
            'Ground Sensors': 'PASS' if ground_ok else 'FAIL',
            'Data Integration': 'PASS' if integration_ok else 'FAIL',
            'Model Training': 'PASS' if models_ok else 'FAIL'
        }
        
        print("\n📋 Validation Summary:")
        for component, status in validation_summary.items():
            icon = "✅" if status == 'PASS' else "❌"
            print(f"   {icon} {component}: {status}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if not sentinel_ok:
            print("   🛰️ Check Sentinel-2 .SAFE files and processing")
        
        if not ground_ok:
            print("   🌡️ Verify ground sensor data collection and formatting")
        
        if not integration_ok:
            print("   🔄 Ensure overlapping dates between datasets")
        
        if not models_ok:
            print("   🤖 Re-run model training with integrated data")
        
        if all(all_validations):
            print("   🚀 System is ready for production deployment!")
            print("   📱 Launch dashboard for real-time monitoring")
            print("   ⚙️ Start automated pipeline for continuous processing")
        
        # Save validation report with JSON serialization fix
        report_data = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'overall_status': overall_status,
            'validation_summary': validation_summary,
            'detailed_results': self.validation_results
        }
        
        # Convert all values to JSON-serializable format
        def make_json_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return int(obj) if isinstance(obj, np.integer) else float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, bool):
                return bool(obj)
            else:
                return str(obj)
        
        json_report = make_json_serializable(report_data)
        
        with open('validation_report_fixed.json', 'w') as f:
            json.dump(json_report, f, indent=2)
        
        print(f"\n💾 Validation report saved to validation_report_fixed.json")
        
        return all(all_validations)

def main():
    """Main validation function"""
    validator = FixedRealDataValidator()
    
    print("🔍 FIXED REAL DATA VALIDATION SYSTEM")
    print("="*60)
    print("Validating real-world data processing and model training")
    
    # Generate comprehensive validation report
    success = validator.generate_validation_report()
    
    if success:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✅ Real data processing system is ready for production")
    else:
        print("\n⚠️ SOME VALIDATIONS FAILED")
        print("📝 Review report above and address issues")

if __name__ == "__main__":
    main()
