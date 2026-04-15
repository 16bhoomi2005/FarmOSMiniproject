@echo off
echo ==============================================
echo 🌍 REAL WORLD DATA INTEGRATION CHECK
echo ==============================================
echo.
echo 1. Checking for Sentinel-2 Data...
if exist "Sentinel_Data\*.SAFE" (
    echo [OK] Sentinel Data Found
) else (
    echo [WARNING] No .SAFE files found in Sentinel_Data/
)

echo.
echo 2. Checking for Ground Sensor CSV...
if exist "sample_ground_sensor_data.csv" (
    echo [OK] Sensor CSV Found
) else (
    echo [FAIL] sample_ground_sensor_data.csv missing!
)

echo.
echo 3. Checking for Active Alerts...
if exist "active_alerts.json" (
    echo [OK] Active Alerts Found
) else (
    echo [INFO] No active alerts yet
)

echo.
echo ==============================================
echo If all checks passed, run:
echo streamlit run impactful_dashboard.py
echo.
pause
