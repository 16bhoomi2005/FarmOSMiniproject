#!/usr/bin/env python3
"""
AI-Powered Farmer Recommendation Engine
Provides actionable advice based on sensor data, satellite imagery, and crop growth stage
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FarmerRecommendationEngine:
    """Generate intelligent farming recommendations"""
    
    def __init__(self, 
                 sensor_data_file='sample_ground_sensor_data.csv',
                 satellite_file='latest_satellite_features.json',
                 trend_file='satellite_trend_analysis.json'):
        self.sensor_file = sensor_data_file
        self.satellite_file = satellite_file
        self.trend_file = trend_file
        self.recommendations = []
        
    def analyze_and_recommend(self):
        """Main analysis function"""
        
        print("🧠 AI Recommendation Engine Starting...")
        
        # Load all data sources
        sensor_data = self._load_sensor_data()
        satellite_data = self._load_satellite_data()
        trend_data = self._load_trend_data()
        
        # Generate recommendations
        self.recommendations = []
        
        # 1. Irrigation recommendations
        self._check_irrigation_needs(sensor_data)
        
        # 2. Fertilization recommendations
        self._check_fertilization_needs(sensor_data, satellite_data)
        
        # 3. Pest/disease risk
        self._check_pest_disease_risk(sensor_data, satellite_data)
        
        # 4. Harvest timing
        self._check_harvest_timing(satellite_data, trend_data)
        
        # 5. Soil health
        self._check_soil_health(sensor_data)
        
        # 6. Weather-based actions
        self._check_weather_actions(sensor_data)
        
        # 7. Crop stress detection
        self._check_crop_stress(satellite_data, trend_data)
        
        # Sort by priority
        self.recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return self.recommendations
    
    def _load_sensor_data(self):
        """Load ground sensor data"""
        if os.path.exists(self.sensor_file):
            df = pd.read_csv(self.sensor_file)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        return None
    
    def _load_satellite_data(self):
        """Load satellite features"""
        if os.path.exists(self.satellite_file):
            with open(self.satellite_file, 'r') as f:
                return json.load(f)
        return None
    
    def _load_trend_data(self):
        """Load trend analysis"""
        if os.path.exists(self.trend_file):
            with open(self.trend_file, 'r') as f:
                return json.load(f)
        return None
    
    def _check_irrigation_needs(self, sensor_data):
        """Recommend irrigation based on soil moisture"""
        if sensor_data is None or len(sensor_data) == 0:
            return
        
        latest = sensor_data.iloc[-1]
        moisture = latest['Soil_Moisture']
        temp = latest['Temperature']
        
        # Critical: Immediate irrigation needed
        if moisture < 25:
            self.recommendations.append({
                'category': '💧 Irrigation',
                'priority': 10,
                'urgency': 'CRITICAL',
                'title': 'Immediate Irrigation Required',
                'issue': f'Soil moisture critically low at {moisture:.1f}%',
                'action': 'Irrigate immediately (2-3 inches of water)',
                'reason': 'Severe water stress can cause permanent crop damage',
                'timeline': 'Within 2 hours',
                'cost_impact': 'High yield loss if delayed'
            })
        
        # High: Irrigation recommended
        elif moisture < 35:
            self.recommendations.append({
                'category': '💧 Irrigation',
                'priority': 8,
                'urgency': 'HIGH',
                'title': 'Irrigation Recommended',
                'issue': f'Soil moisture low at {moisture:.1f}%',
                'action': 'Schedule irrigation within 24 hours',
                'reason': 'Crops entering water stress zone',
                'timeline': 'Within 24 hours',
                'cost_impact': 'Moderate yield reduction if delayed'
            })
        
        # Over-watered
        elif moisture > 80:
            self.recommendations.append({
                'category': '💧 Irrigation',
                'priority': 7,
                'urgency': 'HIGH',
                'title': 'Stop Irrigation - Waterlogging Risk',
                'issue': f'Soil moisture too high at {moisture:.1f}%',
                'action': 'Stop all irrigation, improve drainage',
                'reason': 'Waterlogging causes root rot and fungal diseases',
                'timeline': 'Immediate',
                'cost_impact': 'Disease risk, reduced yields'
            })
    
    def _check_fertilization_needs(self, sensor_data, satellite_data):
        """Recommend fertilization based on NDVI and soil pH"""
        if sensor_data is None or satellite_data is None:
            return
        
        latest = sensor_data.iloc[-1]
        ph = latest['Soil_pH']
        ndvi = satellite_data.get('NDVI_mean', 0.5)
        
        # Low NDVI + Good pH = Nutrient deficiency
        if ndvi < 0.4 and 6.0 <= ph <= 7.5:
            self.recommendations.append({
                'category': '🌱 Fertilization',
                'priority': 9,
                'urgency': 'HIGH',
                'title': 'Nitrogen Deficiency Detected',
                'issue': f'Low NDVI ({ndvi:.2f}) with optimal pH',
                'action': 'Apply nitrogen fertilizer (Urea 50kg/acre)',
                'reason': 'Satellite shows poor vegetation vigor despite good soil pH',
                'timeline': 'Within 1 week',
                'cost_impact': '₹2,000/acre, +15% yield potential'
            })
        
        # pH too low
        if ph < 6.0:
            self.recommendations.append({
                'category': '🌱 Fertilization',
                'priority': 8,
                'urgency': 'HIGH',
                'title': 'Soil Acidification - Apply Lime',
                'issue': f'Soil pH too acidic at {ph:.1f}',
                'action': 'Apply agricultural lime (200kg/acre)',
                'reason': 'Acidic soil blocks nutrient uptake',
                'timeline': 'Before next planting',
                'cost_impact': '₹1,500/acre, improves nutrient availability'
            })
        
        # pH too high
        elif ph > 7.5:
            self.recommendations.append({
                'category': '🌱 Fertilization',
                'priority': 7,
                'urgency': 'MEDIUM',
                'title': 'Soil Alkalinity - Apply Sulfur',
                'issue': f'Soil pH too alkaline at {ph:.1f}',
                'action': 'Apply elemental sulfur (50kg/acre)',
                'reason': 'Alkaline soil reduces iron and zinc availability',
                'timeline': 'Within 2 weeks',
                'cost_impact': '₹800/acre, prevents micronutrient deficiency'
            })
    
    def _check_pest_disease_risk(self, sensor_data, satellite_data):
        """Predict pest/disease risk based on conditions"""
        if sensor_data is None:
            return
        
        latest = sensor_data.iloc[-1]
        temp = latest['Temperature']
        humidity = latest['Humidity']
        
        # High risk: Warm + Humid
        if temp > 25 and humidity > 80:
            self.recommendations.append({
                'category': '🐛 Pest Control',
                'priority': 8,
                'urgency': 'HIGH',
                'title': 'Fungal Disease Risk - High',
                'issue': f'Temp {temp:.1f}°C + Humidity {humidity:.1f}% = Ideal for fungi',
                'action': 'Apply preventive fungicide, scout for leaf spots',
                'reason': 'Warm humid conditions favor fungal growth',
                'timeline': 'Within 48 hours',
                'cost_impact': '₹1,000/acre prevention vs ₹5,000+ treatment'
            })
        
        # Pest pressure
        if temp > 30 and humidity < 50:
            self.recommendations.append({
                'category': '🐛 Pest Control',
                'priority': 6,
                'urgency': 'MEDIUM',
                'title': 'Insect Pest Activity Increasing',
                'issue': f'Hot dry conditions ({temp:.1f}°C) favor pests',
                'action': 'Scout for aphids, whiteflies, and thrips',
                'reason': 'Hot weather increases insect reproduction',
                'timeline': 'Daily monitoring',
                'cost_impact': 'Early detection saves ₹3,000/acre'
            })
    
    def _check_harvest_timing(self, satellite_data, trend_data):
        """Recommend optimal harvest timing"""
        if satellite_data is None or trend_data is None:
            return
        
        ndvi = satellite_data.get('NDVI_mean', 0.5)
        trend = trend_data.get('analysis', {}).get('ndvi_trend', 0)
        
        # NDVI declining = maturity
        if ndvi > 0.5 and trend < -0.05:
            self.recommendations.append({
                'category': '🌾 Harvest',
                'priority': 9,
                'urgency': 'HIGH',
                'title': 'Crop Approaching Maturity',
                'issue': f'NDVI declining from peak (trend: {trend:.3f})',
                'action': 'Plan harvest in 2-3 weeks, monitor grain moisture',
                'reason': 'Satellite shows crop senescence beginning',
                'timeline': '14-21 days',
                'cost_impact': 'Optimal timing = +10% market price'
            })
        
        # Peak NDVI = mid-season
        elif ndvi > 0.6:
            self.recommendations.append({
                'category': '🌾 Harvest',
                'priority': 4,
                'urgency': 'INFO',
                'title': 'Crop at Peak Vigor',
                'issue': f'High NDVI ({ndvi:.2f}) indicates active growth',
                'action': 'Continue monitoring, harvest in 4-6 weeks',
                'reason': 'Crop still accumulating biomass',
                'timeline': '30-45 days',
                'cost_impact': 'Premature harvest = 30% yield loss'
            })
    
    def _check_soil_health(self, sensor_data):
        """Assess overall soil health"""
        if sensor_data is None or len(sensor_data) < 7:
            return
        
        # Check pH stability
        recent = sensor_data.tail(7)
        ph_std = recent['Soil_pH'].std()
        
        if ph_std > 0.5:
            self.recommendations.append({
                'category': '🌍 Soil Health',
                'priority': 5,
                'urgency': 'MEDIUM',
                'title': 'Soil pH Fluctuating',
                'issue': f'pH varying by ±{ph_std:.2f} over past week',
                'action': 'Test soil, check for contamination or drainage issues',
                'reason': 'Unstable pH indicates soil imbalance',
                'timeline': 'Within 1 week',
                'cost_impact': 'Soil test: ₹500, prevents long-term issues'
            })
    
    def _check_weather_actions(self, sensor_data):
        """Weather-based recommendations"""
        if sensor_data is None:
            return
        
        latest = sensor_data.iloc[-1]
        temp = latest['Temperature']
        
        # Heat stress
        if temp > 38:
            self.recommendations.append({
                'category': '🌡️ Weather',
                'priority': 7,
                'urgency': 'HIGH',
                'title': 'Heat Stress Alert',
                'issue': f'Extreme temperature: {temp:.1f}°C',
                'action': 'Increase irrigation frequency, apply mulch',
                'reason': 'Temperatures >38°C cause protein denaturation',
                'timeline': 'Immediate',
                'cost_impact': 'Heat stress = 20% yield loss'
            })
        
        # Cold stress
        elif temp < 10:
            self.recommendations.append({
                'category': '🌡️ Weather',
                'priority': 6,
                'urgency': 'MEDIUM',
                'title': 'Cold Stress Warning',
                'issue': f'Low temperature: {temp:.1f}°C',
                'action': 'Delay planting, protect seedlings if already planted',
                'reason': 'Cold slows growth and increases disease risk',
                'timeline': 'Monitor daily',
                'cost_impact': 'Cold damage = germination failure'
            })
    
    def _check_crop_stress(self, satellite_data, trend_data):
        """Detect crop stress from satellite data"""
        if satellite_data is None or trend_data is None:
            return
        
        ndvi = satellite_data.get('NDVI_mean', 0.5)
        historical = trend_data.get('historical_baseline', {}).get('NDVI_mean', 0.5)
        
        # Severe decline
        if ndvi < historical * 0.7:
            self.recommendations.append({
                'category': '⚠️ Crop Stress',
                'priority': 10,
                'urgency': 'CRITICAL',
                'title': 'Severe Crop Stress Detected',
                'issue': f'NDVI 30% below normal ({ndvi:.2f} vs {historical:.2f})',
                'action': 'Immediate field inspection, check for disease/pests/drought',
                'reason': 'Satellite shows significant vegetation decline',
                'timeline': 'Within 4 hours',
                'cost_impact': 'Potential crop failure if not addressed'
            })
    
    def save_recommendations(self, filename='farmer_recommendations.json'):
        """Save recommendations to file"""
        with open(filename, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_recommendations': len(self.recommendations),
                'recommendations': self.recommendations
            }, f, indent=2)
        
        print(f"\n✅ Saved {len(self.recommendations)} recommendations to {filename}")
    
    def print_summary(self):
        """Print recommendations summary"""
        print("\n" + "="*70)
        print("🧠 AI FARMER RECOMMENDATIONS")
        print("="*70)
        
        if not self.recommendations:
            print("\n✅ No urgent actions needed - All systems optimal!")
            return
        
        # Group by urgency
        critical = [r for r in self.recommendations if r['urgency'] == 'CRITICAL']
        high = [r for r in self.recommendations if r['urgency'] == 'HIGH']
        medium = [r for r in self.recommendations if r['urgency'] == 'MEDIUM']
        info = [r for r in self.recommendations if r['urgency'] == 'INFO']
        
        if critical:
            print(f"\n🔴 CRITICAL ACTIONS ({len(critical)}):")
            for rec in critical:
                print(f"\n   {rec['category']} - {rec['title']}")
                print(f"   Issue: {rec['issue']}")
                print(f"   Action: {rec['action']}")
                print(f"   Timeline: {rec['timeline']}")
        
        if high:
            print(f"\n🟡 HIGH PRIORITY ({len(high)}):")
            for rec in high:
                print(f"\n   {rec['category']} - {rec['title']}")
                print(f"   Action: {rec['action']}")
                print(f"   Timeline: {rec['timeline']}")
        
        if medium:
            print(f"\n🟢 MEDIUM PRIORITY ({len(medium)}):")
            for rec in medium:
                print(f"   • {rec['title']}")
        
        if info:
            print(f"\n🔵 INFORMATIONAL ({len(info)}):")
            for rec in info:
                print(f"   • {rec['title']}")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    import json
    from datetime import datetime
    
    engine = FarmerRecommendationEngine()
    results = engine.analyze_and_recommend()
    
    # Save output
    output = {
        'generated_at': datetime.now().isoformat(),
        'recommendations': results
    }
    
    output_file = 'farmer_recommendations.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=4)
    
    print(f"\n✅ {len(results)} recommendations generated")
    print(f"📄 Full details saved to: {output_file}")
