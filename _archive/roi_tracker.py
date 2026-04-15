#!/usr/bin/env python3
"""
ROI & Farm Impact Tracking System
Monitor yield improvements, cost savings, and time efficiency
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class ROITracker:
    def __init__(self):
        self.yield_data = []
        self.cost_data = []
        self.time_data = []
        self.prediction_accuracy = []
        self.baseline_metrics = self.setup_baseline_metrics()
        
    def setup_baseline_metrics(self):
        """Establish baseline metrics for comparison"""
        return {
            'yield_per_hectare': 68,  # tons/ha (before system)
            'water_cost_per_month': 1200,  # $/month
            'fertilizer_cost_per_month': 800,  # $/month
            'labor_hours_per_week': 20,  # hours/week
            'labor_cost_per_hour': 15,  # $/hour
            'energy_cost_per_month': 400,  # $/month
            'prediction_accuracy': 0.55  # 55% before system
        }
    
    def record_yield_performance(self, field_name, predicted_yield, actual_yield, season_month):
        """Record yield performance with predictions vs actual"""
        variance = actual_yield - predicted_yield
        accuracy = 1 - abs(variance / predicted_yield) if predicted_yield > 0 else 0
        
        record = {
            'field': field_name,
            'season_month': season_month,
            'predicted_yield': predicted_yield,
            'actual_yield': actual_yield,
            'variance': variance,
            'accuracy': accuracy,
            'revenue_impact': variance * 200,  # $200 per ton
            'timestamp': datetime.now().isoformat()
        }
        
        self.yield_data.append(record)
        self.prediction_accuracy.append(accuracy)
        
        return record
    
    def record_cost_savings(self, category, current_cost, baseline_cost=None):
        """Record cost savings across different categories"""
        if baseline_cost is None:
            baseline_cost = self.baseline_metrics.get(f'{category}_cost_per_month', current_cost)
        
        savings = baseline_cost - current_cost
        percentage_savings = (savings / baseline_cost) * 100 if baseline_cost > 0 else 0
        
        record = {
            'category': category,
            'baseline_cost': baseline_cost,
            'current_cost': current_cost,
            'savings': savings,
            'percentage_savings': percentage_savings,
            'annual_savings': savings * 12,
            'timestamp': datetime.now().isoformat()
        }
        
        self.cost_data.append(record)
        
        return record
    
    def record_time_savings(self, manual_hours, automated_hours, activity):
        """Record time savings from automation"""
        hours_saved = manual_hours - automated_hours
        cost_savings = hours_saved * self.baseline_metrics['labor_cost_per_hour']
        
        record = {
            'activity': activity,
            'manual_hours': manual_hours,
            'automated_hours': automated_hours,
            'hours_saved': hours_saved,
            'cost_savings': cost_savings,
            'percentage_reduction': (hours_saved / manual_hours) * 100 if manual_hours > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.time_data.append(record)
        
        return record
    
    def calculate_monthly_roi(self):
        """Calculate comprehensive monthly ROI metrics"""
        # Yield improvements
        current_month_yields = [r for r in self.yield_data 
                              if datetime.fromisoformat(r['timestamp']).month == datetime.now().month]
        
        total_yield_variance = sum(r['variance'] for r in current_month_yields)
        yield_revenue_impact = total_yield_variance * 200  # $200 per ton
        
        # Cost savings
        current_month_costs = [r for r in self.cost_data 
                              if datetime.fromisoformat(r['timestamp']).month == datetime.now().month]
        
        total_cost_savings = sum(r['savings'] for r in current_month_costs)
        
        # Time savings
        current_month_time = [r for r in self.time_data 
                            if datetime.fromisoformat(r['timestamp']).month == datetime.now().month]
        
        total_time_savings = sum(r['cost_savings'] for r in current_month_time)
        
        # Total monthly impact
        total_monthly_impact = yield_revenue_impact + total_cost_savings + total_time_savings
        
        # System cost (estimated)
        system_monthly_cost = 500  # $500/month for system maintenance
        
        # ROI calculation
        monthly_roi = (total_monthly_impact / system_monthly_cost) * 100 if system_monthly_cost > 0 else 0
        
        return {
            'yield_revenue_impact': yield_revenue_impact,
            'cost_savings': total_cost_savings,
            'time_savings': total_time_savings,
            'total_monthly_impact': total_monthly_impact,
            'system_cost': system_monthly_cost,
            'monthly_roi': monthly_roi,
            'prediction_accuracy': np.mean(self.prediction_accuracy) if self.prediction_accuracy else 0
        }
    
    def generate_performance_dashboard(self):
        """Generate comprehensive performance dashboard data"""
        # Field-by-field performance
        field_performance = {}
        for field in ['North', 'East', 'Center', 'South', 'West']:
            field_yields = [r for r in self.yield_data if r['field'] == field]
            if field_yields:
                avg_accuracy = np.mean([r['accuracy'] for r in field_yields])
                total_variance = sum([r['variance'] for r in field_yields])
                field_performance[field] = {
                    'accuracy': avg_accuracy,
                    'total_variance': total_variance,
                    'revenue_impact': total_variance * 200,
                    'predictions_count': len(field_yields)
                }
        
        # Monthly trends
        monthly_trends = {}
        for month in range(1, 13):
            month_yields = [r for r in self.yield_data 
                          if datetime.fromisoformat(r['timestamp']).month == month]
            month_costs = [r for r in self.cost_data 
                          if datetime.fromisoformat(r['timestamp']).month == month]
            
            if month_yields or month_costs:
                monthly_trends[month] = {
                    'yield_accuracy': np.mean([r['accuracy'] for r in month_yields]) if month_yields else 0,
                    'cost_savings': sum([r['savings'] for r in month_costs]) if month_costs else 0,
                    'predictions_count': len(month_yields)
                }
        
        # Current month ROI
        current_roi = self.calculate_monthly_roi()
        
        return {
            'field_performance': field_performance,
            'monthly_trends': monthly_trends,
            'current_month_roi': current_roi,
            'baseline_metrics': self.baseline_metrics,
            'total_predictions': len(self.yield_data),
            'average_prediction_accuracy': np.mean(self.prediction_accuracy) if self.prediction_accuracy else 0
        }
    
    def generate_roi_report(self):
        """Generate comprehensive ROI report for dashboard"""
        dashboard_data = self.generate_performance_dashboard()
        current_roi = dashboard_data['current_month_roi']
        
        report = {
            'summary': {
                'monthly_roi': f"{current_roi['monthly_roi']:.0f}%",
                'prediction_accuracy': f"{current_roi['prediction_accuracy']*100:.0f}%",
                'monthly_impact': f"${current_roi['total_monthly_impact']:.0f}",
                'yield_improvement': f"${current_roi['yield_revenue_impact']:.0f}",
                'cost_savings': f"${current_roi['cost_savings']:.0f}",
                'time_savings': f"${current_roi['time_savings']:.0f}"
            },
            'field_breakdown': {},
            'trends': dashboard_data['monthly_trends'],
            'recommendations': self.generate_recommendations(current_roi)
        }
        
        # Field breakdown
        for field, performance in dashboard_data['field_performance'].items():
            report['field_breakdown'][field] = {
                'accuracy': f"{performance['accuracy']*100:.0f}%",
                'variance': f"{performance['total_variance']:+.1f} tons/ha",
                'revenue_impact': f"${performance['revenue_impact']:.0f}",
                'predictions': performance['predictions_count']
            }
        
        return report
    
    def generate_recommendations(self, current_roi):
        """Generate actionable recommendations based on ROI data"""
        recommendations = []
        
        if current_roi['prediction_accuracy'] < 0.9:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Improve prediction accuracy',
                'impact': 'Better harvest planning',
                'expected_roi_increase': '+15%'
            })
        
        if current_roi['cost_savings'] < 2000:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Optimize input usage',
                'impact': 'Reduce fertilizer and water costs',
                'expected_roi_increase': '+10%'
            })
        
        if current_roi['time_savings'] < 2000:
            recommendations.append({
                'priority': 'LOW',
                'action': 'Expand automation',
                'impact': 'Reduce manual monitoring time',
                'expected_roi_increase': '+5%'
            })
        
        return recommendations
    
    def save_roi_data(self):
        """Save ROI tracking data to files"""
        # Save yield data
        yield_df = pd.DataFrame(self.yield_data)
        yield_df.to_csv('roi_yield_tracking.csv', index=False)
        
        # Save cost data
        cost_df = pd.DataFrame(self.cost_data)
        cost_df.to_csv('roi_cost_tracking.csv', index=False)
        
        # Save time data
        time_df = pd.DataFrame(self.time_data)
        time_df.to_csv('roi_time_tracking.csv', index=False)
        
        # Save dashboard data
        dashboard_data = self.generate_performance_dashboard()
        with open('roi_dashboard_data.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        # Save ROI report
        report = self.generate_roi_report()
        with open('roi_report.json', 'w') as f:
            json.dump(report, f, indent=2)
    
    def load_roi_data(self):
        """Load ROI tracking data from files"""
        try:
            # Load yield data
            if os.path.exists('roi_yield_tracking.csv'):
                yield_df = pd.read_csv('roi_yield_tracking.csv')
                self.yield_data = yield_df.to_dict('records')
            
            # Load cost data
            if os.path.exists('roi_cost_tracking.csv'):
                cost_df = pd.read_csv('roi_cost_tracking.csv')
                self.cost_data = cost_df.to_dict('records')
            
            # Load time data
            if os.path.exists('roi_time_tracking.csv'):
                time_df = pd.read_csv('roi_time_tracking.csv')
                self.time_data = time_df.to_dict('records')
            
            return True
        except Exception as e:
            print(f"Error loading ROI data: {e}")
            return False

# Test the ROI tracker
if __name__ == "__main__":
    roi_tracker = ROITracker()
    
    print("💰 ROI & FARM IMPACT TRACKING SYSTEM")
    print("="*50)
    
    # Simulate some data
    # Yield performance
    roi_tracker.record_yield_performance('North', 72, 73, 'January')
    roi_tracker.record_yield_performance('East', 65, 64, 'January')
    roi_tracker.record_yield_performance('Center', 70, 71, 'January')
    roi_tracker.record_yield_performance('South', 66, 67, 'January')
    roi_tracker.record_yield_performance('West', 71, 72, 'January')
    
    # Cost savings
    roi_tracker.record_cost_savings('water', 900, 1200)  # $300 saved
    roi_tracker.record_cost_savings('fertilizer', 650, 800)  # $150 saved
    roi_tracker.record_cost_savings('energy', 280, 400)  # $120 saved
    
    # Time savings
    roi_tracker.record_time_savings(20, 2, 'Field monitoring')  # 18 hours saved
    roi_tracker.record_time_savings(5, 1, 'Data analysis')  # 4 hours saved
    
    # Generate report
    report = roi_tracker.generate_roi_report()
    
    print("\n📊 CURRENT MONTH ROI SUMMARY:")
    summary = report['summary']
    for key, value in summary.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print("\n🌾 FIELD PERFORMANCE:")
    for field, performance in report['field_breakdown'].items():
        print(f"   {field}: Accuracy {performance['accuracy']}, Variance {performance['variance']}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"   {rec['priority']}: {rec['action']} - {rec['impact']}")
    
    # Save data
    roi_tracker.save_roi_data()
    print(f"\n✅ ROI data saved to files")
    print(f"   - roi_yield_tracking.csv")
    print(f"   - roi_cost_tracking.csv")
    print(f"   - roi_time_tracking.csv")
    print(f"   - roi_dashboard_data.json")
    print(f"   - roi_report.json")
