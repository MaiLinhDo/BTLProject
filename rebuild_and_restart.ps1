Write-Host "🔄 Đang rebuild và restart ứng dụng..." -ForegroundColor Cyan

# Tìm và dừng IIS Express
Write-Host "`n📌 Dừng IIS Express..." -ForegroundColor Yellow
$iisProcesses = Get-Process | Where-Object {$_.ProcessName -like "*iisexpress*"}
if ($iisProcesses) {
    $iisProcesses | ForEach-Object {
        Write-Host "   Đang dừng process: $($_.ProcessName) (ID: $($_.Id))" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Tìm Visual Studio solution
$solutionPath = "E:\BTLProject\WebTMDTLaptop-master\TMDTLaptop.sln"
if (Test-Path $solutionPath) {
    Write-Host "`n🔨 Đang rebuild solution..." -ForegroundColor Yellow
    
    # Sử dụng MSBuild để rebuild
    $msbuildPath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    if (-not (Test-Path $msbuildPath)) {
        $msbuildPath = "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    }
    if (-not (Test-Path $msbuildPath)) {
        $msbuildPath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    }
    
    if (Test-Path $msbuildPath) {
        Write-Host "   Sử dụng MSBuild: $msbuildPath" -ForegroundColor Gray
        & $msbuildPath $solutionPath /t:Rebuild /p:Configuration=Debug /verbosity:minimal
        Write-Host "   ✅ Rebuild hoàn tất!" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Không tìm thấy MSBuild. Vui lòng rebuild trong Visual Studio." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n⚠️  Không tìm thấy solution file." -ForegroundColor Yellow
}

# Xóa cache IIS Express
Write-Host "`n🧹 Đang xóa cache IIS Express..." -ForegroundColor Yellow
$iisExpressConfigPath = "$env:USERPROFILE\Documents\IISExpress\config"
if (Test-Path $iisExpressConfigPath) {
    Write-Host "   Cache path: $iisExpressConfigPath" -ForegroundColor Gray
}

# Xóa bin và obj folders để force rebuild
Write-Host "`n🗑️  Đang xóa bin và obj folders..." -ForegroundColor Yellow
$projectPath = "E:\BTLProject\WebTMDTLaptop-master\TMDTLaptop"
$binPath = Join-Path $projectPath "bin"
$objPath = Join-Path $projectPath "obj"

if (Test-Path $binPath) {
    Remove-Item -Path $binPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Đã xóa bin folder" -ForegroundColor Green
}
if (Test-Path $objPath) {
    Remove-Item -Path $objPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Đã xóa obj folder" -ForegroundColor Green
}

Write-Host "`n✨ Hoàn tất! Vui lòng:" -ForegroundColor Cyan
Write-Host "   1. Mở Visual Studio" -ForegroundColor White
Write-Host "   2. Mở solution TMDTLaptop.sln" -ForegroundColor White
Write-Host "   3. Nhấn Ctrl+Shift+B để rebuild" -ForegroundColor White
Write-Host "   4. Nhấn F5 để chạy lại project" -ForegroundColor White

