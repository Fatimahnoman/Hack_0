@echo off
REM Test Gold Tier LinkedIn Auto-Post Implementation
REM =================================================
REM Run comprehensive test suite for LinkedIn automation

echo.
echo ======================================================================
echo                  GOLD TIER LINKEDIN AUTO-POST TEST
echo ======================================================================
echo.

cd /d "%~dp0"

echo Running Python test suite...
echo.

python test_gold_tier_linkedin.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo                         TESTS PASSED!
    echo ======================================================================
    echo.
    echo Gold Tier LinkedIn Auto-Post is ready to use!
    echo.
    echo Next steps:
    echo 1. Review test report in gold\logs\
    echo 2. Read GOLD_TIER_LINKEDIN_AUTO_POST_COMPLETE.md
    echo 3. Start the system: start_gold_tier.bat
    echo.
) else (
    echo.
    echo ======================================================================
    echo                       SOME TESTS FAILED
    echo ======================================================================
    echo.
    echo Review the errors above. Common fixes:
    echo - Install dependencies: pip install playwright
    echo - Install browser: playwright install chromium
    echo - Check folder structure exists
    echo.
)

pause
