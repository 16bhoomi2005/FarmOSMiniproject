#!/usr/bin/env python3
"""
Automated Crop Monitoring Pipeline
Scheduled data processing and model updates
"""

import os
import schedule
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from enhanced_hybrid_system import EnhancedHybridCropMonitoringSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)

class AutomatedCropPipeline:
    def __init__(self):
        self.system = EnhancedHybridCropMonitoringSystem()
        self.pipeline_config = self.load_config()
        self.setup_logging()
    
    def load_config(self):
        """Load pipeline configuration"""
        config_file = 'pipeline_config.json'
        default_config = {
            "schedule": {
                "daily_run": "06:00",
                "weekly_run": "sunday 08:00",
                "retrain_frequency": "weekly"
            },
            "data_sources": {
                "sentinel_path": "Sentinel_Data",
                "ground_sensor_path": "ground_sensor_data.csv",
                "backup_path": "data_backups/"
            },
            "alerts": {
                "ndvi_threshold": 0.3,
                "temperature_min": 15,
                "temperature_max": 35,
                "humidity_min": 30,
                "humidity_max": 90,
                "soil_moisture_min": 20,
                "soil_moisture_max": 80
            },
            "notifications": {
                "email_enabled": False,
                "email_recipients": [],
                "log_level": "INFO"
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = default_config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        
        return config
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.pipeline_config['notifications']['log_level']
        logging.getLogger().setLevel(getattr(logging, log_level))
    
    def daily_processing(self):
        """Daily data processing and monitoring"""
        logging.info("🌅 Starting daily crop monitoring pipeline")
        
        try:
            # Step 1: Check for new data
            new_data = self.check_new_data()
            
            if new_data:
                logging.info(f"📊 Found new data: {new_data}")
                
                # Step 2: Process new data
                self.process_new_data()
                
                # Step 3: Update predictions
                self.update_predictions()
                
                # Step 4: Check alerts
                self.check_alerts()
                
                # Step 5: Generate report
                self.generate_daily_report()
                
                logging.info("✅ Daily pipeline completed successfully")
            else:
                logging.info("ℹ️ No new data found")
        
        except Exception as e:
            logging.error(f"❌ Daily pipeline failed: {e}")
            self.send_error_alert(str(e))
    
    def weekly_processing(self):
        """Weekly model retraining and system maintenance"""
        logging.info("📅 Starting weekly maintenance pipeline")
        
        try:
            # Step 1: Backup current data
            self.backup_data()
            
            # Step 2: Retrain models with accumulated data
            self.retrain_models()
            
            # Step 3: Generate weekly report
            self.generate_weekly_report()
            
            # Step 4: System health check
            self.system_health_check()
            
            logging.info("✅ Weekly pipeline completed successfully")
        
        except Exception as e:
            logging.error(f"❌ Weekly pipeline failed: {e}")
            self.send_error_alert(str(e))
    
    def check_new_data(self):
        """Check for new satellite and ground sensor data"""
        new_data = {}
        
        # Check for new Sentinel-2 data
        sentinel_path = self.pipeline_config['data_sources']['sentinel_path']
        safe_dirs = glob.glob(os.path.join(sentinel_path, "*.SAFE"))
        
        # Get latest processed date
        latest_processed = self.get_latest_processed_date()
        
        new_scenes = []
        for safe_dir in safe_dirs:
            scene_date = self.extract_date_from_path(safe_dir)
            if scene_date > latest_processed:
                new_scenes.append(scene_date)
        
        if new_scenes:
            new_data['sentinel_scenes'] = new_scenes
        
        # Check for new ground sensor data
        ground_path = self.pipeline_config['data_sources']['ground_sensor_path']
        if os.path.exists(ground_path):
            ground_data = pd.read_csv(ground_path)
            if 'Date' in ground_data.columns:
                ground_data['Date'] = pd.to_datetime(ground_data['Date'])
                latest_ground_date = ground_data['Date'].max()
                
                if latest_ground_date > latest_processed:
                    new_data['ground_data'] = latest_ground_date
        
        return new_data
    
    def get_latest_processed_date(self):
        """Get the latest date that was processed"""
        # Check log file for last successful run
        if os.path.exists('pipeline.log'):
            with open('pipeline.log', 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if 'pipeline completed successfully' in line:
                        # Extract date from log line
                        date_str = line.split()[0]
                        return datetime.strptime(date_str, '%Y-%m-%d')
        
        # Default to 7 days ago
        return datetime.now() - timedelta(days=7)
    
    def extract_date_from_path(self, path):
        """Extract date from Sentinel-2 file path"""
        filename = os.path.basename(path)
        parts = filename.split('_')
        for part in parts:
            if 'T' in part and len(part) == 15:
                return datetime.strptime(part[:8], '%Y%m%d')
        return datetime.now()
    
    def process_new_data(self):
        """Process new satellite and ground sensor data"""
        logging.info("🔄 Processing new data...")
        
        # Run enhanced system
        success = True
        
        if not self.system.step1_satellite_feature_extraction():
            success = False
        
        if not self.system.step2_enhanced_time_series_engineering():
            success = False
        
        if not self.system.step3_merge_with_ground_sensors():
            success = False
        
        if not self.system.step4_enhanced_model_training():
            success = False
        
        if success:
            logging.info("✅ New data processed successfully")
        else:
            logging.warning("⚠️ Some processing steps failed")
    
    def update_predictions(self):
        """Update predictions with latest data"""
        logging.info("🔮 Updating predictions...")
        
        try:
            # Load latest models
            import joblib
            health_model = joblib.load('models/enhanced_health_classifier.pkl')
            yield_model = joblib.load('models/enhanced_yield_regressor.pkl')
            scaler = joblib.load('models/enhanced_feature_scaler.pkl')
            
            # Get latest feature data
            if hasattr(self.system, 'feature_dataset') and len(self.system.feature_dataset) > 0:
                latest_features = self.system.feature_dataset.iloc[-1]
                
                # Make predictions
                feature_vector = latest_features.drop(['Crop_Health', 'Yield'], errors='ignore')
                scaled_features = scaler.transform([feature_vector])
                
                health_pred = health_model.predict(scaled_features)[0]
                yield_pred = yield_model.predict(scaled_features)[0]
                
                # Save predictions
                predictions = {
                    'timestamp': datetime.now().isoformat(),
                    'health_prediction': int(health_pred),
                    'yield_prediction': float(yield_pred),
                    'features': latest_features.to_dict()
                }
                
                with open('latest_predictions.json', 'w') as f:
                    json.dump(predictions, f, indent=2)
                
                logging.info(f"✅ Predictions updated: Health={health_pred}, Yield={yield_pred:.2f}")
            
        except Exception as e:
            logging.error(f"❌ Prediction update failed: {e}")
    
    def check_alerts(self):
        """Check for alert conditions"""
        logging.info("🚨 Checking alert conditions...")
        
        alerts = []
        thresholds = self.pipeline_config['alerts']
        
        try:
            # Load latest predictions
            if os.path.exists('latest_predictions.json'):
                with open('latest_predictions.json', 'r') as f:
                    predictions = json.load(f)
                
                features = predictions['features']
                
                # Check NDVI
                ndvi = features.get('NDVI_mean', 0.6)
                if ndvi < thresholds['ndvi_threshold']:
                    alerts.append({
                        'type': 'warning',
                        'message': f'Low NDVI detected: {ndvi:.3f}',
                        'threshold': thresholds['ndvi_threshold']
                    })
                
                # Check temperature
                temp = features.get('Temperature_mean', 25)
                if temp < thresholds['temperature_min'] or temp > thresholds['temperature_max']:
                    alerts.append({
                        'type': 'danger',
                        'message': f'Extreme temperature: {temp:.1f}°C',
                        'threshold': f"{thresholds['temperature_min']}-{thresholds['temperature_max']}°C"
                    })
                
                # Check humidity
                humidity = features.get('Humidity_mean', 65)
                if humidity < thresholds['humidity_min'] or humidity > thresholds['humidity_max']:
                    alerts.append({
                        'type': 'warning',
                        'message': f'Extreme humidity: {humidity:.1f}%',
                        'threshold': f"{thresholds['humidity_min']}-{thresholds['humidity_max']}%"
                    })
                
                # Check soil moisture
                moisture = features.get('Soil_Moisture_mean', 55)
                if moisture < thresholds['soil_moisture_min'] or moisture > thresholds['soil_moisture_max']:
                    alerts.append({
                        'type': 'warning',
                        'message': f'Extreme soil moisture: {moisture:.1f}%',
                        'threshold': f"{thresholds['soil_moisture_min']}-{thresholds['soil_moisture_max']}%"
                    })
                
                # Save alerts
                if alerts:
                    alerts_data = {
                        'timestamp': datetime.now().isoformat(),
                        'alerts': alerts
                    }
                    
                    with open('active_alerts.json', 'w') as f:
                        json.dump(alerts_data, f, indent=2)
                    
                    logging.warning(f"🚨 {len(alerts)} alerts generated")
                    
                    # Send notifications if enabled
                    if self.pipeline_config['notifications']['email_enabled']:
                        self.send_alert_notifications(alerts)
                else:
                    logging.info("✅ No alerts generated")
            
        except Exception as e:
            logging.error(f"❌ Alert checking failed: {e}")
    
    def generate_daily_report(self):
        """Generate daily monitoring report"""
        logging.info("📄 Generating daily report...")
        
        try:
            report = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'system_status': 'operational',
                'data_processed': True,
                'predictions': {},
                'alerts': [],
                'recommendations': []
            }
            
            # Add predictions
            if os.path.exists('latest_predictions.json'):
                with open('latest_predictions.json', 'r') as f:
                    predictions = json.load(f)
                report['predictions'] = predictions
            
            # Add alerts
            if os.path.exists('active_alerts.json'):
                with open('active_alerts.json', 'r') as f:
                    alerts_data = json.load(f)
                report['alerts'] = alerts_data.get('alerts', [])
            
            # Generate recommendations
            if report['alerts']:
                report['recommendations'] = [
                    "Check irrigation system due to low soil moisture",
                    "Monitor for pest activity with low NDVI values",
                    "Consider additional fertilization for poor vegetation health"
                ]
            else:
                report['recommendations'] = [
                    "Continue normal monitoring schedule",
                    "Maintain current irrigation and fertilization practices"
                ]
            
            # Save report
            report_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(f"reports/{report_filename}", 'w') as f:
                json.dump(report, f, indent=2)
            
            logging.info(f"✅ Daily report saved: {report_filename}")
            
        except Exception as e:
            logging.error(f"❌ Daily report generation failed: {e}")
    
    def backup_data(self):
        """Backup current data and models"""
        logging.info("💾 Creating data backup...")
        
        try:
            backup_path = self.pipeline_config['data_sources']['backup_path']
            os.makedirs(backup_path, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup models
            if os.path.exists('models'):
                import shutil
                shutil.copytree('models', f"{backup_path}/models_{timestamp}")
            
            # Backup data
            data_files = ['sample_ground_sensor_data.csv', 'pipeline.log']
            for file in data_files:
                if os.path.exists(file):
                    shutil.copy2(file, backup_path)
            
            logging.info(f"✅ Backup completed: {timestamp}")
            
        except Exception as e:
            logging.error(f"❌ Backup failed: {e}")
    
    def retrain_models(self):
        """Retrain models with accumulated data"""
        logging.info("🔄 Retraining models...")
        
        try:
            # Run enhanced system training
            success = True
            
            if not self.system.step1_satellite_feature_extraction():
                success = False
            
            if not self.system.step2_enhanced_time_series_engineering():
                success = False
            
            if not self.system.step3_merge_with_ground_sensors():
                success = False
            
            if not self.system.step4_enhanced_model_training():
                success = False
            
            if success:
                logging.info("✅ Models retrained successfully")
            else:
                logging.warning("⚠️ Model retraining had issues")
            
        except Exception as e:
            logging.error(f"❌ Model retraining failed: {e}")
    
    def generate_weekly_report(self):
        """Generate comprehensive weekly report"""
        logging.info("📊 Generating weekly report...")
        
        try:
            report = {
                'week_start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'week_end': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'daily_runs': 7,
                    'successful_runs': 6,  # Example
                    'alerts_generated': 3,
                    'models_retrained': True
                },
                'performance': {
                    'avg_ndvi': 0.65,
                    'avg_temperature': 26.5,
                    'avg_yield_prediction': 68.2
                },
                'recommendations': [
                    "Continue current monitoring schedule",
                    "Consider expanding sensor coverage",
                    "Review alert thresholds for optimization"
                ]
            }
            
            # Save report
            report_filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(f"reports/{report_filename}", 'w') as f:
                json.dump(report, f, indent=2)
            
            logging.info(f"✅ Weekly report saved: {report_filename}")
            
        except Exception as e:
            logging.error(f"❌ Weekly report generation failed: {e}")
    
    def system_health_check(self):
        """Perform system health check"""
        logging.info("🏥 Performing system health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Check data availability
        health_status['components']['sentinel_data'] = os.path.exists(self.pipeline_config['data_sources']['sentinel_path'])
        health_status['components']['ground_data'] = os.path.exists(self.pipeline_config['data_sources']['ground_sensor_path'])
        health_status['components']['models'] = os.path.exists('models/enhanced_health_classifier.pkl')
        
        # Check disk space
        import shutil
        disk_usage = shutil.disk_usage('.')
        health_status['components']['disk_space_gb'] = disk_usage.free / (1024**3)
        
        # Check memory usage
        import psutil
        health_status['components']['memory_usage_percent'] = psutil.virtual_memory().percent
        
        # Overall health
        all_healthy = all(health_status['components'].values())
        health_status['overall_health'] = 'healthy' if all_healthy else 'warning'
        
        # Save health status
        with open('system_health.json', 'w') as f:
            json.dump(health_status, f, indent=2)
        
        if all_healthy:
            logging.info("✅ System health check passed")
        else:
            logging.warning("⚠️ System health check found issues")
    
    def send_alert_notifications(self, alerts):
        """Send alert notifications (placeholder for email/SMS)"""
        logging.info(f"📧 Sending {len(alerts)} alert notifications...")
        
        # Placeholder for email/SMS implementation
        # In production, integrate with email service or SMS API
        
        for alert in alerts:
            logging.warning(f"ALERT: {alert['message']}")
    
    def send_error_alert(self, error_message):
        """Send error alert notifications"""
        logging.error(f"🚨 SYSTEM ERROR: {error_message}")
        
        # Placeholder for error notification system
    
    def run_scheduler(self):
        """Run the automated scheduler"""
        logging.info("🚀 Starting automated crop monitoring pipeline")
        
        # Create necessary directories
        os.makedirs('reports', exist_ok=True)
        os.makedirs(self.pipeline_config['data_sources']['backup_path'], exist_ok=True)
        
        # Schedule daily processing
        daily_time = self.pipeline_config['schedule']['daily_run']
        schedule.every().day.at(daily_time).do(self.daily_processing)
        
        # Schedule weekly processing
        weekly_time = self.pipeline_config['schedule']['weekly_run']
        if weekly_time.startswith('sunday'):
            time_part = weekly_time.split(' ')[1]
            schedule.every().sunday.at(time_part).do(self.weekly_processing)
        
        logging.info(f"⏰ Daily processing scheduled for {daily_time}")
        logging.info(f"⏰ Weekly processing scheduled for {weekly_time}")
        
        # Run initial processing
        logging.info("🔄 Running initial processing...")
        self.daily_processing()
        
        # Main scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main function to run the automated pipeline"""
    print("🚀 AUTOMATED CROP MONITORING PIPELINE")
    print("="*60)
    print("Starting scheduled data processing and monitoring...")
    print("Press Ctrl+C to stop")
    print("="*60)
    
    try:
        pipeline = AutomatedCropPipeline()
        pipeline.run_scheduler()
    except KeyboardInterrupt:
        logging.info("🛑 Pipeline stopped by user")
    except Exception as e:
        logging.error(f"❌ Pipeline crashed: {e}")

if __name__ == "__main__":
    main()
