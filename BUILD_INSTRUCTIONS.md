# Hướng dẫn Build Project

## Vấn đề hiện tại
Project chưa được build, nên không có thư mục `bin` và các file DLL cần thiết. Điều này gây ra lỗi:
- "Could not load type 'TMDTLaptop.MvcApplication'"
- "The resource cannot be found" (404 errors)

## Giải pháp

### Cách 1: Build trong Visual Studio (Khuyến nghị)

1. **Mở Visual Studio**
   - Mở Visual Studio 2019 hoặc 2022

2. **Mở Solution**
   - File → Open → Project/Solution
   - Chọn file: `E:\BTLProject\WebTMDTLaptop-master\TMDTLaptop.sln`

3. **Restore NuGet Packages** (nếu cần)
   - Right-click vào Solution → Restore NuGet Packages
   - Hoặc: Tools → NuGet Package Manager → Package Manager Console
   - Chạy lệnh: `Update-Package -reinstall`

4. **Build Solution**
   - Menu: Build → Build Solution (Ctrl+Shift+B)
   - Hoặc: Build → Rebuild Solution
   - Đợi cho đến khi build thành công (không có lỗi)

5. **Chạy Project**
   - Nhấn F5 hoặc Start Debugging
   - Hoặc: Debug → Start Debugging

### Cách 2: Build bằng Command Line (Nếu có MSBuild)

Mở PowerShell và chạy:

```powershell
# Tìm MSBuild
$msbuild = Get-ChildItem "C:\Program Files*" -Recurse -Filter "MSBuild.exe" -ErrorAction SilentlyContinue | Select-Object -First 1

# Build solution
& $msbuild.FullName "E:\BTLProject\WebTMDTLaptop-master\TMDTLaptop.sln" /t:Build /p:Configuration=Debug
```

## Sau khi build thành công

- Thư mục `bin` sẽ được tạo tại: `E:\BTLProject\WebTMDTLaptop-master\TMDTLaptop\bin`
- File `TMDTLaptop.dll` sẽ có trong thư mục `bin`
- Ứng dụng sẽ chạy bình thường

## Kiểm tra build thành công

Sau khi build, kiểm tra:
```powershell
Test-Path "E:\BTLProject\WebTMDTLaptop-master\TMDTLaptop\bin\TMDTLaptop.dll"
```

Nếu trả về `True`, nghĩa là build thành công!

## Lưu ý

- Nếu gặp lỗi về NuGet packages, cần restore packages trước
- Nếu gặp lỗi về missing references, kiểm tra lại các packages trong `packages.config`
- Đảm bảo Visual Studio đã cài đặt đầy đủ các components cho ASP.NET MVC

