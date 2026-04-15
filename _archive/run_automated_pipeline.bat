@echo off
echo ========================================
echo AUTOMATED CROP MONITORING PIPELINE
echo ========================================
echo.
echo Starting automated pipeline with:
echo - Daily data processing at 6:00 AM
echo - Weekly model retraining on Sunday 8:00 AM
echo - Real-time alert monitoring
echo - Automatic report generation
echo.
echo Pipeline will run continuously in background
echo Press Ctrl+C to stop
echo.
cd /d "c:\CropSatelliteSensorMain\project"
python automated_pipeline.py
pause
