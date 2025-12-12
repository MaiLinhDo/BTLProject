Write-Host "🚀 Đang khởi động web application..." -ForegroundColor Cyan

# Kiểm tra và dừng các process cũ
Write-Host "`n📌 Kiểm tra các process đang chạy..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
$iisProcesses = Get-Process | Where-Object {$_.ProcessName -like "*iisexpress*"}

if ($pythonProcesses) {
    Write-Host "   Đang dừng Python processes cũ..." -ForegroundColor Gray
    $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

if ($iisProcesses) {
    Write-Host "   Đang dừng IIS Express processes cũ..." -ForegroundColor Gray
    $iisProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Chạy Flask backend
Write-Host "`n🐍 Đang khởi động Flask backend (port 5000)..." -ForegroundColor Green
$flaskJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "LaptopStore"
    python run.py
}

Start-Sleep -Seconds 3

# Kiểm tra Flask đã chạy chưa
Write-Host "   Đang kiểm tra Flask backend..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000" -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "   ✅ Flask backend đã chạy thành công!" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Flask backend đang khởi động..." -ForegroundColor Yellow
}

# Chạy ASP.NET MVC frontend
Write-Host "`n🌐 Đang khởi động ASP.NET MVC frontend..." -ForegroundColor Green

$solutionPath = "WebTMDTLaptop-master\TMDTLaptop.sln"
$projectPath = "WebTMDTLaptop-master\TMDTLaptop"

# Kiểm tra xem đã build chưa
$dllPath = "$projectPath\bin\TMDTLaptop.dll"
if (-not (Test-Path $dllPath)) {
    Write-Host "   ⚠️  Project chưa được build. Đang build..." -ForegroundColor Yellow
    
    # Tìm MSBuild
    $msbuildPaths = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    )
    
    $msbuild = $null
    foreach ($path in $msbuildPaths) {
        if (Test-Path $path) {
            $msbuild = $path
            break
        }
    }
    
    if ($msbuild) {
        Write-Host "   Đang build với MSBuild..." -ForegroundColor Gray
        & $msbuild $solutionPath /t:Build /p:Configuration=Debug /verbosity:minimal /nologo
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Build thành công!" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Build thất bại. Vui lòng build trong Visual Studio." -ForegroundColor Red
        }
    } else {
        Write-Host "   ❌ Không tìm thấy MSBuild. Vui lòng build trong Visual Studio." -ForegroundColor Red
        Write-Host "`n📝 Hướng dẫn:" -ForegroundColor Cyan
        Write-Host "   1. Mở Visual Studio" -ForegroundColor White
        Write-Host "   2. Mở file: $solutionPath" -ForegroundColor White
        Write-Host "   3. Nhấn Ctrl+Shift+B để build" -ForegroundColor White
        Write-Host "   4. Nhấn F5 để chạy" -ForegroundColor White
    }
}

# Tìm IIS Express
$iisExpressPath = "${env:ProgramFiles}\IIS Express\iisexpress.exe"
if (-not (Test-Path $iisExpressPath)) {
    $iisExpressPath = "${env:ProgramFiles(x86)}\IIS Express\iisexpress.exe"
}

if (Test-Path $iisExpressPath) {
    Write-Host "   Đang khởi động IIS Express..." -ForegroundColor Gray
    
    # Đọc port từ Web.config hoặc dùng port mặc định
    $port = 59774  # Port mặc định từ Web.config
    
    $webConfigPath = "$projectPath\Web.config"
    if (Test-Path $webConfigPath) {
        $webConfig = [xml](Get-Content $webConfigPath)
        $returnUrl = $webConfig.configuration.appSettings.add | Where-Object { $_.key -eq "vnp_Returnurl" }
        if ($returnUrl) {
            if ($returnUrl.value -match 'localhost:(\d+)') {
                $port = $matches[1]
            }
        }
    }
    
    $iisJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        Set-Location $using:projectPath
        & $using:iisExpressPath /path:"$using:PWD\$using:projectPath" /port:$using:port
    }
    
    Start-Sleep -Seconds 2
    Write-Host "   ✅ IIS Express đã khởi động!" -ForegroundColor Green
    Write-Host "`n🌐 Frontend đang chạy tại: http://localhost:$port" -ForegroundColor Cyan
} else {
    Write-Host "   ⚠️  Không tìm thấy IIS Express." -ForegroundColor Yellow
    Write-Host "   Vui lòng chạy project trong Visual Studio (F5)" -ForegroundColor White
}

Write-Host "`n✨ Hoàn tất!" -ForegroundColor Green
Write-Host "`n📋 Trạng thái:" -ForegroundColor Cyan
Write-Host "   🐍 Flask Backend: http://127.0.0.1:5000" -ForegroundColor White
if ($iisExpressPath -and (Test-Path $iisExpressPath)) {
    Write-Host "   🌐 ASP.NET Frontend: http://localhost:$port" -ForegroundColor White
}
Write-Host "`n💡 Để dừng các services, nhấn Ctrl+C hoặc đóng cửa sổ này." -ForegroundColor Yellow

# Giữ script chạy
try {
    while ($true) {
        Start-Sleep -Seconds 10
        # Kiểm tra jobs còn chạy không
        $flaskJobState = Get-Job -Id $flaskJob.Id -ErrorAction SilentlyContinue
        if ($flaskJobState -and $flaskJobState.State -eq "Failed") {
            Write-Host "`n❌ Flask backend đã dừng!" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "`nStop requested. Stopping services..." -ForegroundColor Yellow
    Stop-Job $flaskJob -ErrorAction SilentlyContinue
    Remove-Job $flaskJob -ErrorAction SilentlyContinue
    if ($iisJob) {
        Stop-Job $iisJob -ErrorAction SilentlyContinue
        Remove-Job $iisJob -ErrorAction SilentlyContinue
    }
}
