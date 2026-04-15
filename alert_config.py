#!/usr/bin/env python3
"""
Actionable Alerts Configuration System
Real farming alerts with specific actions and locations
Rice (Paddy) domain — Kharif / Rabi seasons
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# ─────────────────────────────────────────────────────────────────────────────
# THRESHOLDS — Rice (Paddy) specific sensor alert thresholds
# Used by sim_engine.py and the new Spectral / Pest Risk pages.
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# THREAT METADATA — Drivers, actions, and localized content for Pests & Diseases
# ─────────────────────────────────────────────────────────────────────────────
THREAT_METADATA = {
    "Rice Blast": {
        "drivers": [("Humidity", "88%", "critical"), ("Temp", "27°C", "normal"), ("Leaf Wet", "5h", "warning")],
        "action": "Spray Tricyclazole 0.6 g/L. NW Field most exposed. Window: 4-8am.",
        "action_hi": "ट्राइसाइक्लाज़ोल 0.6 ग्राम/लीटर का छिड़काव करें। NW खेत सबसे अधिक जोखिम में है।"
    },
    "Brown Spot": {
        "drivers": [("Humidity", "71%", "normal"), ("Nitrogen", "Low", "critical"), ("Leaf Wet", "4h", "normal")],
        "action": "Apply nitrogen to SW field first. Avoid spray if heavy rain occurs.",
        "action_hi": "पहले SW खेत में नाइट्रोजन डालें। भारी बारिश होने पर छिड़काव से बचें।"
    },
    "Sheath Blight": {
        "drivers": [("Canopy", "Dense", "critical"), ("Humidity", "77%", "normal"), ("Wind", "Low", "safe")],
        "action": "Risk rises after Saturday rain. Trim dense canopy manually where possible.",
        "action_hi": "शनिवार की बारिश के बाद जोखिम बढ़ जाता है। संभव हो तो घने चंदवा को मैन्युअल रूप से काटें।"
    },
    "False Smut": {
        "drivers": [("Humidity", "78%", "normal"), ("Crop Stage", "Booting", "warning"), ("Rain", "Expected", "warning")],
        "action": "Monitoring only. Conditions for spore growth are emerging.",
        "action_hi": "केवल निगरानी। स्पोर वृद्धि की स्थितियां बन रही हैं।"
    },
    "Stem Borer": {
        "drivers": [("Temp", "32°C", "normal"), ("Crop Stage", "Tillering", "normal"), ("Trap Count", "2/wk", "safe")],
        "action": "Low risk detected. Pheromone trap counts are below threshold.",
        "action_hi": "कम जोखिम। फेरोमोन ट्रैप काउंट सीमा से नीचे हैं।"
    },
    "Leaf Folder": {
        "drivers": [("Humidity", "77%", "normal"), ("Wind", "12 km/h", "normal"), ("Sighting", "None", "safe")],
        "action": "All clear. No butterfly activity recorded field-side this week.",
        "action_hi": "उत्तम स्थिति। इस सप्ताह खेत के किनारे तितलियों की कोई गतिविधि नहीं देखी गई।"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# NPK CONFIG — Nutrition thresholds and fertilizer rates/costs
# ─────────────────────────────────────────────────────────────────────────────
NPK_CONFIG = {
    "N": {"min": 120, "max": 140, "unit": "kg/ha", "name": "Nitrogen"},
    "P": {"min": 40, "max": 60, "unit": "kg/ha", "name": "Phosphorus"},
    "K": {"min": 120, "max": 150, "unit": "kg/ha", "name": "Potassium"}
}

FERTILIZER_CONFIG = {
    "MRP": {
        "name": "MRP (Monoammonium Phosphate)",
        "role": "Root development - energy transfer",
        "price": 9.2, # ₹/kg
        "standard_dose": 50, # kg/ha
        "nutrient": "P"
    },
    "MOP": {
        "name": "MOP (Muriate of Potash)",
        "role": "Disease resistance - water regulation",
        "price": 2.0,
        "standard_dose": 10,
        "nutrient": "K"
    },
    "Urea": {
        "name": "Urea Top-up",
        "role": "Primary macronutrient - growth & leaf color",
        "price": 7.5,
        "standard_dose": 25,
        "nutrient": "N"
    }
}

THRESHOLDS = {
    "soil_moisture":  {"warning": 45,  "critical": 35},   # % — rice needs higher moisture
    "soil_pH":        {"low_warning": 5.5, "high_warning": 7.0},  # optimal 5.5–6.5 for rice
    "soil_temp":      {"warning": 30,  "critical": 35},   # °C
    "air_temp":       {"warning": 34,  "critical": 38},   # °C — rice heat stress
    "humidity":       {"warning": 85,  "critical": 92},   # % — blast fungi threshold
    "leaf_wetness":   {"warning": 70,  "critical": 85},   # % — disease trigger
    "nitrogen":       {"warning": 90,  "critical": 70},   # kg/ha — deficiency thresholds
    "pest_risk":      {"warning": 50,  "critical": 75},   # 0–100 score
    "health_score":   {"warning": 55,  "critical": 40},   # 0–100 score
    "ndvi":           {"warning": 0.45, "critical": 0.30},# greenness thresholds
}

class ActionableAlertsSystem:
    def __init__(self):
        self.alert_thresholds = self.setup_alert_thresholds()
        self.field_locations = self.setup_field_locations()
        self.alert_history = []
        
    def setup_field_locations(self):
        """Define precise field locations with coordinates"""
        return {
            'North': {
                'coordinates': (28.6139, 77.2090),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Loamy'
            },
            'East': {
                'coordinates': (28.6239, 77.2190),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Sandy'
            },
            'Center': {
                'coordinates': (28.6339, 77.2290),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Clay'
            },
            'South': {
                'coordinates': (28.6439, 77.2390),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Loamy'
            },
            'West': {
                'coordinates': (28.6539, 77.2490),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Sandy'
            },
            'Northwest': {
                'coordinates': (28.6639, 77.2590),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Loamy'
            },
            'Northeast': {
                'coordinates': (28.6739, 77.2690),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Clay'
            },
            'Southwest': {
                'coordinates': (28.6839, 77.2790),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Sandy'
            },
            'Southeast': {
                'coordinates': (28.6939, 77.2890),
                'area_acres': 10,
                'crop_type': 'Rice (Paddy)',
                'soil_type': 'Loamy'
            }
        }
    
    def setup_alert_thresholds(self):
        """Define precise alert thresholds for farming decisions"""
        return {
            'irrigation': {
                'critical_ndvi_drop': 0.15,  # 15% drop
                'critical_soil_moisture': 35,  # Below 35%
                'warning_soil_moisture': 45,   # Below 45%
                'monitoring_soil_moisture': 55 # Below 55%
            },
            'temperature': {
                'critical_high': 38,  # Above 38°C
                'warning_high': 35,    # Above 35°C
                'critical_low': 5,    # Below 5°C
                'warning_low': 10      # Below 10°C
            },
            'humidity': {
                'critical_high': 85,  # Above 85%
                'warning_high': 80,    # Above 80%
                'critical_low': 25,    # Below 25%
                'warning_low': 30      # Below 30%
            },
            'ndvi': {
                'critical_drop': 0.20,  # 20% drop in 72 hours
                'warning_drop': 0.10,   # 10% drop in 72 hours
                'critical_level': 0.3,  # Below 0.3
                'warning_level': 0.4    # Below 0.4
            },
            'soil_ph': {
                'critical_low': 5.5,
                'critical_high': 7.5,
                'warning_low': 6.0,
                'warning_high': 7.0
            },
            'soil_temperature': {
                'critical_low': 10,
                'critical_high': 30,
                'warning_low': 15,
                'warning_high': 25
            }
        }
    
    def generate_irrigation_alert(self, field_name, current_data, historical_data):
        """Generate specific irrigation alerts with actions"""
        alerts = []
        
        current_ndvi = current_data.get('NDVI_mean', 0)
        current_moisture = current_data.get('soil_moisture_mean', 50)
        
        # Critical NDVI drop alert
        if len(historical_data) >= 2:
            prev_ndvi = historical_data[-2].get('NDVI_mean', current_ndvi)
            ndvi_drop = (prev_ndvi - current_ndvi) / prev_ndvi
            
            if ndvi_drop >= self.alert_thresholds['irrigation']['critical_ndvi_drop']:
                location = self.field_locations[field_name]
                alerts.append({
                    'type': 'CRITICAL',
                    'category': 'IRRIGATION',
                    'field': field_name,
                    'coordinates': location['coordinates'],
                    'message': f"NDVI dropped {ndvi_drop*100:.0f}% in 48 hours",
                    'action': 'Start irrigation pumps immediately',
                    'time_sensitivity': 'Within 2 hours',
                    'impact': f"Prevent ${2100 * location['area_acres']/10:.0f} yield loss",
                    'confidence': 95,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Soil moisture alerts
        if current_moisture <= self.alert_thresholds['irrigation']['critical_soil_moisture']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'CRITICAL',
                'category': 'IRRIGATION',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil moisture critical at {current_moisture:.0f}%",
                'action': 'Start irrigation immediately',
                'time_sensitivity': 'Within 1 hour',
                'impact': f"Prevent crop stress, save ${1500 * location['area_acres']/10:.0f}",
                'confidence': 90,
                'timestamp': datetime.now().isoformat()
            })
        
        elif current_moisture <= self.alert_thresholds['irrigation']['warning_soil_moisture']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'WARNING',
                'category': 'IRRIGATION',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil moisture low at {current_moisture:.0f}%",
                'action': 'Schedule irrigation within 6 hours',
                'time_sensitivity': 'Within 6 hours',
                'impact': f"Optimize water usage, save ${400 * location['area_acres']/10:.0f}/month",
                'confidence': 85,
                'timestamp': datetime.now().isoformat()
            })
        
        elif current_moisture <= self.alert_thresholds['irrigation']['monitoring_soil_moisture']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'MONITORING',
                'category': 'IRRIGATION',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil moisture trending down at {current_moisture:.0f}%",
                'action': 'Check sensors, plan irrigation tomorrow',
                'time_sensitivity': 'Next 24 hours',
                'impact': 'Maintain optimal conditions',
                'confidence': 75,
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def generate_temperature_alerts(self, field_name, current_data):
        """Generate temperature-related alerts"""
        alerts = []
        
        current_temp = current_data.get('Temperature', 25)
        
        if current_temp >= self.alert_thresholds['temperature']['critical_high']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'CRITICAL',
                'category': 'TEMPERATURE',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Temperature critical at {current_temp:.0f}°C",
                'action': 'Deploy shade nets immediately',
                'time_sensitivity': 'Within 1 hour',
                'impact': f"Prevent heat stress, save ${1800 * location['area_acres']/10:.0f}",
                'confidence': 95,
                'timestamp': datetime.now().isoformat()
            })
        
        elif current_temp >= self.alert_thresholds['temperature']['warning_high']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'WARNING',
                'category': 'TEMPERATURE',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Temperature high at {current_temp:.0f}°C",
                'action': 'Consider shade nets, increase ventilation',
                'time_sensitivity': 'Within 4 hours',
                'impact': f"Reduce temperature stress, save ${800 * location['area_acres']/10:.0f}",
                'confidence': 80,
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def generate_humidity_alerts(self, field_name, current_data):
        """Generate humidity-related alerts"""
        alerts = []
        
        current_humidity = current_data.get('Humidity', 60)
        
        if current_humidity >= self.alert_thresholds['humidity']['critical_high']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'WARNING',
                'category': 'HUMIDITY',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Humidity high at {current_humidity:.0f}%",
                'action': 'Increase ventilation, monitor for disease',
                'time_sensitivity': 'Within 4 hours',
                'impact': f"Prevent fungal growth, save ${600 * location['area_acres']/10:.0f}",
                'confidence': 85,
                'timestamp': datetime.now().isoformat()
            })
        
        elif current_humidity <= self.alert_thresholds['humidity']['critical_low']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'MONITORING',
                'category': 'HUMIDITY',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Humidity low at {current_humidity:.0f}%",
                'action': 'Consider misting if temperature >30°C',
                'time_sensitivity': 'Plan for tomorrow morning',
                'impact': 'Optimize growing conditions',
                'confidence': 70,
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def generate_ndvi_alerts(self, field_name, current_data, historical_data):
        """Generate NDVI and crop stress alerts"""
        alerts = []
        
        current_ndvi = current_data.get('NDVI_mean', 0.5)
        
        # Critical NDVI level
        if current_ndvi <= self.alert_thresholds['ndvi']['critical_level']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'CRITICAL',
                'category': 'CROP_STRESS',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"NDVI critical at {current_ndvi:.2f}",
                'action': 'Immediate field inspection - possible disease/pest',
                'time_sensitivity': 'Within 12 hours',
                'impact': f"Prevent field-wide loss, save ${5000 * location['area_acres']/10:.0f}",
                'confidence': 90,
                'timestamp': datetime.now().isoformat()
            })
        
        # NDVI drop analysis
        if len(historical_data) >= 4:  # Check last 3 readings
            recent_ndvis = [d.get('NDVI_mean', current_ndvi) for d in historical_data[-4:]]
            if len(recent_ndvis) >= 3:
                # Calculate trend
                trend = np.polyfit(range(len(recent_ndvis)), recent_ndvis, 1)[0]
                
                if trend <= -0.05:  # Significant downward trend
                    location = self.field_locations[field_name]
                    alerts.append({
                        'type': 'WARNING',
                        'category': 'CROP_STRESS',
                        'field': field_name,
                        'coordinates': location['coordinates'],
                        'message': f"NDVI trending down ({trend:.3f} per reading)",
                        'action': 'Check nutrient levels, soil pH',
                        'time_sensitivity': 'Within 24 hours',
                        'impact': f"Optimize growth, add {200 * location['area_acres']/10:.0f} tons/ha yield",
                        'confidence': 80,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return alerts
    
    def generate_ph_alerts(self, field_name, current_data):
        """Generate Soil pH alerts"""
        alerts = []
        
        current_ph = current_data.get('Soil_pH', 6.5)
        
        if current_ph <= self.alert_thresholds['soil_ph']['critical_low'] or \
           current_ph >= self.alert_thresholds['soil_ph']['critical_high']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'CRITICAL',
                'category': 'SOIL_HEALTH',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil pH critical at {current_ph:.1f}",
                'action': 'Apply lime (if low) or sulfur (if high) immediately',
                'time_sensitivity': 'Within 24 hours',
                'impact': f"Restore nutrient availability, prevent long-term damage",
                'confidence': 90,
                'timestamp': datetime.now().isoformat()
            })
            
        elif current_ph <= self.alert_thresholds['soil_ph']['warning_low'] or \
             current_ph >= self.alert_thresholds['soil_ph']['warning_high']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'WARNING',
                'category': 'SOIL_HEALTH',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil pH suboptimal at {current_ph:.1f}",
                'action': 'Schedule soil amendment application',
                'time_sensitivity': 'Next 3 days',
                'impact': 'Optimize nutrient uptake',
                'confidence': 80,
                'timestamp': datetime.now().isoformat()
            })
            
        return alerts

    def generate_soil_temp_alerts(self, field_name, current_data):
        """Generate Soil Temperature alerts"""
        alerts = []
        
        current_soil_temp = current_data.get('Soil_Temperature', 20)
        
        if current_soil_temp <= self.alert_thresholds['soil_temperature']['critical_low']:
            location = self.field_locations[field_name]
            alerts.append({
                'type': 'CRITICAL',
                'category': 'SOIL_HEALTH',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil temp too low at {current_soil_temp:.1f}°C",
                'action': 'Delay planting / Use soil covers',
                'time_sensitivity': 'Immediate',
                'impact': f"Prevent germination failure",
                'confidence': 90,
                'timestamp': datetime.now().isoformat()
            })
            
        elif current_soil_temp >= self.alert_thresholds['soil_temperature']['critical_high']:
             location = self.field_locations[field_name]
             alerts.append({
                'type': 'CRITICAL',
                'category': 'SOIL_HEALTH',
                'field': field_name,
                'coordinates': location['coordinates'],
                'message': f"Soil temp too high at {current_soil_temp:.1f}°C",
                'action': 'Increase irrigation / Mulching',
                'time_sensitivity': 'Immediate',
                'impact': f"Prevent root burn",
                'confidence': 90,
                'timestamp': datetime.now().isoformat()
            })
            
        return alerts

    def process_field_data(self, field_name, current_data, historical_data):
        """Process all field data and generate comprehensive alerts"""
        all_alerts = []
        
        # Generate all types of alerts
        irrigation_alerts = self.generate_irrigation_alert(field_name, current_data, historical_data)
        temperature_alerts = self.generate_temperature_alerts(field_name, current_data)
        humidity_alerts = self.generate_humidity_alerts(field_name, current_data)
        ndvi_alerts = self.generate_ndvi_alerts(field_name, current_data, historical_data)
        ph_alerts = self.generate_ph_alerts(field_name, current_data)
        soil_temp_alerts = self.generate_soil_temp_alerts(field_name, current_data)
        
        all_alerts.extend(irrigation_alerts)
        all_alerts.extend(temperature_alerts)
        all_alerts.extend(humidity_alerts)
        all_alerts.extend(ndvi_alerts)
        all_alerts.extend(ph_alerts)
        all_alerts.extend(soil_temp_alerts)
        
        # Store in history
        self.alert_history.extend(all_alerts)
        
        return all_alerts
    
    def get_active_alerts(self):
        """Get all currently active alerts"""
        # Filter alerts from last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        active_alerts = [
            alert for alert in self.alert_history 
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        # Sort by priority and time
        priority_order = {'CRITICAL': 0, 'WARNING': 1, 'MONITORING': 2}
        active_alerts.sort(key=lambda x: (priority_order.get(x['type'], 3), x['timestamp']))
        
        return active_alerts
    
    def save_alert_config(self):
        """Save alert configuration to file"""
        config = {
            'thresholds': self.alert_thresholds,
            'field_locations': self.field_locations,
            'last_updated': datetime.now().isoformat()
        }
        
        with open('alert_configuration.json', 'w') as f:
            json.dump(config, f, indent=2)

    def save_active_alerts(self):
        """Save active alerts to JSON for dashboard integration"""
        active_alerts = self.get_active_alerts()
        with open('active_alerts.json', 'w') as f:
            json.dump(active_alerts, f, indent=2)
        print(f"✅ Active alerts saved to active_alerts.json ({len(active_alerts)} alerts)")
    
    def load_alert_config(self):
        """Load alert configuration from file"""
        try:
            with open('alert_configuration.json', 'r') as f:
                config = json.load(f)
                self.alert_thresholds = config.get('thresholds', self.alert_thresholds)
                self.field_locations = config.get('field_locations', self.field_locations)
            return True
        except:
            return False

# Test the alert system
if __name__ == "__main__":
    alert_system = ActionableAlertsSystem()
    
    # Test with sample data including new sensors
    current_data = {
        'NDVI_mean': 0.45,
        'Temperature': 36,
        'Humidity': 82,
        'soil_moisture_mean': 38,
        'Soil_pH': 4.5,
        'Soil_Temperature': 8,
        'Light_Intensity': 150
    }
    
    historical_data = [
        {'NDVI_mean': 0.55, 'Temperature': 28, 'Humidity': 65, 'soil_moisture_mean': 45},
        {'NDVI_mean': 0.52, 'Temperature': 30, 'Humidity': 70, 'soil_moisture_mean': 42},
        {'NDVI_mean': 0.48, 'Temperature': 33, 'Humidity': 75, 'soil_moisture_mean': 40}
    ]
    
    alerts = alert_system.process_field_data('North', current_data, historical_data)
    
    print("🚨 ACTIONABLE ALERTS SYSTEM - SEASON 2 TEST")
    print("="*50)
    print(f"Generated {len(alerts)} alerts for North field:")
    
    for alert in alerts:
        print(f"\n{alert['type']} {alert['category']} ALERT")
        print(f"Field: {alert['field']} at {alert['coordinates']}")
        print(f"Message: {alert['message']}")
        print(f"Action: {alert['action']}")
        print(f"Time: {alert['time_sensitivity']}")
        print(f"Impact: {alert['impact']}")
        print(f"Confidence: {alert['confidence']}%")
    
    # Save configuration
    alert_system.save_alert_config()
    print(f"\n✅ Alert configuration saved to alert_configuration.json")
    
    # Save active alerts for dashboard
    alert_system.save_active_alerts()
