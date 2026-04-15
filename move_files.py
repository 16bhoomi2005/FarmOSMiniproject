import os
import shutil

# Config
current_dir = os.getcwd()
archive_dir = os.path.join(current_dir, "_archive")
pages_dir = os.path.join(current_dir, "pages")
pages_archive_dir = os.path.join(archive_dir, "pages")

# Create directories
os.makedirs(pages_archive_dir, exist_ok=True)

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

# 2. Page Files to Archive (The ones identified as inferior/mock-heavy)
pages_to_archive = [
    "1_🛰️_Satellite_Intelligence.py",  # Mock data, vs 1_Field_Health_Map.py (Real)
    "2_🌡️_Sensor_Insights.py",         # Mock data, vs 2_Sensor_Monitoring.py (Real)
    "3_🧠_Farming_AI.py",              # Reimpl logic, vs 3_Smart_Prediction_Engine.py (Central)
    "4_Actionable_Alerts.py",          # Reimpl logic, vs 4_🚨_Alerts_&_Recommendations.py (Central)
    "3_Future_Risk_Forecast.py",       # Likely older version
    "4_📊_Business_&_ROI.py",          # ROI stuff not in main scope?
    "5_📖_Knowledge_Base.py",          # Likely static text
    "6_🔮_Future_Projections.py"       # Likely mock
]

# Execution
print(f"📂 Archiving files to: {archive_dir}")

# Move Root Files
for f in root_files_to_archive:
    src = os.path.join(current_dir, f)
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
