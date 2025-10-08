@echo off
echo ========================================
echo VRehab - Mind-Controlled Robot Setup
echo ========================================
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Checking for pydobot installation...
python -c "import pydobot; print('✅ pydobot installed successfully')" 2>nul || (
    echo ❌ pydobot not found, installing...
    pip install pydobot
)

echo.
echo Checking for pylsl installation...
python -c "import pylsl; print('✅ pylsl installed successfully')" 2>nul || (
    echo ❌ pylsl not found, installing...
    pip install pylsl
)

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo To run VRehab:
echo   python vrehab_gui_refactored.py
echo.
echo Make sure to:
echo   1. Connect your Dobot Magic robot
echo   2. Start your EEG device with LSL stream
echo   3. Select the correct COM port
echo.
pause
