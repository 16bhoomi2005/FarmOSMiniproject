@echo off
echo ==============================================
echo 🌾 SMART FARM SEASON 2 - VERIFICATION RUN
echo ==============================================
echo.
echo 1. Generating Data & Training AI Models...
python enhanced_hybrid_system.py
echo.
echo 2. Testing Alert System (New Sensors)...
python alert_config.py
echo.
echo ==============================================
echo ✅ VERIFICATION COMPLETE
echo.
echo Check the output above for:
echo  - "Enhanced Ground Sensor Features" (should list pH, Soil Temp)
echo  - "SOIL_HEALTH ALERT" (should see pH and Temp alerts)
echo.
pause
