@echo off
chcp 65001 >nul
echo ========================================
echo   KHOI DONG API VA WEB APPLICATION
echo ========================================
echo.

REM Kiểm tra và dừng các process cũ
echo [*] Kiem tra cac process dang chay...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM iisexpress.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

REM Thiết lập đường dẫn
set "PROJECT_DIR=%~dp0"
set "FLASK_DIR=%PROJECT_DIR%LaptopStore"
set "WEB_DIR=%PROJECT_DIR%WebTMDTLaptop-master\TMDTLaptop"
set "SOLUTION_PATH=%PROJECT_DIR%WebTMDTLaptop-master\TMDTLaptop.sln"
set "PORT=59774"

REM Kiểm tra xem project đã build chưa
set "DLL_PATH=%WEB_DIR%\bin\TMDTLaptop.dll"
if not exist "%DLL_PATH%" (
    echo [*] Project chua duoc build. Dang build...
    
    REM Tìm MSBuild
    set "MSBUILD_PATH="
    if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
        set "MSBUILD_PATH=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    ) else if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
        set "MSBUILD_PATH=%ProgramFiles%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    ) else if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" (
        set "MSBUILD_PATH=%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    )
    
    if defined MSBUILD_PATH (
        echo     Dang build voi MSBuild...
        "%MSBUILD_PATH%" "%SOLUTION_PATH%" /t:Build /p:Configuration=Debug /verbosity:minimal /nologo
        if %ERRORLEVEL% EQU 0 (
            echo     [OK] Build thanh cong!
        ) else (
            echo     [ERROR] Build that bai. Vui long build trong Visual Studio.
        )
    ) else (
        echo     [WARNING] Khong tim thay MSBuild. Vui long build trong Visual Studio.
        echo.
        echo     Huong dan:
        echo     1. Mo Visual Studio
        echo     2. Mo file: %SOLUTION_PATH%
        echo     3. Nhan Ctrl+Shift+B de build
        echo     4. Nhan F5 de chay
        echo.
    )
)

REM Tìm IIS Express
set "IISEXPRESS_PATH="
if exist "%ProgramFiles%\IIS Express\iisexpress.exe" (
    set "IISEXPRESS_PATH=%ProgramFiles%\IIS Express\iisexpress.exe"
) else if exist "%ProgramFiles(x86)%\IIS Express\iisexpress.exe" (
    set "IISEXPRESS_PATH=%ProgramFiles(x86)%\IIS Express\iisexpress.exe"
)

REM Khởi động Flask API
echo.
echo [*] Dang khoi dong Flask backend (port 5000)...
cd /d "%FLASK_DIR%"
start "Flask API - Port 5000" cmd /k "python run.py"
timeout /t 3 /nobreak >nul

REM Khởi động ASP.NET Web
echo [*] Dang khoi dong ASP.NET MVC frontend...
if defined IISEXPRESS_PATH (
    cd /d "%WEB_DIR%"
    start "IIS Express - Port %PORT%" cmd /k ""%IISEXPRESS_PATH%" /path:"%WEB_DIR%" /port:%PORT%"
    timeout /t 2 /nobreak >nul
    echo     [OK] IIS Express da khoi dong!
) else (
    echo     [WARNING] Khong tim thay IIS Express.
    echo     Vui long chay project trong Visual Studio (F5)
)

REM Hiển thị thông tin
echo.
echo ========================================
echo   HOAN TAT!
echo ========================================
echo.
echo Trang thai:
echo   Flask Backend:    http://127.0.0.1:5000
if defined IISEXPRESS_PATH (
    echo   ASP.NET Frontend: http://localhost:%PORT%
)
echo.
echo De dung cac services, dong cac cua so cmd hoac nhan Ctrl+C
echo.
echo Dang cho... (Nhan Ctrl+C de thoat)
pause

