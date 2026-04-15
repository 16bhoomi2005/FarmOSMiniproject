import os
import shutil

# Hardcoded paths specifically for this environment
base_dir = r"c:\CropSatelliteSensorMain\project"
archive_dir = os.path.join(base_dir, "_archive")
pages_dir = os.path.join(base_dir, "pages")
pages_archive_dir = os.path.join(archive_dir, "pages")

print(f"Base Dir: {base_dir}")
print(f"Archive Dir: {archive_dir}")

# Create directories
try:
    os.makedirs(pages_archive_dir, exist_ok=True)
    print("✅ Created archive directories.")
except Exception as e:
    print(f"❌ Failed to create directories: {e}")

# 1. Root Files to Archive
root_files_to_archive = [
    "impactful_dashboard.py",
    "enhanced_dashboard.py",
    "simple_implementation.py",
    "enhanced_hybrid_system.py",
    "cleanup_pages.py",
    "cleanup_project.py",
    "automated_pipeline.py",
    "recommendation_engine.py",
    "next_season_planner.py",
    "roi_tracker.py",
    "fix_csv_fields.py",
    "fix_csv_robust.py",
    "generate_data.py",
    "process_recent_data.py",
    "recover_polygon.py",
    "report_generator.py",
    "fixed_validator.py",
    "run_automated_pipeline.bat",
    "run_check.bat",
    "run_enhanced_hybrid.bat",
    "run_fixed_validator.bat",
    "run_impactful_dashboard.bat",
    "run_simple_implementation.bat",
    "run_verify_real_data.bat"
]

# 2. Page Files to Archive
pages_to_archive = [
    "1_🛰️_Satellite_Intelligence.py",  
    "2_🌡️_Sensor_Insights.py",         
    "3_🧠_Farming_AI.py",              
    "4_Actionable_Alerts.py",          
    "3_Future_Risk_Forecast.py",       
    "4_📊_Business_&_ROI.py",          
    "5_📖_Knowledge_Base.py",          
    "6_🔮_Future_Projections.py"       
]

# Move Root Files
for f in root_files_to_archive:
    src = os.path.join(base_dir, f)
    dst = os.path.join(archive_dir, f)
    if os.path.exists(src):
        try:
            shutil.move(src, dst)
            print(f"✅ Archived: {f}")
        except Exception as e:
            print(f"❌ Failed to archive {f}: {e}")
    else:
        print(f"⚠️ Not found: {f}")

# Move Page Files
for f in pages_to_archive:
    src = os.path.join(pages_dir, f)
    dst = os.path.join(pages_archive_dir, f)
    if os.path.exists(src):
        try:
            shutil.move(src, dst)
            print(f"✅ Archived Page: {f}")
        except Exception as e:
            print(f"❌ Failed to archive page {f}: {e}")
    else:
        print(f"⚠️ Page not found: {f}")

print("\n🎉 Cleanup Complete.")
