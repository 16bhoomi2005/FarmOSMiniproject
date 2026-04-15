@echo off
echo ========================================
echo FIXED REAL DATA VALIDATION SYSTEM
echo ========================================
echo.
echo Validating real-world data processing with JSON fix:
echo - Sentinel-2 data extraction
echo - Ground sensor data collection  
echo - Data integration quality
echo - Model training results
echo.
echo Fixed JSON serialization issues
echo.
cd /d "c:\CropSatelliteSensorMain\project"
python fixed_validator.py
pause
