@echo off
echo Starting Personal Assistant Bot...

REM Activate virtual environment
call env\Scripts\activate.bat

REM Install/update requirements
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Run the bot
echo Starting bot...
python main.py

pause