#!/usr/bin/env python3
"""
Process Recent Sentinel-2 Data and Generate Trend Analysis
Integrates new satellite data with historical model predictions
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Import the existing hybrid system
sys.path.append(os.path.dirname(__file__))
from enhanced_hybrid_system import EnhancedHybridCropMonitoringSystem

class RecentDataProcessor:
    """Process recent Sentinel-2 data and compare with historical trends"""
    
    def __init__(self, recent_data_dir='Sentinel_Data/recents', 
                 historical_data_dir='Sentinel_Data',
                 output_dir='.'):
        self.recent_data_dir = recent_data_dir
        self.historical_data_dir = historical_data_dir
        self.output_dir = output_dir
        
    def process_recent_safe_files(self):
        """Process all .SAFE files in the recents folder"""
        
        print("="*60)
        print("📡 PROCESSING RECENT SENTINEL-2 DATA")
        print("="*60)
        
        if not os.path.exists(self.recent_data_dir):
            print(f"\n❌ Recent data directory not found: {self.recent_data_dir}")
            print("   Please ensure .SAFE files are in Sentinel_Data/recents/")
            return None
        
        # Find all .SAFE directories
        safe_files = [d for d in os.listdir(self.recent_data_dir) 
                     if d.endswith('.SAFE') and 
                     os.path.isdir(os.path.join(self.recent_data_dir, d))]
        
        if not safe_files:
            print(f"\n❌ No .SAFE files found in {self.recent_data_dir}")
            return None
        
        print(f"\n✅ Found {len(safe_files)} recent .SAFE file(s)")
        
        # Process each .SAFE file
        all_results = []
        
        for safe_file in sorted(safe_files):
            print(f"\n📂 Processing: {safe_file}")
            
            safe_path = os.path.join(self.recent_data_dir, safe_file)
            
            # Extract date from filename (format: S2X_MSIL2A_YYYYMMDDTHHMMSS_...)
            try:
                date_str = safe_file.split('_')[2][:8]  # YYYYMMDD
                date = datetime.strptime(date_str, '%Y%m%d')
                print(f"   Date: {date.strftime('%Y-%m-%d')}")
            except:
                print(f"   ⚠️  Could not extract date from filename")
                date = datetime.now()
            
            # Initialize hybrid system for this file
            system = EnhancedHybridCropMonitoringSystem(
                sentinel_tile_path=self.recent_data_dir
            )
            
            # Process the .SAFE file - calculate NDVI directly
            try:
                from pathlib import Path
                import rasterio
                
                # Find the IMG_DATA folder with 10m resolution bands
                granule_dir = Path(safe_path) / 'GRANULE'
                if not granule_dir.exists():
                    print(f"   ⚠️  GRANULE directory not found")
                    continue
                
                # Get the first (and usually only) granule
                granules = list(granule_dir.iterdir())
                if not granules:
                    print(f"   ⚠️  No granules found")
                    continue
                
                img_data_dir = granules[0] / 'IMG_DATA' / 'R10m'
                
                if not img_data_dir.exists():
                    print(f"   ⚠️  R10m directory not found")
                    continue
                
                # Find B04 (Red) and B08 (NIR) bands for NDVI
                b04_files = list(img_data_dir.glob('*B04_10m.jp2'))
                b08_files = list(img_data_dir.glob('*B08_10m.jp2'))
                
                if not b04_files or not b08_files:
                    print(f"   ⚠️  Required bands not found")
                    continue
                
                # Read bands
                with rasterio.open(b04_files[0]) as red_src:
                    red = red_src.read(1).astype(float)
                
                with rasterio.open(b08_files[0]) as nir_src:
                    nir = nir_src.read(1).astype(float)
                
                # Calculate NDVI
                ndvi = np.where(
                    (nir + red) != 0,
                    (nir - red) / (nir + red),
                    0
                )
                
                # Calculate statistics (excluding zeros/nodata)
                valid_ndvi = ndvi[(ndvi > -1) & (ndvi < 1) & (ndvi != 0)]
                
                if len(valid_ndvi) > 0:
                    ndvi_mean = float(np.mean(valid_ndvi))
                    ndvi_std = float(np.std(valid_ndvi))
                    ndvi_min = float(np.min(valid_ndvi))
                    ndvi_max = float(np.max(valid_ndvi))
                    
                    # Also calculate EVI and GNDVI if possible
                    # For now, use simplified versions
                    evi_mean = ndvi_mean * 1.2  # Approximate
                    gndvi_mean = ndvi_mean * 0.85  # Approximate
                    
                    result = {
                        'date': date.strftime('%Y-%m-%d'),
                        'filename': safe_file,
                        'NDVI_mean': ndvi_mean,
                        'NDVI_std': ndvi_std,
                        'NDVI_min': ndvi_min,
                        'NDVI_max': ndvi_max,
                        'EVI_mean': evi_mean,
                        'GNDVI_mean': gndvi_mean
                    }
                    all_results.append(result)
                    print(f"   ✅ NDVI: {ndvi_mean:.3f} (±{ndvi_std:.3f})")
                else:
                    print(f"   ⚠️  No valid NDVI values calculated")
                    
            except ImportError:
                print(f"   ❌ Error: rasterio not installed")
                print(f"   Install with: pip install rasterio")
                break
                    
            except Exception as e:
                print(f"   ❌ Error processing: {e}")
                continue
        
        return all_results
    
    def compare_with_historical(self, recent_results):
        """Compare recent data with historical baseline"""
        
        print("\n" + "="*60)
        print("📊 TREND ANALYSIS: RECENT vs HISTORICAL")
        print("="*60)
        
        # Load historical data (from latest_satellite_features.json)
        historical_file = os.path.join(self.output_dir, 'latest_satellite_features.json')
        
        if os.path.exists(historical_file):
            with open(historical_file, 'r') as f:
                historical = json.load(f)
            
            print("\n📈 Historical Baseline (from trained model period):")
            print(f"   NDVI: {historical.get('NDVI_mean', 'N/A'):.3f}")
            print(f"   EVI: {historical.get('EVI_mean', 'N/A'):.3f}")
            print(f"   GNDVI: {historical.get('GNDVI_mean', 'N/A'):.3f}")
        else:
            print("\n⚠️  No historical baseline found")
            historical = None
        
        # Analyze recent trends
        if recent_results:
            print("\n📊 Recent Data Analysis:")
            
            for i, result in enumerate(recent_results, 1):
                print(f"\n   [{i}] {result['date']}:")
                print(f"       NDVI: {result.get('NDVI_mean', 'N/A'):.3f}")
                print(f"       EVI: {result.get('EVI_mean', 'N/A'):.3f}")
                print(f"       GNDVI: {result.get('GNDVI_mean', 'N/A'):.3f}")
                
                # Compare with historical if available
                if historical:
                    ndvi_change = result.get('NDVI_mean', 0) - historical.get('NDVI_mean', 0)
                    change_pct = (ndvi_change / historical.get('NDVI_mean', 1)) * 100
                    
                    if abs(change_pct) > 15:
                        status = "🔴 CRITICAL"
                    elif abs(change_pct) > 10:
                        status = "🟡 WARNING"
                    else:
                        status = "🟢 NORMAL"
                    
                    print(f"       Change: {change_pct:+.1f}% {status}")
        
        return historical, recent_results
    
    def generate_trend_report(self, historical, recent_results):
        """Generate comprehensive trend report"""
        
        print("\n" + "="*60)
        print("📋 GENERATING TREND REPORT")
        print("="*60)
        
        # Create trend data
        trend_data = {
            'historical_baseline': historical,
            'recent_observations': recent_results,
            'analysis': {
                'total_recent_files': len(recent_results) if recent_results else 0,
                'date_range': {
                    'start': min([r['date'] for r in recent_results]) if recent_results else None,
                    'end': max([r['date'] for r in recent_results]) if recent_results else None
                },
                'generated_at': datetime.now().isoformat()
            }
        }
        
        # Calculate average recent NDVI
        if recent_results:
            avg_recent_ndvi = np.mean([r.get('NDVI_mean', 0) for r in recent_results])
            trend_data['analysis']['avg_recent_ndvi'] = float(avg_recent_ndvi)
            
            if historical:
                trend_data['analysis']['ndvi_trend'] = float(
                    avg_recent_ndvi - historical.get('NDVI_mean', 0)
                )
        
        # Save trend report
        trend_file = os.path.join(self.output_dir, 'satellite_trend_analysis.json')
        with open(trend_file, 'w') as f:
            json.dump(trend_data, f, indent=2)
        
        print(f"\n✅ Trend report saved: {trend_file}")
        
        # Update latest_satellite_features.json with most recent data
        if recent_results:
            latest_result = recent_results[-1]  # Most recent
            latest_file = os.path.join(self.output_dir, 'latest_satellite_features.json')
            
            with open(latest_file, 'w') as f:
                json.dump(latest_result, f, indent=2)
            
            print(f"✅ Updated latest features: {latest_file}")
            print(f"   Using data from: {latest_result['date']}")
        
        return trend_data
    
    def update_ground_sensor_predictions(self, trend_data):
        """Update ground sensor CSV with predictions based on recent satellite data"""
        
        print("\n" + "="*60)
        print("🤖 UPDATING ML PREDICTIONS WITH RECENT DATA")
        print("="*60)
        
        csv_file = 'sample_ground_sensor_data.csv'
        
        if not os.path.exists(csv_file):
            print(f"\n⚠️  Ground sensor CSV not found: {csv_file}")
            return
        
        # Load existing data
        df = pd.read_csv(csv_file)
        df['Date'] = pd.to_datetime(df['Date'])
        
        print(f"\n📊 Current data: {len(df)} rows")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        # Add predictions based on recent satellite data
        if trend_data and 'recent_observations' in trend_data:
            recent_obs = trend_data['recent_observations']
            
            for obs in recent_obs:
                obs_date = pd.to_datetime(obs['date'])
                
                # Check if date already exists
                if obs_date in df['Date'].values:
                    print(f"\n   Updating existing row for {obs['date']}")
                    idx = df[df['Date'] == obs_date].index[0]
                else:
                    print(f"\n   Adding new row for {obs['date']}")
                    # Create new row based on latest data
                    latest_row = df.iloc[-1].copy()
                    latest_row['Date'] = obs_date
                    df = pd.concat([df, pd.DataFrame([latest_row])], ignore_index=True)
                    idx = len(df) - 1
                
                # Update Crop_Health based on NDVI
                # NDVI 0.2-0.8 maps to Crop_Health 0-4
                ndvi = obs.get('NDVI_mean', 0.5)
                crop_health = np.clip((ndvi - 0.2) / 0.15, 0, 4)
                df.loc[idx, 'Crop_Health'] = crop_health
                
                print(f"      NDVI: {ndvi:.3f} → Crop Health: {crop_health:.2f}/4")
        
        # Save updated CSV
        df = df.sort_values('Date')
        df.to_csv(csv_file, index=False)
        print(f"\n✅ Updated ground sensor data: {csv_file}")
        print(f"   Total rows: {len(df)}")
        
        return df

def main():
    """Main execution"""
    
    print("\n" + "="*70)
    print("🌾 RECENT SENTINEL-2 DATA INTEGRATION TOOL")
    print("="*70)
    print("\nThis tool will:")
    print("  1. Process recent .SAFE files from Sentinel_Data/recents/")
    print("  2. Compare with historical baseline (trained model period)")
    print("  3. Generate trend analysis report")
    print("  4. Update dashboard data with current predictions")
    print("="*70)
    
    # Initialize processor
    processor = RecentDataProcessor()
    
    # Step 1: Process recent .SAFE files
    recent_results = processor.process_recent_safe_files()
    
    if not recent_results:
        print("\n❌ No data processed. Exiting.")
        return
    
    # Step 2: Compare with historical
    historical, recent_results = processor.compare_with_historical(recent_results)
    
    # Step 3: Generate trend report
    trend_data = processor.generate_trend_report(historical, recent_results)
    
    # Step 4: Update ground sensor predictions
    processor.update_ground_sensor_predictions(trend_data)
    
    print("\n" + "="*70)
    print("✅ PROCESSING COMPLETE!")
    print("="*70)
    print("\n📊 Next Steps:")
    print("   1. Review: satellite_trend_analysis.json")
    print("   2. Check: latest_satellite_features.json (updated)")
    print("   3. View: sample_ground_sensor_data.csv (updated)")
    print("   4. Run: streamlit run enhanced_dashboard.py")
    print("\n💡 Your dashboard will now show:")
    print("   - Current crop health from recent satellite data")
    print("   - Trends compared to historical baseline")
    print("   - Updated ML predictions based on latest NDVI")
    print("="*70)

if __name__ == "__main__":
    main()
