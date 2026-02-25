@echo off
echo Starting Enhanced Codebase Indexer...

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python
)

REM Run the enhanced indexer service
cd ..
python -c "from src.sync.main_enhanced import main; main()"

REM Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo Error occurred. Press any key to exit.
    pause > nul
)
