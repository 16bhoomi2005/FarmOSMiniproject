#!/usr/bin/env python3
"""
Season Report Generator for Smart Farm AI
Aggregates satellite and sensor data into a professional summary
"""

import json
import os
import pandas as pd
from datetime import datetime

class SeasonReportGenerator:
    def __init__(self, output_file='season_report_2026.json'):
        self.output_file = output_file
        self.data_sources = {
            'sensors': 'sample_ground_sensor_data.csv',
            'satellite': 'satellite_trend_analysis.json',
            'alerts': 'active_alerts.json'
        }

    def generate(self):
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'farm_id': 'Bhandara_District_B01',
                'season_id': '2026_Kharif_Early'
            },
            'performance_summary': {},
            'infrastructure_health': {},
            'economic_impact': {}
        }

        # 1. Load Data
        df = pd.read_csv(self.data_sources['sensors']) if os.path.exists(self.data_sources['sensors']) else None
        trends = {}
        if os.path.exists(self.data_sources['satellite']):
            with open(self.data_sources['satellite'], 'r') as f:
                trends = json.load(f)

        # 2. Extract Performance
        if trends:
            report['performance_summary']['ndvi_trend'] = trends.get('analysis', {}).get('ndvi_trend', 0)
            report['performance_summary']['health_status'] = "Improving" if report['performance_summary']['ndvi_trend'] > 0 else "Declining"
        
        if df is not None:
            report['infrastructure_health']['avg_moisture'] = df['Soil_Moisture'].mean()
            report['infrastructure_health']['soil_ph_avg'] = df['Soil_pH'].mean()
            report['infrastructure_health']['system_uptime_days'] = len(df)

        # 3. Save Report
        with open(self.output_file, 'w') as f:
            json.dump(report, f, indent=4)
        
        return self.output_file

if __name__ == "__main__":
    gen = SeasonReportGenerator()
    path = gen.generate()
    print(f"✅ Season Report Generated at: {path}")
