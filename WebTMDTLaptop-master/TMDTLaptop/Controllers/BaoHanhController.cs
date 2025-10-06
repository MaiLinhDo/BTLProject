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
                    if (format.ToLower() == "pdf")
                    {
                        return ExportToPdf(phieuBaoHanh, startDate.Value, endDate.Value);
                    }
                    else
                    {
                        return ExportToExcel(phieuBaoHanh, startDate.Value, endDate.Value);
                    }
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