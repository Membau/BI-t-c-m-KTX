@echo off
chcp 65001 > nul
setlocal
title RUN BIG DATA KAFKA PROJECT (PY -3.10)

REM ===== 1. SỬA ĐƯỜNG DẪN KAFKA TẠI ĐÂY =====
set "KAFKA_HOME=C:\kafka_2.13-4.2.0"

REM ===== 2. THƯ MỤC PROJECT =====
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo ==========================================
echo BIG DATA + KAFKA 4.2 + AI + STREAMLIT + OLLAMA
echo ==========================================
echo Project Dir : %PROJECT_DIR%
echo Kafka Home  : %KAFKA_HOME%
echo Python      : py -3.10
echo.

REM Kiem tra Kafka co ton tai khong
if not exist "%KAFKA_HOME%\bin\windows\kafka-server-start.bat" (
    echo [ERROR] Khong tim thay kafka-server-start.bat tai %KAFKA_HOME%
    pause
    exit /b 1
)

REM Tao thu muc neu chua co
if not exist "%PROJECT_DIR%data" mkdir "%PROJECT_DIR%data"
if not exist "%PROJECT_DIR%output" mkdir "%PROJECT_DIR%output"

REM ====================================================
REM THÊM MỚI: TỰ ĐỘNG BẬT OLLAMA VÀ LOAD MODEL
REM ====================================================
REM ====================================================
REM KIỂM TRA OLLAMA CÓ TRÊN MÁY HAY CHƯA
REM ====================================================
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [CANH BAO NGHIEM TRONG] May tinh nay chua cai dat Ollama!
    echo He thong AI parsing khong the hoat dong thieu Ollama.
    echo.
    echo Dang tu dong mo trang tai Ollama cho ban...
    start https://ollama.com/download
    echo.
    echo ====================================================
    echo VUI LONG CAI DAT OLLAMA, SAU DO CHAY LAI FILE NAY!
    echo ====================================================
    pause
    exit /b 1
)
echo [0/6] Khoi dong Ollama Server ngam...
start "OLLAMA SERVER" cmd /c "ollama serve"
echo Cho Ollama khoi dong (5 giay)...
timeout /t 5 /nobreak > nul

echo Nap model Gemma3 vao RAM (an qua trinh nay)...
start /b cmd /c "ollama run gemma3 < nul"
REM ====================================================

echo [1/6] Tao du lieu mau...
py -3.10 generate_sample_data.py
if errorlevel 1 (
    echo [ERROR] Loi khi tao du lieu mau.
    pause
    exit /b 1
)

if exist "%PROJECT_DIR%output\stream_output.csv" del /f /q "%PROJECT_DIR%output\stream_output.csv"

echo [2/6] Mo Kafka Server...
start "KAFKA SERVER" cmd /k "cd /d "%KAFKA_HOME%" && bin\windows\kafka-server-start.bat config\server.properties"

echo Cho Kafka khoi dong (12 giay)...
timeout /t 12 /nobreak > nul

echo [3/6] Tao topic facebook_orders_stream neu chua co...
call "%KAFKA_HOME%\bin\windows\kafka-topics.bat" --list --bootstrap-server localhost:9092 | findstr /x "facebook_orders_stream" > nul
if errorlevel 1 (
    call "%KAFKA_HOME%\bin\windows\kafka-topics.bat" --create --topic facebook_orders_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
) else (
    echo Topic facebook_orders_stream da ton tai.
)

echo [4/6] Mo Consumer (AI Parsing)...
start "CONSUMER" cmd /k "cd /d "%PROJECT_DIR%" && py -3.10 consumer_fb.py"
timeout /t 3 /nobreak > nul

echo [5/6] Mo Producer (Streaming Data)...
start "PRODUCER" cmd /k "cd /d "%PROJECT_DIR%" && py -3.10 producer_fb.py"
timeout /t 3 /nobreak > nul

echo [6/6] Mo Streamlit Dashboard...
start "STREAMLIT" cmd /k "cd /d "%PROJECT_DIR%" && py -3.10 -m streamlit run app.py"

echo.
echo ==========================================
echo HE THONG DA KHOI DONG VOI PY -3.10
echo ==========================================
echo.
pause
endlocal