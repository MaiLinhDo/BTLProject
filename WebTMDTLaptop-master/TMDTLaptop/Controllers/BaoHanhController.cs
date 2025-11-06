using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Web.Mvc;
using Newtonsoft.Json;
using TMDTLaptop.Models.Class;

namespace TMDTLaptop.Controllers
{
    public class BaoHanhController : Controller
    {
        private readonly string apiBaseUrl = "http://127.0.0.1:5000/api";

        // GET: Danh sách phiếu bảo hành
        public async Task<ActionResult> QuanLyBaoHanh(string searchString, string trangThai, int page = 1, int pageSize = 10)
        {
            using (var client = new HttpClient())
            {
                var postData = new
                {
                    SearchString = searchString,
                    TrangThai = trangThai,
                    Page = page,
                    PageSize = pageSize
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync($"{apiBaseUrl}/get_phieu_bao_hanh", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    var phieuBaoHanh = data.phieuBaoHanh.ToObject<List<dynamic>>();
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)data.totalPages;
                    ViewBag.SearchString = searchString;
                    ViewBag.TrangThai = trangThai;
                    ViewBag.TotalCount = (int)data.totalCount;

                    // Danh sách trạng thái cho dropdown
                    ViewBag.TrangThaiList = new List<SelectListItem>
                    {
                        new SelectListItem { Value = "", Text = "Tất cả" },
                        new SelectListItem { Value = "Chờ xử lý", Text = "Chờ xử lý" },
                        new SelectListItem { Value = "Đã duyệt", Text = "Đã duyệt" },
                        new SelectListItem { Value = "Chờ lấy hàng bảo hành", Text = "Chờ lấy hàng" },
                        new SelectListItem { Value = "Đang bảo hành", Text = "Đang bảo hành" },
                        new SelectListItem { Value = "Hoàn tất", Text = "Hoàn tất" },
                        new SelectListItem { Value = "Từ chối", Text = "Từ chối" }
                    };

                    return View(phieuBaoHanh);
                }
                else
                {
                    TempData["ErrorMessage"] = "Không thể tải danh sách phiếu bảo hành";
                    return View(new List<dynamic>());
                }
            }
        }

        // GET: Chi tiết phiếu bảo hành
        public async Task<ActionResult> ChiTietBaoHanh(int id)
        {
            using (var client = new HttpClient())
            {
                var postData = new { MaPhieuBH = id };
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync($"{apiBaseUrl}/get_chi_tiet_bao_hanh", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    ViewBag.ChiTiet = data.chiTiet;
                    return View();
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }
        // GET: Chi tiết phiếu bảo hành
        public async Task<ActionResult> ChiTietBaoHanhUser(int id)
        {
            using (var client = new HttpClient())
            {
                var postData = new { MaPhieuBH = id };
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync($"{apiBaseUrl}/get_chi_tiet_bao_hanh", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    ViewBag.ChiTiet = data.chiTiet;
                    return View();
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }
        // GET: Trang tạo phiếu bảo hành (cho khách hàng)
        public async Task<ActionResult> TaoBaoHanh(int? maDonHang, int? maSanPham)
        {
            if (maDonHang.HasValue && maSanPham.HasValue)
            {
                // Kiểm tra điều kiện bảo hành
                using (var client = new HttpClient())
                {
                    var checkData = new
                    {
                        MaDonHang = maDonHang.Value,
                        MaSanPham = maSanPham.Value
                    };

                    var content = new StringContent(JsonConvert.SerializeObject(checkData), Encoding.UTF8, "application/json");
                    var response = await client.PostAsync($"{apiBaseUrl}/kiem_tra_dieu_kien_bao_hanh", content);
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);

                    if ((bool)data.success)
                    {
                        ViewBag.KiemTra = data;
                        ViewBag.MaDonHang = maDonHang.Value;
                        ViewBag.MaSanPham = maSanPham.Value;
                    }
                    else
                    {
                        ViewBag.ErrorMessage = data.message;
                    }
                }
            }

            return View();
        }

        // POST: Tạo phiếu bảo hành
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> TaoBaoHanh()
        {
            // Lấy dữ liệu từ form
            var maDonHang = Request.Form["MaDonHang"];
            var maSanPham = Request.Form["MaSanPham"];
            var soLuongBH = Request.Form["SoLuongBH"];
            var moTaLoi = Request.Form["MoTaLoi"];

            // Lấy files hình ảnh
            var hinhAnhFiles = Request.Files.GetMultiple("HinhAnhLoi");

            if (string.IsNullOrEmpty(maDonHang) || string.IsNullOrEmpty(maSanPham) || string.IsNullOrEmpty(moTaLoi))
            {
                TempData["ErrorMessage"] = "Vui lòng điền đầy đủ thông tin bắt buộc";
                return RedirectToAction("TaoBaoHanh", new { maDonHang = maDonHang, maSanPham = maSanPham });
            }

            try
            {
                // Tạo phiếu bảo hành trước để có MaPhieuBH (gọi API tạm thời)
                var tempData = new
                {
                    MaDonHang = maDonHang,
                    MaSanPham = maSanPham,
                    SoLuongBH = soLuongBH ?? "1",
                    MoTaLoi = moTaLoi,
                    HinhAnhLoi = new List<string>() // Gửi rỗng trước
                };

                string maPhieuBH = "";
                using (var client = new HttpClient())
                {
                    var jsonContent = JsonConvert.SerializeObject(tempData);
                    var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");
                    var response = await client.PostAsync($"{apiBaseUrl}/tao_phieu_bao_hanh", content);
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);

                    if (!(bool)data.success)
                    {
                        TempData["ErrorMessage"] = data.message;
                        return RedirectToAction("TaoBaoHanh", new { maDonHang = maDonHang, maSanPham = maSanPham });
                    }

                    maPhieuBH = data.maPhieuBH.ToString();
                }

                // Lưu files hình ảnh nếu có (GIỐNG LOGIC SẢN PHẨM)
                List<string> savedFileNames = new List<string>();
                if (hinhAnhFiles != null && hinhAnhFiles.Any(f => f != null && f.ContentLength > 0))
                {
                    // Tạo thư mục lưu trữ
                    string warrantyFolder = Server.MapPath($"~/assets/images/warranty/{maPhieuBH}/");
                    if (!Directory.Exists(warrantyFolder))
                    {
                        Directory.CreateDirectory(warrantyFolder);
                    }

                    foreach (var file in hinhAnhFiles)
                    {
                        if (file != null && file.ContentLength > 0)
                        {
                            // Validate file
                            string[] allowedExtensions = { ".jpg", ".jpeg", ".png", ".gif", ".webp" };
                            string fileExtension = Path.GetExtension(file.FileName).ToLower();

                            if (!allowedExtensions.Contains(fileExtension))
                            {
                                continue; // Skip invalid files
                            }

                            if (file.ContentLength > 5 * 1024 * 1024) // 5MB
                            {
                                continue; // Skip files too large
                            }

                            // Tạo tên file unique
                            string uniqueFileName = $"{Guid.NewGuid().ToString("N")}{fileExtension}";
                            string filePath = Path.Combine(warrantyFolder, uniqueFileName);

                            // Lưu file
                            file.SaveAs(filePath);
                            savedFileNames.Add(uniqueFileName);
                        }
                    }
                }

                // Cập nhật đường dẫn hình ảnh vào database (gọi API update)
                if (savedFileNames.Count > 0)
                {
                    using (var client = new HttpClient())
                    {
                        var updateData = new
                        {
                            MaPhieuBH = maPhieuBH,
                            HinhAnhLoi = savedFileNames
                        };

                        var jsonContent = JsonConvert.SerializeObject(updateData);
                        var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");
                        var response = await client.PostAsync($"{apiBaseUrl}/cap_nhat_hinh_anh_bao_hanh", content);

                        // Không cần check response vì đã tạo phiếu thành công rồi
                    }
                }

                TempData["SuccessMessage"] = $"Tạo phiếu bảo hành thành công! Mã phiếu: {maPhieuBH}";
                if (savedFileNames.Count > 0)
                {
                    TempData["SuccessMessage"] += $" Đã tải lên {savedFileNames.Count} hình ảnh.";
                }

                return RedirectToAction("DanhSachBaoHanhKhachHang");
            }
            catch (Exception ex)
            {
                TempData["ErrorMessage"] = "Lỗi khi tạo phiếu bảo hành: " + ex.Message;
                return RedirectToAction("TaoBaoHanh", new { maDonHang = maDonHang, maSanPham = maSanPham });
            }
        }

        // GET: Danh sách bảo hành của khách hàng
        public async Task<ActionResult> DanhSachBaoHanhKhachHang(int page = 1, int pageSize = 10)
        {
            // Kiểm tra đăng nhập
            var username = Session["Username"] as string;
            if (string.IsNullOrEmpty(username))
            {
                return RedirectToAction("DangNhap", "Home");
            }

            try
            {
                using (var client = new HttpClient())
                {
                    // Lấy thông tin user từ API check_username
                    string apiUrl = $"http://127.0.0.1:5000/api/check_username?username={username}";
                    var response = await client.GetAsync(apiUrl);

                    if (response.IsSuccessStatusCode)
                    {
                        string responseBody = await response.Content.ReadAsStringAsync();
                        dynamic user = JsonConvert.DeserializeObject(responseBody);

                        if (user == null)
                        {
                            return RedirectToAction("DangNhap", "Home");
                        }

                        if (user.TrangThai == false)
                        {
                            return RedirectToAction("DangNhap", "Home", new { mess = "Tài khoản của bạn đã bị khóa" });
                        }

                        // Lưu thông tin vào ViewBag để sử dụng trong JavaScript
                        ViewBag.MaTaiKhoan = (int)user.MaTaiKhoan;
                        ViewBag.HoTen = (string)user.HoTen;
                        ViewBag.CurrentPage = page;
                        ViewBag.PageSize = pageSize;

                        // Thêm thông tin user vào Session nếu chưa có
                        if (Session["MaTaiKhoan"] == null)
                        {
                            Session["MaTaiKhoan"] = (int)user.MaTaiKhoan;
                            Session["HoTen"] = (string)user.HoTen;
                        }

                        return View();
                    }
                    else
                    {
                        return RedirectToAction("DangNhap", "Home");
                    }
                }
            }
            catch (Exception ex)
            {
                ViewBag.ErrorMessage = "Lỗi kết nối: " + ex.Message;
                return View();
            }
        }
        // POST: Cập nhật trạng thái
        [HttpPost]
        public async Task<JsonResult> CapNhatTrangThai(int maPhieuBH, string trangThai, string lyDoTuChoi, string ghiChu)
        {
            var postData = new
            {
                MaPhieuBH = maPhieuBH,
                TrangThai = trangThai,
                LyDoTuChoi = lyDoTuChoi,
                GhiChu = ghiChu,
                NhanVienXuLy = Session["MaTaiKhoan"] // Giả sử lưu trong session
            };

            using (var client = new HttpClient())
            {
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync($"{apiBaseUrl}/cap_nhat_trang_thai_bao_hanh", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                return Json(new { success = data.success, message = data.message });
            }
        }

        

        

        // GET: Thống kê bảo hành
        public async Task<ActionResult> ThongKeBaoHanh(DateTime? startDate, DateTime? endDate)
        {
            if (!startDate.HasValue) startDate = DateTime.Now.AddMonths(-3);
            if (!endDate.HasValue) endDate = DateTime.Now;

            using (var client = new HttpClient())
            {
                var postData = new
                {
                    startDate = startDate.Value.ToString("yyyy-MM-dd"),
                    endDate = endDate.Value.ToString("yyyy-MM-dd")
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync($"{apiBaseUrl}/thong_ke_bao_hanh", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    ViewBag.ThongKe = data;
                    ViewBag.StartDate = startDate.Value;
                    ViewBag.EndDate = endDate.Value;

                    return View();
                }
                else
                {
                    ViewBag.ErrorMessage = data.message;
                    return View();
                }
            }
        }

        

        // GET: Export báo cáo bảo hành
        public async Task<ActionResult> ExportBaoCao(DateTime? startDate, DateTime? endDate, string format = "excel")
        {
            if (!startDate.HasValue) startDate = DateTime.Now.AddMonths(-1);
            if (!endDate.HasValue) endDate = DateTime.Now;

            using (var client = new HttpClient())
            {
                var postData = new
                {
                    startDate = startDate.Value.ToString("yyyy-MM-dd"),
                    endDate = endDate.Value.ToString("yyyy-MM-dd")
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync($"{apiBaseUrl}/get_phieu_bao_hanh", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    var phieuBaoHanh = data.phieuBaoHanh.ToObject<List<dynamic>>();

                    // Tạo file Excel hoặc PDF dựa trên format
                    //if (format.ToLower() == "pdf")
                    //{
                    //    return ExportToPdf(phieuBaoHanh, startDate.Value, endDate.Value);
                    //}
                    //else
                    //{
                        return ExportToExcel(phieuBaoHanh, startDate.Value, endDate.Value);
                   // }
                }
                else
                {
                    TempData["ErrorMessage"] = "Không thể xuất báo cáo";
                    return RedirectToAction("ThongKeBaoHanh");
                }
            }
        }

        // Helper methods cho export
        private ActionResult ExportToExcel(List<dynamic> data, DateTime startDate, DateTime endDate)
        {
            // Implementation cho export Excel
            // Sử dụng thư viện như EPPlus hoặc ClosedXML
            // Code implementation...

            TempData["InfoMessage"] = "Chức năng xuất Excel đang được phát triển";
            return RedirectToAction("ThongKeBaoHanh");
        }

        
    }
}