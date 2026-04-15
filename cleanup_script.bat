@echo off
mkdir _archive 2>NUL
mkdir _archive\pages 2>NUL

echo Moving Root Files...
move impactful_dashboard.py _archive\ 2>NUL
move enhanced_dashboard.py _archive\ 2>NUL
move simple_implementation.py _archive\ 2>NUL
move enhanced_hybrid_system.py _archive\ 2>NUL
move cleanup_pages.py _archive\ 2>NUL
move cleanup_project.py _archive\ 2>NUL
move automated_pipeline.py _archive\ 2>NUL
move recommendation_engine.py _archive\ 2>NUL
move next_season_planner.py _archive\ 2>NUL
move roi_tracker.py _archive\ 2>NUL
move fix_csv_fields.py _archive\ 2>NUL
move fix_csv_robust.py _archive\ 2>NUL
move generate_data.py _archive\ 2>NUL
move process_recent_data.py _archive\ 2>NUL
move recover_polygon.py _archive\ 2>NUL
move report_generator.py _archive\ 2>NUL
move fixed_validator.py _archive\ 2>NUL
move run_automated_pipeline.bat _archive\ 2>NUL
move run_check.bat _archive\ 2>NUL
move run_enhanced_hybrid.bat _archive\ 2>NUL
move run_fixed_validator.bat _archive\ 2>NUL
move run_impactful_dashboard.bat _archive\ 2>NUL
move run_simple_implementation.bat _archive\ 2>NUL
move run_verify_real_data.bat _archive\ 2>NUL

echo Moving Page Files...
move "pages\1_🛰️_Satellite_Intelligence.py" _archive\pages\ 2>NUL
move "pages\2_🌡️_Sensor_Insights.py" _archive\pages\ 2>NUL
move "pages\3_🧠_Farming_AI.py" _archive\pages\ 2>NUL
move "pages\4_Actionable_Alerts.py" _archive\pages\ 2>NUL
move "pages\3_Future_Risk_Forecast.py" _archive\pages\ 2>NUL
move "pages\4_📊_Business_&_ROI.py" _archive\pages\ 2>NUL
move "pages\5_📖_Knowledge_Base.py" _archive\pages\ 2>NUL
move "pages\6_🔮_Future_Projections.py" _archive\pages\ 2>NUL

echo Cleanup Done.
