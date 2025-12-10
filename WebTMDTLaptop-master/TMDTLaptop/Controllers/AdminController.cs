using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Data;
using System.Data.Entity;
using System.Data.Entity.Infrastructure;
using System.Drawing.Printing;
using System.IO;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using System.Web.UI;
using TMDTLaptop.Models;
using TMDTLaptop.Models.Class;
using OfficeOpenXml;
using Newtonsoft.Json;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Globalization;
using System.Collections.Specialized;
namespace TMDTLaptop.Controllers
{
    public class AdminController : Controller
    {
     
        public bool check()
        {
            if (Session["Admin"] == null) { return false; }
            return true;
        }

      
        // GET: Quản lý banner
        public async Task<ActionResult> QuanLyBanner()
        {
            //        if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var response = await client.GetAsync("http://127.0.0.1:5000/api/get_all_banners");

                if (!response.IsSuccessStatusCode)
                {
                    ViewBag.Message = "Có lỗi khi kết nối đến API.";
                    return View();
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data.success == true && data.banners != null)
                {
                    var banners = data.banners.ToObject<List<Banner>>();
                    return View(banners);
                }
                else
                {
                    ViewBag.Message = data.message ?? "Không thể lấy dữ liệu từ API.";
                    return View();
                }
            }
        }
        public ActionResult ThemBanner()
        {
            //   if (!check()) { return RedirectToAction("Loi404", "Admin"); }
            return View();
        }

        [HttpPost]
        public async Task<ActionResult> ThemBanner(Banner model, HttpPostedFileBase HinhAnh)
        {
            if (ModelState.IsValid)
            {
                if (HinhAnh != null && HinhAnh.ContentLength > 0)
                {
                    var fileName = Path.GetFileName(HinhAnh.FileName);
                    var path = Path.Combine(Server.MapPath("~/assets/images/banner/"), fileName);
                    HinhAnh.SaveAs(path);
                    model.HinhAnh = fileName;
                }

                model.LienKet = "";

                using (var client = new HttpClient())
                {
                    client.BaseAddress = new Uri("http://127.0.0.1:5000");
                    var data = new
                    {
                        MoTa = model.MoTa,
                        HinhAnh = model.HinhAnh,
                        LienKet = model.LienKet
                    };

                    var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                    var response = await client.PostAsync("/api/banners", content);
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic responseData = JsonConvert.DeserializeObject(result);

                    if (responseData.success == true)
                    {
                        return RedirectToAction("QuanLyBanner");
                    }

                    ModelState.AddModelError("", responseData.message.ToString());
                }
            }

            return View(model);
        }

        public async Task<ActionResult> XoaBanner(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.DeleteAsync($"http://127.0.0.1:5000/api/banners/{id}");
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data.success == true)
                {
                    return RedirectToAction("QuanLyBanner");
                }

                ViewBag.Message = data.message ?? "Xóa thất bại.";
                return RedirectToAction("QuanLyBanner");
            }
        }
        public async Task<ActionResult> Index(string month = null)
        {
            using (var client = new HttpClient())
            {
                var now = DateTime.Now;
                var selectedMonth = string.IsNullOrWhiteSpace(month) ? now.ToString("yyyy-MM") : month;
                if (!DateTime.TryParseExact($"{selectedMonth}-01", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out DateTime monthDate))
                {
                    monthDate = new DateTime(now.Year, now.Month, 1);
                    selectedMonth = monthDate.ToString("yyyy-MM");
                }

                var firstDayOfMonth = new DateTime(monthDate.Year, monthDate.Month, 1);
                var lastDayOfMonth = firstDayOfMonth.AddMonths(1).AddDays(-1);

                var payload = new
                {
                    startDate = firstDayOfMonth.ToString("yyyy-MM-dd"),
                    endDate = lastDayOfMonth.ToString("yyyy-MM-dd"),
                    month = selectedMonth
                };

                var content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/thong_ke", content);

                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể lấy dữ liệu thống kê.";
                    return View();
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                ViewBag.TotalOrders = data.totalOrders;
                ViewBag.PendingOrders = data.pendingOrders;
                ViewBag.ApprovedOrders = data.approvedOrders;
                ViewBag.DeliveredOrders = data.deliveredOrders;
                ViewBag.CancelledOrders = data.cancelledOrders;

                ViewBag.RevenuePending = data.revenuePending;
                ViewBag.RevenueApproved = data.revenueApproved;
                ViewBag.RevenueDelivered = data.revenueDelivered;
                ViewBag.RevenueCancelled = data.revenueCancelled;
                ViewBag.TotalRevenue = data.totalRevenue;
                ViewBag.BestSellingProducts = data.bestSellingProducts.ToObject<List<BestSellingProduct>>();
                ViewBag.SlowSellingProducts = data.slowSellingProducts.ToObject<List<BestSellingProduct>>();
                ViewBag.SelectedMonth = selectedMonth;
            }

            return View();
        }
        private List<SpecFilterInput> ParseSpecFilters(NameValueCollection query)
        {
            var filters = new List<SpecFilterInput>();
            if (query == null) return filters;

            foreach (string key in query.AllKeys)
            {
                if (string.IsNullOrEmpty(key) || !key.StartsWith("spec_", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                var value = query[key];
                if (string.IsNullOrWhiteSpace(value))
                {
                    continue;
                }

                if (int.TryParse(key.Substring(5), out int specId))
                {
                    filters.Add(new SpecFilterInput
                    {
                        MaThongSo = specId,
                        GiaTri = value.Trim()
                    });
                }
            }

            return filters;
        }

        private List<ThongSoKyThuat> DeserializeSpecValues(string payload)
        {
            if (string.IsNullOrWhiteSpace(payload))
            {
                return new List<ThongSoKyThuat>();
            }

            try
            {
                var result = JsonConvert.DeserializeObject<List<ThongSoKyThuat>>(payload);
                return result ?? new List<ThongSoKyThuat>();
            }
            catch
            {
                return new List<ThongSoKyThuat>();
            }
        }


        private class SpecFilterInput
        {
            public int MaThongSo { get; set; }
            public string GiaTri { get; set; }
        }
        #region Thông số kỹ thuật

        public async Task<ActionResult> QuanLyThongSo(string searchTerm = null, int? status = null, int page = 1, int pageSize = 10)
        {
            using (var client = new HttpClient())
            {
                var builder = new StringBuilder($"http://127.0.0.1:5000/api/spec-definitions?page={page}&pageSize={pageSize}");
                if (!string.IsNullOrWhiteSpace(searchTerm))
                {
                    builder.Append($"&search={HttpUtility.UrlEncode(searchTerm)}");
                }
                if (status.HasValue)
                {
                    builder.Append($"&status={status.Value}");
                }

                var response = await client.GetAsync(builder.ToString());
                if (!response.IsSuccessStatusCode)
                {
                    ViewBag.Message = "Không thể lấy danh sách thông số.";
                    return View(new List<ThongSoKyThuat>());
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data.success == true)
                {
                    var specs = data.specs.ToObject<List<ThongSoKyThuat>>();
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)data.totalPages;
                    ViewBag.SearchTerm = searchTerm;
                    ViewBag.Status = status;
                    return View(specs);
                }

                ViewBag.Message = data.message ?? "Không thể lấy dữ liệu.";
                return View(new List<ThongSoKyThuat>());
            }
        }

        public ActionResult ThemThongSo()
        {
            return View(new ThongSoKyThuat());
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemThongSo(ThongSoKyThuat model)
        {
            if (!ModelState.IsValid)
            {
                return View(model);
            }

            using (var client = new HttpClient())
            {
                var payload = JsonConvert.SerializeObject(model);
                var content = new StringContent(payload, Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/spec-definitions", content);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);
                    if (data.success == true)
                    {
                        return RedirectToAction("QuanLyThongSo");
                    }
                    ModelState.AddModelError("", data.message.ToString());
                }
                else
                {
                    ModelState.AddModelError("", "Không thể tạo thông số mới.");
                }
            }

            return View(model);
        }

        public async Task<ActionResult> SuaThongSo(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.GetAsync($"http://127.0.0.1:5000/api/spec-definitions/{id}");
                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không tìm thấy thông số.";
                    return RedirectToAction("QuanLyThongSo");
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);
                if (data.success == true)
                {
                    var spec = data.spec.ToObject<ThongSoKyThuat>();
                    return View(spec);
                }

                TempData["Error"] = data.message;
                return RedirectToAction("QuanLyThongSo");
            }
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> SuaThongSo(ThongSoKyThuat model)
        {
            if (!ModelState.IsValid)
            {
                return View(model);
            }

            using (var client = new HttpClient())
            {
                var payload = JsonConvert.SerializeObject(model);
                var content = new StringContent(payload, Encoding.UTF8, "application/json");
                var response = await client.PutAsync($"http://127.0.0.1:5000/api/spec-definitions/{model.MaThongSo}", content);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);
                    if (data.success == true)
                    {
                        return RedirectToAction("QuanLyThongSo");
                    }
                    ModelState.AddModelError("", data.message.ToString());
                }
                else
                {
                    ModelState.AddModelError("", "Không thể cập nhật thông số.");
                }
            }

            return View(model);
        }

        public async Task<ActionResult> CapNhatTrangThaiThongSo(int id)
        {
            using (var client = new HttpClient())
            {
                var request = new HttpRequestMessage(new HttpMethod("PATCH"), $"http://127.0.0.1:5000/api/spec-definitions/{id}/toggle");
                var response = await client.SendAsync(request);
                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể cập nhật trạng thái thông số.";
                }
            }
            return RedirectToAction("QuanLyThongSo");
        }

        #endregion
        // GET: QuanLySanPham
        public async Task<ActionResult> QuanLySanPham(int page = 1, int pageSize = 5, string searchTerm = "")
        {
            //   if (!check()) return RedirectToAction("Loi404", "Admin");

            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000"); // Đổi thành base URL Flask của bạn

                var specResponse = await client.GetAsync("/api/spec-definitions?active=1&pageSize=200");
                if (specResponse.IsSuccessStatusCode)
                {
                    var specJson = await specResponse.Content.ReadAsStringAsync();
                    dynamic specData = JsonConvert.DeserializeObject(specJson);
                    ViewBag.SpecDefinitions = specData.specs.ToObject<List<ThongSoKyThuat>>();
                }

                var specFilters = ParseSpecFilters(Request.QueryString);
                ViewBag.ActiveSpecFilters = specFilters.ToDictionary(x => x.MaThongSo, x => x.GiaTri);

                var payload = new
                {
                    SearchTerm = searchTerm ?? "",
                    Page = page,
                    PageSize = pageSize,
                    SpecFilters = specFilters.Select(f => new { f.MaThongSo, f.GiaTri }).ToList()
                };

                var content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("/api/get_sanpham_admin", content);

                if (response.IsSuccessStatusCode)
                {
                    var jsonString = await response.Content.ReadAsStringAsync();
                    dynamic result = JsonConvert.DeserializeObject(jsonString);

                    var sanPhams = JsonConvert.DeserializeObject<List<SanPham>>(Convert.ToString(result.sanPhams));

                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)result.totalPages;
                    ViewBag.SearchTerm = searchTerm;

                    return View(sanPhams);
                }

                // Xử lý lỗi
                return View(new List<SanPham>());
            }
        }

        public async Task<ActionResult> ChiTietSanPhamAdmin(int id)
        {
            using (var client = new HttpClient())
            {
                var requestData = new { productId = id };
                var content = new StringContent(JsonConvert.SerializeObject(requestData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_detail_product", content);

                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể lấy chi tiết sản phẩm.";
                    return RedirectToAction("QuanLySanPham");
                }

                var jsonResponse = await response.Content.ReadAsStringAsync();
                dynamic result = JsonConvert.DeserializeObject(jsonResponse);
                if (result.success == false)
                {
                    TempData["Error"] = result.message ?? "Không tìm thấy sản phẩm.";
                    return RedirectToAction("QuanLySanPham");
                }

                var sanPham = result.product.ToObject<SanPham>();
                ViewBag.ThongSoKyThuat = result.product.ThongSoKyThuat != null
                    ? result.product.ThongSoKyThuat.ToObject<List<ThongSoKyThuat>>()
                    : new List<ThongSoKyThuat>();
                ViewBag.SanPhamCungGia = result.similarProducts != null
                    ? result.similarProducts.ToObject<List<SanPham>>()
                    : new List<SanPham>();
                var serials = new List<SerialNumberViewModel>();
                if (result.product.SerialNumbers != null)
                {
                    foreach (var serial in result.product.SerialNumbers)
                    {
                        serials.Add(new SerialNumberViewModel
                        {
                            MaSerial = (int)serial.MaSerial,
                            SerialNumber = (string)serial.SerialNumber,
                            TrangThai = serial.TrangThai != null ? (string)serial.TrangThai : string.Empty,
                            NgayNhap = serial.NgayNhap != null ? (string)serial.NgayNhap : string.Empty,
                            NgayBan = serial.NgayBan != null ? (string)serial.NgayBan : string.Empty
                        });
                    }
                }
                ViewBag.SerialNumbers = serials;
                ViewBag.SerialCount = result.product.SerialCount != null ? (int)result.product.SerialCount : serials.Count;

                return View(sanPham);
            }
        }

        // GET: ThemSanPham
        public async Task<ActionResult> ThemSanPham()
        {
            //  if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            // Tạo một HttpClient để gọi API Flask
            using (var client = new HttpClient())
            {
                // Gửi yêu cầu GET đến API Flask để lấy danh mục sản phẩm
                var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");
                var specResponse = await client.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                {
                    var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                    var hangData = await hangResponse.Content.ReadAsStringAsync();
                    var specData = await specResponse.Content.ReadAsStringAsync();

                    // Deserialise dữ liệu trả về thành danh sách
                    ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                    ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                    dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                    ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                    ViewBag.SpecValues = new List<ThongSoKyThuat>();
                }
                else
                {
                    ViewBag.DanhMuc = new List<DanhMucSanPham>();
                    ViewBag.Hang = new List<HangSanPham>();
                    ViewBag.SpecDefinitions = new List<ThongSoKyThuat>();
                    ViewBag.SpecValues = new List<ThongSoKyThuat>();
                    ModelState.AddModelError("", "Lỗi khi gọi API.");
                    return RedirectToAction("QuanLySanPham");
                }

                return View();
            }
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemSanPham(SanPham model, HttpPostedFileBase HinhDaiDien, IEnumerable<HttpPostedFileBase> HinhKemTheo)
        {
            if (ModelState.IsValid)
            {
                var thongSoPayload = Request.Form["ThongSoPayload"] ?? "[]";
                var currentSpecs = DeserializeSpecValues(thongSoPayload);
                using (var client = new HttpClient())
                using (var formData = new MultipartFormDataContent())
                {
                    // Thêm thông tin sản phẩm
                    formData.Add(new StringContent(model.TenSanPham), "TenSanPham");
                    formData.Add(new StringContent(model.MoTa ?? ""), "MoTa");
                    formData.Add(new StringContent(model.Gia.ToString()), "Gia");
                    formData.Add(new StringContent(model.MaDanhMuc.ToString()), "MaDanhMuc");
                    formData.Add(new StringContent(model.MaHang.ToString()), "MaHang");
                    formData.Add(new StringContent(model.SoLuong.ToString()), "SoLuong");
                    formData.Add(new StringContent(thongSoPayload, Encoding.UTF8, "application/json"), "ThongSoKyThuat");
                    // Hình đại diện
                    if (HinhDaiDien != null && HinhDaiDien.ContentLength > 0)
                    {
                        var stream = HinhDaiDien.InputStream;
                        var content = new StreamContent(stream);
                        content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(HinhDaiDien.ContentType);
                        formData.Add(content, "HinhDaiDien", Path.GetFileName(HinhDaiDien.FileName));
                    }

                    // Hình kèm theo
                    if (HinhKemTheo != null)
                    {
                        foreach (var hinh in HinhKemTheo)
                        {
                            if (hinh != null && hinh.ContentLength > 0)
                            {
                                var stream = hinh.InputStream;
                                var content = new StreamContent(stream);
                                content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(hinh.ContentType);
                                formData.Add(content, "HinhKemTheo", Path.GetFileName(hinh.FileName));
                            }
                        }
                    }

                    // Gửi request đến API Flask để thêm sản phẩm
                    var response = await client.PostAsync("http://127.0.0.1:5000/api/create_sanpham", formData);
                    if (response.IsSuccessStatusCode)
                    {
                        var jsonResponse = await response.Content.ReadAsStringAsync();
                        var result = JsonConvert.DeserializeObject<dynamic>(jsonResponse);
                        if (result.success.Value)
                        {
                            int maSanPham = result.MaSanPham;

                            // Tạo thư mục đích: img/product/{maSanPham}
                            string folderPath = Server.MapPath($"~/assets/images/product/{maSanPham}");
                            if (!Directory.Exists(folderPath))
                            {
                                Directory.CreateDirectory(folderPath);
                            }

                            // Lưu hình đại diện
                            if (HinhDaiDien != null && HinhDaiDien.ContentLength > 0)
                            {
                                string fileName = Path.GetFileName(HinhDaiDien.FileName);
                                string filePath = Path.Combine(folderPath, fileName);
                                HinhDaiDien.SaveAs(filePath);

                            }

                            // Lưu các hình kèm theo
                            if (HinhKemTheo != null)
                            {
                                foreach (var hinh in HinhKemTheo)
                                {
                                    if (hinh != null && hinh.ContentLength > 0)
                                    {
                                        string fileName = Path.GetFileName(hinh.FileName);
                                        string filePath = Path.Combine(folderPath, fileName);
                                        hinh.SaveAs(filePath);
                                    }
                                }
                            }

                            // Sau khi lưu xong có thể gọi lại API cập nhật hình ảnh (nếu cần)
                            return RedirectToAction("QuanLySanPham");
                        }

                        else
                        {
                            var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                            var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");
                            var specResponse = await client.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                            if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                            {
                                var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                                var hangData = await hangResponse.Content.ReadAsStringAsync();
                                var specData = await specResponse.Content.ReadAsStringAsync();

                                // Deserialise dữ liệu trả về thành danh sách
                                ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                                ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                                dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                                ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                                ViewBag.SpecValues = currentSpecs;
                            }
                            ModelState.AddModelError("", "Lỗi khi tạo sản phẩm.");
                        }
                    }
                    else
                    {
                        var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                        var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");
                        var specResponse = await client.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                        if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                        {
                            var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                            var hangData = await hangResponse.Content.ReadAsStringAsync();
                            var specData = await specResponse.Content.ReadAsStringAsync();

                            // Deserialise dữ liệu trả về thành danh sách
                            ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                            ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                            dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                            ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                            ViewBag.SpecValues = currentSpecs;
                        }
                        ModelState.AddModelError("", "Lỗi khi gọi API.");
                    }
                }
            }

            if (ViewBag.DanhMuc == null || ViewBag.Hang == null || ViewBag.SpecDefinitions == null)
            {
                using (var lookupClient = new HttpClient())
                {
                    var danhMucResponse = await lookupClient.GetAsync("http://127.0.0.1:5000/api/categories");
                    var hangResponse = await lookupClient.GetAsync("http://127.0.0.1:5000/api/get_hang");
                    var specResponse = await lookupClient.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                    if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                    {
                        var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                        var hangData = await hangResponse.Content.ReadAsStringAsync();
                        var specData = await specResponse.Content.ReadAsStringAsync();
                        ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                        ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                        dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                        ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                    }
                }
            }

            if (ViewBag.SpecValues == null)
            {
                ViewBag.SpecValues = DeserializeSpecValues(Request.Form["ThongSoPayload"]);
            }

            return View(model);
        }

        [HttpGet]
        public async Task<ActionResult> SuaSanPham(int id)
        {
            // Tạo một HttpClient để gọi API Flask
            using (var client = new HttpClient())
            {
                var requestData = new
                {
                    productId = id
                };

                // Chuyển dữ liệu thành JSON
                var content = new StringContent(JsonConvert.SerializeObject(requestData), Encoding.UTF8, "application/json");

                // Gửi yêu cầu POST đến API Flask
                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_detail_product", content);

                if (response.IsSuccessStatusCode)
                {
                    var jsonResponse = await response.Content.ReadAsStringAsync();
                    var result = JsonConvert.DeserializeObject<dynamic>(jsonResponse);

                    if (result.success == false)
                    {
                        return HttpNotFound();
                    }

                    var sanPham = result.product.ToObject<SanPham>(); // Convert from dynamic to SanPham

                    // Gán danh sách danh mục và hãng sản phẩm vào ViewBag
                    var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                    var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");
                    var specResponse = await client.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                    if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                    {
                        var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                        var hangData = await hangResponse.Content.ReadAsStringAsync();
                        var specData = await specResponse.Content.ReadAsStringAsync();
                        ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                        ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                        dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                        ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                        ViewBag.SpecValues = result.product.ThongSoKyThuat.ToObject<List<ThongSoKyThuat>>();
                    }

                    return View(sanPham);
                }
                else
                {
                    ModelState.AddModelError("", "Lỗi khi gọi API.");
                    return RedirectToAction("QuanLySanPham");
                }
            }
        }





        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> SuaSanPham(SanPham model, HttpPostedFileBase HinhDaiDien, IEnumerable<HttpPostedFileBase> HinhKemTheo)
        {
            if (ModelState.IsValid)
            {
                var thongSoPayload = Request.Form["ThongSoPayload"] ?? "[]";
                var currentSpecs = DeserializeSpecValues(thongSoPayload);
                using (var client = new HttpClient())
                using (var formData = new MultipartFormDataContent())
                {
                    // Thêm thông tin sản phẩm
                    formData.Add(new StringContent(model.TenSanPham), "TenSanPham");
                    formData.Add(new StringContent(model.MoTa ?? ""), "MoTa");
                    formData.Add(new StringContent(model.Gia.ToString()), "Gia");
                    formData.Add(new StringContent(model.MaDanhMuc.ToString()), "MaDanhMuc");
                    formData.Add(new StringContent(model.MaHang.ToString()), "MaHang");
                    formData.Add(new StringContent(thongSoPayload, Encoding.UTF8, "application/json"), "ThongSoKyThuat");

                    // Hình đại diện
                    if (HinhDaiDien != null && HinhDaiDien.ContentLength > 0)
                    {
                        var stream = HinhDaiDien.InputStream;
                        var content = new StreamContent(stream);
                        content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(HinhDaiDien.ContentType);
                        formData.Add(content, "HinhDaiDien", Path.GetFileName(HinhDaiDien.FileName));
                    }

                    // Hình kèm theo
                    if (HinhKemTheo != null)
                    {
                        foreach (var hinh in HinhKemTheo)
                        {
                            if (hinh != null && hinh.ContentLength > 0)
                            {
                                var stream = hinh.InputStream;
                                var content = new StreamContent(stream);
                                content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(hinh.ContentType);
                                formData.Add(content, "HinhKemTheo", Path.GetFileName(hinh.FileName));
                            }
                        }
                    }

                    // Gửi request đến API Flask để cập nhật sản phẩm
                    var response = await client.PostAsync($"http://127.0.0.1:5000/api/update_sanpham/{model.MaSanPham}", formData);
                    if (response.IsSuccessStatusCode)
                    {
                        var jsonResponse = await response.Content.ReadAsStringAsync();
                        var result = JsonConvert.DeserializeObject<dynamic>(jsonResponse);
                        if (result.success.Value)
                        {
                            return RedirectToAction("QuanLySanPham");
                        }
                        else
                        {
                            var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                            var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");
                            var specResponse = await client.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                            if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                            {
                                var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                                var hangData = await hangResponse.Content.ReadAsStringAsync();
                                var specData = await specResponse.Content.ReadAsStringAsync();
                                ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                                ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                                dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                                ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                                ViewBag.SpecValues = currentSpecs;
                            }
                            ModelState.AddModelError("", "Lỗi khi cập nhật sản phẩm.");
                            return View(model);

                        }
                    }
                    else
                    {
                        var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                        var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");
                        var specResponse = await client.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                        if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                        {
                            var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                            var hangData = await hangResponse.Content.ReadAsStringAsync();
                            var specData = await specResponse.Content.ReadAsStringAsync();
                            ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                            ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                            dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                            ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                            ViewBag.SpecValues = currentSpecs;
                        }
                        ModelState.AddModelError("", "Lỗi khi gọi API.");
                        return View(model);

                    }
                }
            }


            if (ViewBag.DanhMuc == null || ViewBag.Hang == null || ViewBag.SpecDefinitions == null)
            {
                using (var lookupClient = new HttpClient())
                {
                    var danhMucResponse = await lookupClient.GetAsync("http://127.0.0.1:5000/api/categories");
                    var hangResponse = await lookupClient.GetAsync("http://127.0.0.1:5000/api/get_hang");
                    var specResponse = await lookupClient.GetAsync("http://127.0.0.1:5000/api/spec-definitions?active=1&pageSize=200");

                    if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode && specResponse.IsSuccessStatusCode)
                    {
                        var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                        var hangData = await hangResponse.Content.ReadAsStringAsync();
                        var specData = await specResponse.Content.ReadAsStringAsync();
                        ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                        ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                        dynamic parsedSpecs = JsonConvert.DeserializeObject(specData);
                        ViewBag.SpecDefinitions = parsedSpecs.specs.ToObject<List<ThongSoKyThuat>>();
                    }
                }
            }

            if (ViewBag.SpecValues == null)
            {
                ViewBag.SpecValues = DeserializeSpecValues(Request.Form["ThongSoPayload"]);
            }

            return View(model);
        }

        public async Task<ActionResult> QuanLyDanhMuc(int page = 1, int pageSize = 5, string searchTerm = null)
        {
            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/danhmuc?page={page}&pageSize={pageSize}&search={searchTerm}";
                var response = await client.GetAsync(url);

                if (!response.IsSuccessStatusCode)
                {
                    ViewBag.Message = "Có lỗi khi kết nối đến API.";
                    return View();
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data != null && data.success == true)
                {
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)Math.Ceiling((double)data.total / pageSize);
                    ViewBag.SearchTerm = searchTerm; // Giữ từ khóa tìm kiếm

                    if (data.categories != null)
                    {
                        return View(data.categories);
                    }
                    else
                    {
                        ViewBag.Message = "Không có danh mục sản phẩm nào.";
                        return View();
                    }
                }
                else
                {
                    ViewBag.Message = data != null ? data.message : "Không thể lấy dữ liệu từ API.";
                    return View();
                }
            }
        }


  

        public ActionResult ThemDanhMuc()
        {
            return View();
        }

        [HttpPost]
        public async Task<ActionResult> ThemDanhMuc(DanhMucSanPham model)
        {
            if (string.IsNullOrWhiteSpace(model.TenDanhMuc))
            {
                ModelState.AddModelError("TenDanhMuc", "Tên danh mục không được để trống.");
                return View(model);
            }

            using (var client = new HttpClient())
            {
                var checkNameUrl = $"http://127.0.0.1:5000/api/danhmuc";
                var checkResponse = await client.GetAsync($"{checkNameUrl}?search={model.TenDanhMuc}");
                var checkResult = await checkResponse.Content.ReadAsStringAsync();
                dynamic checkData = JsonConvert.DeserializeObject(checkResult);

                bool success = Convert.ToBoolean(checkData.success);
                if (success && checkData.categories.Count > 0)
                {
                    ModelState.AddModelError("TenDanhMuc", "Tên danh mục này đã tồn tại.");
                    return View(model);
                }
            }

            using (var client = new HttpClient())
            {
                var data = new { TenDanhMuc = model.TenDanhMuc };
                var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/danhmuc", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic responseData = JsonConvert.DeserializeObject(result);

                bool responseSuccess = Convert.ToBoolean(responseData.success);
                if (responseSuccess)
                {
                    return RedirectToAction("QuanLyDanhMuc");
                }
                else
                {
                    ModelState.AddModelError("", responseData.message);
                    return View(model);
                }
            }
        }


        public async Task<ActionResult> SuaDanhMuc(int id)
        {
            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/get_danhmuc_by_id/{id}";
                var response = await client.GetAsync(url);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    var apiResponse = JsonConvert.DeserializeObject<dynamic>(result);

                    if (apiResponse.success == true && apiResponse.category != null)
                    {
                        var danhMuc = JsonConvert.DeserializeObject<DanhMucSanPham>(apiResponse.category.ToString());
                        return View(danhMuc);
                    }
                    else
                    {
                        ModelState.AddModelError("", apiResponse.message.ToString());
                        return View();
                    }
                }
                else
                {
                    var errorResponse = await response.Content.ReadAsStringAsync();
                    var errorData = JsonConvert.DeserializeObject<dynamic>(errorResponse);
                    ModelState.AddModelError("", errorData.message.ToString());
                    return View();
                }
            }
        }

        [HttpPost]
        public async Task<ActionResult> SuaDanhMuc(DanhMucSanPham model)
        {
            if (string.IsNullOrWhiteSpace(model.TenDanhMuc))
            {
                ModelState.AddModelError("TenDanhMuc", "Tên danh mục không được để trống.");
                return View(model);
            }

            using (var client = new HttpClient())
            {
                var checkNameUrl = $"http://127.0.0.1:5000/api/danhmuc";
                var checkResponse = await client.GetAsync($"{checkNameUrl}?search={model.TenDanhMuc}");
                var checkResult = await checkResponse.Content.ReadAsStringAsync();
                dynamic checkData = JsonConvert.DeserializeObject(checkResult);

                bool success = Convert.ToBoolean(checkData.success);
                if (success && checkData.categories.Count > 0)
                {
                    ModelState.AddModelError("TenDanhMuc", "Tên danh mục này đã tồn tại.");
                    return View(model);
                }
            }

            using (var client = new HttpClient())
            {
                var data = new { MaDanhMuc = model.MaDanhMuc, TenDanhMuc = model.TenDanhMuc };
                var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                var response = await client.PutAsync("http://127.0.0.1:5000/api/danhmuc", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic responseData = JsonConvert.DeserializeObject(result);

                bool responseSuccess = Convert.ToBoolean(responseData.success);
                if (responseSuccess)
                {
                    return RedirectToAction("QuanLyDanhMuc");
                }
                else
                {
                    ModelState.AddModelError("", responseData.message);
                    return View(model);
                }
            }
        }


        public async Task<ActionResult> CapNhatTrangThai(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.PutAsync($"http://127.0.0.1:5000/api/danhmuc/{id}/toggle", null);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                bool success = Convert.ToBoolean(data.success);
                if (success)
                {
                    return RedirectToAction("QuanLyDanhMuc");
                }
                else
                {
                    ViewBag.Message = data.message.ToString();
                    return RedirectToAction("QuanLyDanhMuc");
                }
            }
        }

        // Quản lý hãng sản phẩm
        public async Task<ActionResult> QuanLyHang(int page = 1, int pageSize = 5, string searchTerm = null)
        {
          //  if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                // Gọi API để lấy danh sách danh mục
                var url = $"http://127.0.0.1:5000/api/hang?page={page}&pageSize={pageSize}&search={searchTerm}";
                var response = await client.GetAsync(url);

                if (!response.IsSuccessStatusCode)
                {
                    // Kiểm tra nếu có lỗi khi gọi API
                    ViewBag.Message = "Có lỗi khi kết nối đến API.";
                    return View();
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                // Kiểm tra success và đảm bảo có dữ liệu trả về
                if (data != null && data.success != null && data.success == true)
                {
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = data.total != null ? (int)Math.Ceiling((double)data.total / pageSize) : 0;
                    ViewBag.SearchTerm = searchTerm; // Giữ từ khóa tìm kiếm

                    // Kiểm tra nếu danh sách danh mục tồn tại
                    if (data.categories != null)
                    {
                        // Chuyển đổi JArray thành IEnumerable<HangSanPham>
                        var categories = data.categories.ToObject<List<HangSanPham>>();
                        return View(data.categories);
                    }
                    else
                    {
                        ViewBag.Message = "Không có danh mục sản phẩm nào.";
                        return View();
                    }
                }
                else
                {
                    // Nếu API trả về không thành công, hiển thị thông báo lỗi
                    ViewBag.Message = data != null ? data.message : "Không thể lấy dữ liệu từ API.";
                    return View();
                }
            }
        }



        public ActionResult ThemHang()
        {
         //   if (!check()) { return RedirectToAction("Loi404", "Admin"); }
            return View();
        }
        [HttpPost]
        public async Task<ActionResult> ThemHang(HangSanPham model)
        {
            if (string.IsNullOrWhiteSpace(model.TenHang))
            {
                ModelState.AddModelError("TenHang", "Tên không được để trống.");
                return View(model);
            }

            // Kiểm tra tên danh mục trùng từ API
            using (var client = new HttpClient())
            {
                var checkNameUrl = $"http://127.0.0.1:5000/api/hang";
                var checkResponse = await client.GetAsync($"{checkNameUrl}?search={model.TenHang}");
                var checkResult = await checkResponse.Content.ReadAsStringAsync();
                dynamic checkData = JsonConvert.DeserializeObject(checkResult);

                // Chuyển đổi checkData.success thành bool
                bool success = Convert.ToBoolean(checkData.success);

                if (success && checkData.categories.Count > 0)
                {
                    ModelState.AddModelError("TenHang", "Tên này đã tồn tại.");
                    return View(model);
                }
            }

            // Thêm danh mục mới qua API
            using (var client = new HttpClient())
            {
                var data = new
                {
                    TenHang = model.TenHang
                };

                var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/hang", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic responseData = JsonConvert.DeserializeObject(result);

                bool responseSuccess = Convert.ToBoolean(responseData.success);

                if (responseSuccess)
                {
                    return RedirectToAction("QuanLyHang");
                }
                else
                {
                    ModelState.AddModelError("", responseData.message);
                    return View(model);
                }
            }
        }



        #region Nhà cung cấp

        public async Task<ActionResult> QuanLyNhaCungCap(string searchTerm = null, int? status = null, int page = 1, int pageSize = 10)
        {
            using (var client = new HttpClient())
            {
                var builder = new StringBuilder($"http://127.0.0.1:5000/api/suppliers?page={page}&pageSize={pageSize}");
                if (!string.IsNullOrWhiteSpace(searchTerm))
                {
                    builder.Append($"&search={HttpUtility.UrlEncode(searchTerm)}");
                }
                if (status.HasValue)
                {
                    builder.Append($"&status={status.Value}");
                }

                var response = await client.GetAsync(builder.ToString());
                if (!response.IsSuccessStatusCode)
                {
                    ViewBag.Message = "Không thể lấy danh sách nhà cung cấp.";
                    return View(new List<NhaCungCap>());
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data.success == true)
                {
                    var suppliers = data.suppliers.ToObject<List<NhaCungCap>>();
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)data.totalPages;
                    ViewBag.SearchTerm = searchTerm;
                    ViewBag.Status = status;
                    return View(suppliers);
                }

                ViewBag.Message = data.message ?? "Không thể lấy dữ liệu.";
                return View(new List<NhaCungCap>());
            }
        }

        public ActionResult ThemNhaCungCap()
        {
            return View(new NhaCungCap());
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemNhaCungCap(NhaCungCap model)
        {
            if (!ModelState.IsValid)
            {
                return View(model);
            }

            using (var client = new HttpClient())
            {
                var payload = JsonConvert.SerializeObject(model);
                var content = new StringContent(payload, Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/suppliers", content);
                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);
                    if (data.success == true)
                    {
                        return RedirectToAction("QuanLyNhaCungCap");
                    }
                    ModelState.AddModelError("", data.message.ToString());
                }
                else
                {
                    ModelState.AddModelError("", "Không thể tạo nhà cung cấp mới.");
                }
            }

            return View(model);
        }

        public async Task<ActionResult> SuaNhaCungCap(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.GetAsync($"http://127.0.0.1:5000/api/suppliers/{id}");
                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không tìm thấy nhà cung cấp.";
                    return RedirectToAction("QuanLyNhaCungCap");
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);
                if (data.success == true)
                {
                    var supplier = data.supplier.ToObject<NhaCungCap>();
                    return View(supplier);
                }

                TempData["Error"] = data.message;
                return RedirectToAction("QuanLyNhaCungCap");
            }
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> SuaNhaCungCap(NhaCungCap model)
        {
            if (!ModelState.IsValid)
            {
                return View(model);
            }

            using (var client = new HttpClient())
            {
                var payload = JsonConvert.SerializeObject(model);
                var content = new StringContent(payload, Encoding.UTF8, "application/json");
                var response = await client.PutAsync($"http://127.0.0.1:5000/api/suppliers/{model.MaNhaCungCap}", content);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);
                    if (data.success == true)
                    {
                        return RedirectToAction("QuanLyNhaCungCap");
                    }
                    ModelState.AddModelError("", data.message.ToString());
                }
                else
                {
                    ModelState.AddModelError("", "Không thể cập nhật nhà cung cấp.");
                }
            }

            return View(model);
        }

        public async Task<ActionResult> CapNhatTrangThaiNhaCungCap(int id)
        {
            using (var client = new HttpClient())
            {
                var request = new HttpRequestMessage(new HttpMethod("PATCH"), $"http://127.0.0.1:5000/api/suppliers/{id}/toggle");
                var response = await client.SendAsync(request);
                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể cập nhật trạng thái nhà cung cấp.";
                }
            }
            return RedirectToAction("QuanLyNhaCungCap");
        }

        #endregion

        public async Task<ActionResult> SuaHang(int id)
        {
            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/get_category_by_id/{id}"; // API lấy chi tiết sản phẩm theo ID
                var response = await client.GetAsync(url);

                if (response.IsSuccessStatusCode)
                {
                    // Đọc kết quả từ response và chuyển thành đối tượng dynamic
                    var result = await response.Content.ReadAsStringAsync();
                    var apiResponse = JsonConvert.DeserializeObject<dynamic>(result);

                    // Kiểm tra nếu thành công và có category
                    if (apiResponse.success == true && apiResponse.category != null)
                    {
                        // Chuyển category thành đối tượng HangSanPham
                        var danhMuc = JsonConvert.DeserializeObject<HangSanPham>(apiResponse.category.ToString());

                        if (danhMuc == null)
                        {
                            return HttpNotFound();
                        }

                        return View(danhMuc);
                    }
                    else
                    {
                        // Trường hợp API trả về lỗi hoặc không tìm thấy danh mục
                        ModelState.AddModelError("", apiResponse.message.ToString());
                        return View();
                    }
                }
                else
                {
                    // Xử lý lỗi khi API trả về lỗi
                    var errorResponse = await response.Content.ReadAsStringAsync();
                    var errorData = JsonConvert.DeserializeObject<dynamic>(errorResponse);
                    ModelState.AddModelError("", errorData.message.ToString());
                    return View();
                }
            }
        }



        [HttpPost]
        public async Task<ActionResult> SuaHang(HangSanPham model)
        {
            if (string.IsNullOrWhiteSpace(model.TenHang))
            {
                ModelState.AddModelError("TenHang", "Tên không được để trống.");
                return View(model);
            }

            // Kiểm tra tên danh mục trùng từ API
            using (var client = new HttpClient())
            {
                var checkNameUrl = $"http://127.0.0.1:5000/api/hang";
                var checkResponse = await client.GetAsync($"{checkNameUrl}?search={model.TenHang}");
                var checkResult = await checkResponse.Content.ReadAsStringAsync();
                dynamic checkData = JsonConvert.DeserializeObject(checkResult);

                // Chuyển đổi checkData.success thành bool
                bool success = Convert.ToBoolean(checkData.success);

                if (success && checkData.categories.Count > 0)
                {
                    ModelState.AddModelError("TenDanhMuc", "Tên này đã tồn tại.");
                    return View(model);
                }
            }

            // Cập nhật danh mục qua API
            using (var client = new HttpClient())
            {
                var data = new
                {
                    MaHang = model.MaHang,
                    TenHang = model.TenHang
                };

                var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                var response = await client.PutAsync("http://127.0.0.1:5000/api/hang", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic responseData = JsonConvert.DeserializeObject(result);

                // Chuyển đổi responseData.success thành bool
                bool responseSuccess = Convert.ToBoolean(responseData.success);

                if (responseSuccess)
                {
                    return RedirectToAction("QuanLyHang");
                }
                else
                {
                    ModelState.AddModelError("", responseData.message);
                    return View(model);
                }
            }
        }



        public async Task<ActionResult> CapNhatTrangThaiHang(int id)
        {
            using (var client = new HttpClient())
            {
                // Gọi API để thay đổi trạng thái
                var response = await client.PutAsync($"http://127.0.0.1:5000/api/hang/{id}/toggle", null);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                // Chuyển đổi checkData.success thành bool nếu không phải kiểu bool
                bool success = Convert.ToBoolean(data.success);

                if (success)
                {
                    return RedirectToAction("QuanLyHang");
                }
                else
                {
                    ViewBag.Message = data.message.ToString();
                    return RedirectToAction("QuanLyHang");
                }
            }
        }

        // Quản lý khách hàng
        public async Task<ActionResult> QuanLyKhachHang(int page = 1, int pageSize = 5, string searchTerm = null)
        {
         //   if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            // Gọi API để lấy dữ liệu danh sách khách hàng
            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000");  // URL của Flask API

                // Xây dựng URL với tham số trang và kích thước trang
                var url = $"/api/khachhang?page={page}&pageSize={pageSize}&search={searchTerm}";

                // Gọi API GET
                var response = await client.GetAsync(url);
                if (response.IsSuccessStatusCode)
                {
                    Debug.WriteLine("Kết nối thành công đến API");
                    // Đọc kết quả trả về từ API
                    var data = await response.Content.ReadAsStringAsync();
                    var result = JsonConvert.DeserializeObject<dynamic>(data);
                    
                    // Kiểm tra dữ liệu trả về từ API
                    if (result != null && result.success != null && result.success == true)
                    {
                        ViewBag.CurrentPage = page;

                        // Tính toán tổng số trang
                        ViewBag.TotalPages = result.total != null ? (int)Math.Ceiling((double)result.total / pageSize) : 0;
                        ViewBag.SearchTerm = searchTerm; // Giữ từ khóa tìm kiếm

                        // Kiểm tra nếu danh sách khách hàng tồn tại
                        if (result.khachhang != null)
                        {
                            // Chuyển đổi JArray thành IEnumerable<KhachHang>
                            var categories = result.khachhang.ToObject<List<TaiKhoan>>();
                            ViewBag.TaiKhoan = categories;
                            // Trả về view với dữ liệu khách hàng
                            return View();
                        }
                        else
                        {
                            ViewBag.Message = "Không có khách hàng nào.";
                            return View();
                        }
                    }
                    else
                    {
                        // Nếu API trả về không thành công
                        ViewBag.Message = result != null ? result.message : "Không thể lấy dữ liệu từ API.";
                        return View();
                    }
                }
                else
                {
                    // Xử lý lỗi khi không thể kết nối tới API
                    ViewBag.Message = "Không thể kết nối đến API.";
                    return View();
                }
            }
        }



        public async Task<ActionResult> CapNhatTrangThaiKH(int id)
        {
            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000"); // URL của Flask API

                // Gọi API PUT để cập nhật trạng thái
                var response = await client.PutAsync($"/api/capnhat_trangthai_taikhoan/{id}/toggle", null);

                if (response.IsSuccessStatusCode)
                {
                    return RedirectToAction("QuanLyKhachHang");
                }
                else
                {
                    // Xử lý lỗi nếu không thành công
                    return RedirectToAction("Loi404", "Admin");
                }
            }
        }

        [HttpPost]
        public async Task<ActionResult> GiamGia(int maSanPham, decimal giaMoi)
        {
            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000");
                var payload = new { MaSanPham = maSanPham, GiaMoi = giaMoi };
                var content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("/api/giamgia", content);
                if (response.IsSuccessStatusCode)
                {
                    return Json(new { success = true });
                }
                return Json(new { success = false });
            }
        }

        [HttpPost]
        public async Task<ActionResult> NgungGiamGia(int id)
        {
            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000");
                var payload = new { MaSanPham = id };
                var content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("/api/ngunggiamgia", content);
                if (response.IsSuccessStatusCode)
                {
                    return RedirectToAction("QuanLySanPham");
                }
                return RedirectToAction("Loi404", "Admin");
            }
        }


        // Cập nhật trạng thái sản phẩm
        public async Task<ActionResult> CapNhatTrangThaiSP(int id)
        {
            using (var client = new HttpClient())
            {
                // Gọi API để lấy chi tiết sản phẩm
                var detailPayload = new
                {
                    productId = id
                };

                var detailContent = new StringContent(JsonConvert.SerializeObject(detailPayload), Encoding.UTF8, "application/json");
                var detailResponse = await client.PostAsync("http://127.0.0.1:5000/api/get_detail_product", detailContent); // <-- thay đổi đúng port

                if (!detailResponse.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể lấy thông tin sản phẩm.";
                    return RedirectToAction("QuanLySanPham");
                }

                var detailResult = await detailResponse.Content.ReadAsStringAsync();
                dynamic detailJson = JsonConvert.DeserializeObject(detailResult);

                bool currentStatus = detailJson.product.TrangThai;

                // Gọi API để cập nhật trạng thái sản phẩm
                var updatePayload = new
                {
                    MaSanPham = id,
                    TrangThai = !currentStatus // đảo trạng thái
                };

                var updateContent = new StringContent(JsonConvert.SerializeObject(updatePayload), Encoding.UTF8, "application/json");
                var updateResponse = await client.PostAsync("http://127.0.0.1:5000/api/ngung_ban", updateContent); // <-- thay đổi đúng port

                if (!updateResponse.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể cập nhật trạng thái sản phẩm.";
                }
            }

            return RedirectToAction("QuanLySanPham");
        }
        // GET: Voucher
        public async Task<ActionResult> QuanLyVoucher(int page = 1, int pageSize = 5, string searchTerm = null)
        {
           // if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/get_all_voucher?page={page}&pageSize={pageSize}&search={searchTerm}";
                var response = await client.GetAsync(url);

                if (!response.IsSuccessStatusCode)
                {
                    ViewBag.Message = "Có lỗi khi kết nối đến API.";
                    return View();
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data != null && data.success != null && data.success == true)
                {
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = data.total != null ? (int)Math.Ceiling((double)data.total / pageSize) : 0;
                    ViewBag.SearchTerm = searchTerm; // Giữ từ khóa tìm kiếm

                    if (data.vouchers != null)
                    {
                        var vouchers = data.vouchers.ToObject<List<Voucher>>(); // Chuyển dữ liệu từ JSON thành list voucher
                        return View(vouchers);
                    }
                    else
                    {
                        ViewBag.Message = "Không có voucher nào.";
                        return View();
                    }
                }
                else
                {
                    ViewBag.Message = data != null ? data.message : "Không thể lấy dữ liệu từ API.";
                    return View();
                }
            }
        }



        public ActionResult ThemVoucher()
        {
         //   if (!check()) { return RedirectToAction("Loi404", "Admin"); }
            return View();
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemVoucher(Voucher voucher)
        {
            if (ModelState.IsValid)
            {
                // Kiểm tra ngày bắt đầu không được nhỏ hơn ngày hiện tại
                if (voucher.NgayBatDau < DateTime.Now.Date)
                {
                    ModelState.AddModelError("NgayBatDau", "Ngày bắt đầu không được nhỏ hơn ngày hiện tại.");
                    return View(voucher);
                }

                // Kiểm tra ngày kết thúc phải sau ngày bắt đầu
                if (voucher.NgayBatDau > voucher.NgayKetThuc)
                {
                    ModelState.AddModelError("NgayKetThuc", "Ngày kết thúc phải sau ngày bắt đầu.");
                    return View(voucher);
                }

                // Kiểm tra tỷ lệ giảm giá không vượt quá 100
                if (voucher.GiamGia > 100)
                {
                    ModelState.AddModelError("GiamGia", "Tỷ lệ giảm giá không được vượt quá 100%.");
                    return View(voucher);
                }

                // Gửi voucher mới qua API
                using (var client = new HttpClient())
                {
                    var data = new
                    {
                        Code = voucher.Code,
                        GiamGia = voucher.GiamGia,
                        NgayBatDau = voucher.NgayBatDau,
                        NgayKetThuc = voucher.NgayKetThuc,
                        SoLuongSuDungToiDa = voucher.SoLuongSuDungToiDa,
                        MoTa = voucher.MoTa
                    };

                    var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                    var response = await client.PostAsync("http://127.0.0.1:5000/api/voucher", content);
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic responseData = JsonConvert.DeserializeObject(result);

                    bool success = Convert.ToBoolean(responseData.success);

                    if (success)
                    {
                        return RedirectToAction("QuanLyVoucher");
                    }
                    else
                    {
                        ModelState.AddModelError("", responseData.message);
                        return View(voucher);
                    }
                }
            }

            return View(voucher);
        }


        // GET: Voucher/Sua/5
        public async Task<ActionResult> SuaVoucher(int id)
        {
            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/voucher/{id}"; // API lấy chi tiết voucher theo ID
                var response = await client.GetAsync(url);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    var apiResponse = JsonConvert.DeserializeObject<dynamic>(result);

                    if (apiResponse.success == true && apiResponse.voucher != null)
                    {
                        var voucher = JsonConvert.DeserializeObject<Voucher>(apiResponse.voucher.ToString());
                        return View(voucher);
                    }
                    else
                    {
                        ModelState.AddModelError("", apiResponse.message.ToString());
                        return View();
                    }
                }
                else
                {
                    var errorResponse = await response.Content.ReadAsStringAsync();
                    var errorData = JsonConvert.DeserializeObject<dynamic>(errorResponse);
                    ModelState.AddModelError("", errorData.message.ToString());
                    return View();
                }
            }
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> SuaVoucher(Voucher voucher)
        {
            if (ModelState.IsValid)
            {
                using (var client = new HttpClient())
                {
                    // Tạo đối tượng data từ voucher
                    var data = new
                    {
                        MaVoucher = voucher.MaVoucher,
                        Code = voucher.Code,
                        GiamGia = voucher.GiamGia,
                        NgayBatDau = voucher.NgayBatDau,
                        NgayKetThuc = voucher.NgayKetThuc,
                        SoLuongSuDungToiDa = voucher.SoLuongSuDungToiDa,
                        MoTa = voucher.MoTa
                    };

                    // Chuyển đối tượng data thành JSON và gói nó vào StringContent
                    var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");

                    // Gửi yêu cầu PUT tới API
                    var response = await client.PutAsync($"http://127.0.0.1:5000/api/voucher/{voucher.MaVoucher}", content);

                    // Đọc phản hồi trả về từ server
                    var result = await response.Content.ReadAsStringAsync();

                    // Giải mã JSON trả về từ server
                    dynamic responseData = JsonConvert.DeserializeObject(result);

                    // Kiểm tra kết quả trả về
                    bool success = Convert.ToBoolean(responseData.success);

                    if (success)
                    {
                        // Nếu cập nhật thành công, chuyển hướng về trang quản lý voucher
                        return RedirectToAction("QuanLyVoucher");
                    }
                    else
                    {
                        // Nếu thất bại, thêm lỗi vào ModelState và hiển thị lại trang
                        ModelState.AddModelError("", responseData.message);
                        return View(voucher);
                    }
                }
            }

            return View(voucher);
        }


        public async Task<ActionResult> ChuyenDoiTrangThai(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.PutAsync($"http://127.0.0.1:5000/api/voucher/{id}/toggle", null);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                bool success = Convert.ToBoolean(data.success);

                if (success)
                {
                    return RedirectToAction("QuanLyVoucher");
                }
                else
                {
                    ViewBag.Message = data.message.ToString();
                    return RedirectToAction("QuanLyVoucher");
                }
            }
        }

        public async Task<ActionResult> QuanLyTonKho(string searchString, int page = 1, int pageSize = 10)
        {
         //   if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var postData = new
                {
                    SearchString = searchString,
                    Page = page,
                    PageSize = pageSize
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_products", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    var pagedProducts = data.products.ToObject<List<SanPham>>();
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)data.totalPages;
                    ViewBag.SearchString = searchString;

                    return View(pagedProducts);
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }

        public async Task<ActionResult> QuanLyPhieuNhapKho(int? searchString, int page = 1, int pageSize = 10)
        {
            // if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var postData = new
                {
                    SearchString = searchString,
                    Page = page,
                    PageSize = pageSize
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_phieunhapkho", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    var pagedPhieuNhap = data.phieuNhaps.ToObject<List<PhieuNhapKho>>();
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)data.totalPages;
                    ViewBag.SearchString = searchString;

                    return View(pagedPhieuNhap);
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }

        public async Task<ActionResult> ChiTietPhieuNhapKho(int id)
        {
            // if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var postData = new { MaPhieuNhap = id };
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_chitietphieunhap", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    var phieuNhap = data.phieuNhap.ToObject<PhieuNhapKho>();
                    var chiTietDynamic = data.chiTiet;
                    var chiTiet = new List<ChiTietPhieuNhapViewModel>();
                    foreach (var item in chiTietDynamic)
                    {
                        var serials = new List<string>();
                        if (item.SerialNumbers != null)
                        {
                            foreach (var serial in item.SerialNumbers)
                            {
                                serials.Add((string)serial);
                            }
                        }

                        chiTiet.Add(new ChiTietPhieuNhapViewModel
                        {
                            MaChiTiet = (int)item.MaChiTiet,
                            MaPhieuNhap = (int)item.MaPhieuNhap,
                            MaSanPham = (int)item.MaSanPham,
                            TenSanPham = (string)item.TenSanPham,
                            SoLuong = (int)item.SoLuong,
                            GiaNhap = (decimal)item.GiaNhap,
                            TongTien = (decimal)item.TongTien,
                            SerialNumbers = serials
                        });
                    }
                    ViewBag.ChiTietPhieuNhapKho = chiTiet;

                    return View(phieuNhap);
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }

        public async Task<ActionResult> ThemPhieuNhapKho()
        {
            // if (!check()) { return RedirectToAction("Loi404", "Admin"); }
            await LoadPhieuNhapDropdowns();
            return View();
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemPhieuNhapKho(PhieuNhapKho phieuNhapKho, List<ChiTietPhieuNhapKho> ChiTietPhieuNhaps)
        {
            if (!phieuNhapKho.MaNhaCungCap.HasValue)
            {
                ModelState.AddModelError("MaNhaCungCap", "Vui lòng chọn nhà cung cấp.");
            }

            if (ChiTietPhieuNhaps == null || !ChiTietPhieuNhaps.Any())
            {
                ModelState.AddModelError("", "Cần nhập ít nhất một sản phẩm.");
            }

            if (!ModelState.IsValid)
            {
                await LoadPhieuNhapDropdowns();
                return View(phieuNhapKho);
            }

            var serialSeparators = new[] { '\n', '\r', ',', ';' };
            var chiTietPayload = ChiTietPhieuNhaps.Select(ct => new
            {
                MaSanPham = ct.MaSanPham,
                SoLuong = ct.SoLuong,
                GiaNhap = ct.GiaNhap,
                SerialNumbers = string.IsNullOrWhiteSpace(ct.SerialNumbers)
                    ? new List<string>()
                    : ct.SerialNumbers
                        .Split(serialSeparators, StringSplitOptions.RemoveEmptyEntries)
                        .Select(s => s.Trim())
                        .Where(s => !string.IsNullOrWhiteSpace(s))
                        .ToList()
            }).ToList();

            var postData = new
            {
                phieuNhapKho = new
                {
                    GhiChu = phieuNhapKho.GhiChu,
                    MaNhaCungCap = phieuNhapKho.MaNhaCungCap
                },
                ChiTietPhieuNhaps = chiTietPayload
            };

            using (var client = new HttpClient())
            {
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/create_phieunhap", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    return RedirectToAction("QuanLyPhieuNhapKho");
                }
                else
                {
                    ViewBag.ErrorMessage = data.message;
                    await LoadPhieuNhapDropdowns();
                    return View(phieuNhapKho);
                }
            }
        }

        public async Task<ActionResult> QuanLyKhoHangLoi(string searchString, int page = 1, int pageSize = 10)
        {
            // if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var postData = new
                {
                    SearchString = searchString,
                    Page = page,
                    PageSize = pageSize
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_kho_hang_loi", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    var khoHangLoi = data.khoHangLoi.ToObject<List<dynamic>>();
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = (int)data.totalPages;
                    ViewBag.SearchString = searchString;
                    ViewBag.TotalCount = (int)data.totalCount;

                    return View(khoHangLoi);
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }

        public async Task<ActionResult> ThemKhoHangLoi()
        {
            // if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var response = await client.GetAsync("http://127.0.0.1:5000/api/get_sanpham");
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);
                if ((bool)data.success)
                {
                    ViewBag.SanPhams = data.sanPhams.ToObject<List<SanPham>>();
                }
            }

            return View();
        }

        private async Task LoadPhieuNhapDropdowns()
        {
            using (var client = new HttpClient())
            {
                try
                {
                    var spResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_sanpham");
                    if (spResponse.IsSuccessStatusCode)
                    {
                        var spResult = await spResponse.Content.ReadAsStringAsync();
                        dynamic spData = JsonConvert.DeserializeObject(spResult);
                        ViewBag.SanPhams = spData.success == true
                            ? spData.sanPhams.ToObject<List<SanPham>>()
                            : new List<SanPham>();
                    }
                    else
                    {
                        ViewBag.SanPhams = new List<SanPham>();
                    }

                    var supplierResponse = await client.GetAsync("http://127.0.0.1:5000/api/suppliers?pageSize=200");
                    if (supplierResponse.IsSuccessStatusCode)
                    {
                        var supplierResult = await supplierResponse.Content.ReadAsStringAsync();
                        dynamic supplierData = JsonConvert.DeserializeObject(supplierResult);
                        ViewBag.NhaCungCaps = supplierData.success == true
                            ? supplierData.suppliers.ToObject<List<NhaCungCap>>()
                            : new List<NhaCungCap>();
                    }
                    else
                    {
                        ViewBag.NhaCungCaps = new List<NhaCungCap>();
                    }
                }
                catch
                {
                    ViewBag.SanPhams = new List<SanPham>();
                    ViewBag.NhaCungCaps = new List<NhaCungCap>();
                }
            }
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemKhoHangLoi(KhoHangLoi khoHangLoi)
        {
            if (!ModelState.IsValid)
            {
                // Nếu có lỗi validation, load lại danh sách sản phẩm
                using (var client = new HttpClient())
                {
                    var response = await client.GetAsync("http://127.0.0.1:5000/api/get_sanpham");
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);
                    if ((bool)data.success)
                    {
                        ViewBag.SanPhams = data.sanPhams.ToObject<List<SanPham>>();
                    }
                }
                return View(khoHangLoi);
            }

            var postData = new
            {
                MaSanPham = khoHangLoi.MaSanPham,
                SoLuong = khoHangLoi.SoLuong,
                LyDo = khoHangLoi.LyDo
            };

            using (var client = new HttpClient())
            {
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/them_kho_hang_loi", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    TempData["SuccessMessage"] = "Thêm sản phẩm vào kho hàng lỗi thành công!";
                    return RedirectToAction("QuanLyKhoHangLoi");
                }
                else
                {
                    ViewBag.ErrorMessage = data.message;

                    // Load lại danh sách sản phẩm
                    var productResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_sanpham");
                    var productResult = await productResponse.Content.ReadAsStringAsync();
                    dynamic productData = JsonConvert.DeserializeObject(productResult);
                    if ((bool)productData.success)
                    {
                        ViewBag.SanPhams = productData.sanPhams.ToObject<List<SanPham>>();
                    }

                    return View(khoHangLoi);
                }
            }
        }

      

        [HttpPost]
        public async Task<JsonResult> XoaKhoHangLoi(int maKhoLoi)
        {
            var postData = new { MaKhoLoi = maKhoLoi };

            using (var client = new HttpClient())
            {
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/xoa_kho_hang_loi", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                return Json(new { success = data.success, message = data.message });
            }
        }

        public async Task<ActionResult> ThongKeKhoHangLoi()
        {
            // if (!check()) { return RedirectToAction("Loi404", "Admin"); }

            using (var client = new HttpClient())
            {
                var response = await client.GetAsync("http://127.0.0.1:5000/api/thong_ke_kho_hang_loi");
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                {
                    ViewBag.TongSanPham = (int)data.tongSanPham;
                    ViewBag.TongSoLuong = (int)data.tongSoLuong;
                    var thongKe = data.thongKeSanPham.ToObject<List<dynamic>>();

                    return View(thongKe);
                }
                else
                {
                    return HttpNotFound();
                }
            }
        }
        public async Task<ActionResult> QuanLyDonHang(int page = 1, int pageSize = 5, string searchTerm = null, string status = null)
        {
          //  if (!check()) return RedirectToAction("Loi404", "Admin");QuanLyTonKho

            using (var client = new HttpClient())
            {
            //    var quyen = Convert.ToInt32(Session["quyen"]);

                var postData = new
                {
                    page,
                    pageSize,
                    searchTerm,
                    status
                    //       quyen
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_orders", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                ViewBag.CurrentPage = page;
                ViewBag.TotalPages = (int)Math.Ceiling((double)data.total / pageSize);
                ViewBag.SearchTerm = searchTerm;
                 ViewBag.Status = status;
                return View(data.orders);
            }
        }

        public async Task<ActionResult> DuyetDonHang(int id)
        {
            using (var client = new HttpClient())
            {
                var postData = new
                {
                    MaDonHang = id,
                    TrangThai = "Đã Duyệt"
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                // Sử dụng PutAsync thay vì PostAsync
                var response = await client.PutAsync("http://127.0.0.1:5000/api/update_order_status", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                    return RedirectToAction("QuanLyDonHang");
                else
                    return HttpNotFound();
            }

        }

        public async Task<ActionResult> HuyDonHang(int id)
        {
            using (var client = new HttpClient())
            {
                var postData = new
                {
                    order_id = id
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/cancel_order", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                    return RedirectToAction("QuanLyDonHang");
                else
                    return HttpNotFound();
            }
        }

        public async Task<ActionResult> ChiTietDonHang(int id)
        {
          //  if (!check()) return RedirectToAction("Loi404", "Admin");

            using (var client = new HttpClient())
            {
                var postData = new { orderId = id };
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_order_detail", content);
                var result = await response.Content.ReadAsStringAsync();

                dynamic responseData = JsonConvert.DeserializeObject(result);

                bool success = Convert.ToBoolean(responseData.success);
                if (!success)
                {
                    return HttpNotFound();
                }

                ViewBag.Order = responseData.order;
                ViewBag.Details = responseData.details;
                ViewBag.GiamGia = responseData.giamGia;
                ViewBag.Code = responseData.code;

                return View();
            }
        }

        public async Task<ActionResult> InHoaDon(int id)
        {
            using (var client = new HttpClient())
            {
                var postData = new { orderId = id };
                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_order_detail", content);

                if (!response.IsSuccessStatusCode)
                {
                    TempData["Error"] = "Không thể lấy dữ liệu đơn hàng.";
                    return RedirectToAction("QuanLyDonHang");
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic responseData = JsonConvert.DeserializeObject(result);

                bool success = Convert.ToBoolean(responseData.success);
                if (!success)
                {
                    TempData["Error"] = responseData.message ?? "Không tìm thấy đơn hàng.";
                    return RedirectToAction("QuanLyDonHang");
                }

                ViewBag.Order = responseData.order;
                ViewBag.Details = responseData.details;
                ViewBag.GiamGia = responseData.giamGia;
                ViewBag.Code = responseData.code;

                var username = Session["Admin"] as string;
                string staffName = username ?? "Admin";
                string staffPhone = "";
                string staffEmail = "";

                if (!string.IsNullOrEmpty(username))
                {
                    var staffResponse = await client.GetAsync($"http://127.0.0.1:5000/api/check_username?username={username}");
                    if (staffResponse.IsSuccessStatusCode)
                    {
                        var staffJson = await staffResponse.Content.ReadAsStringAsync();
                        dynamic staffData = JsonConvert.DeserializeObject(staffJson);
                        if (staffData != null && staffData.error == null)
                        {
                            if (staffData.HoTen != null)
                                staffName = staffData.HoTen;
                            if (staffData.SoDienThoai != null)
                                staffPhone = staffData.SoDienThoai;
                            if (staffData.Email != null)
                                staffEmail = staffData.Email;
                        }
                    }
                }

                ViewBag.StaffName = staffName;
                ViewBag.StaffPhone = string.IsNullOrWhiteSpace(staffPhone) ? "1900 999 888" : staffPhone;
                ViewBag.StaffEmail = string.IsNullOrWhiteSpace(staffEmail) ? "support@laptopstore.vn" : staffEmail;
                ViewBag.PrintedAt = DateTime.Now;

                return View();
            }
        }


        // Xem danh sách nhân viên
        public async Task<ActionResult> QuanLyNhanVien(int page = 1, int pageSize = 5, string searchTerm = null)
        {
            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/get_all_nhanvien?page={page}&pageSize={pageSize}&search={searchTerm}";
                var response = await client.GetAsync(url);

                if (!response.IsSuccessStatusCode)
                {
                    ViewBag.Message = "Có lỗi khi kết nối đến API.";
                    return View();
                }

                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if (data != null && data.success != null && data.success == true)
                {
                    ViewBag.CurrentPage = page;
                    ViewBag.TotalPages = data.total != null ? (int)Math.Ceiling((double)data.total / pageSize) : 0;
                    ViewBag.SearchTerm = searchTerm; // Giữ từ khóa tìm kiếm

                    if (data.nhanviens != null)
                    {
                        var nhanViens = data.nhanviens.ToObject<List<TaiKhoan>>(); // Chuyển dữ liệu từ JSON thành list nhanvien
                        return View(nhanViens);
                    }
                    else
                    {
                        ViewBag.Message = "Không có nhân viên nào.";
                        return View();
                    }
                }
                else
                {
                    ViewBag.Message = data != null ? data.message : "Không thể lấy dữ liệu từ API.";
                    return View();
                }
            }
        }


        // Thêm nhân viên
        public ActionResult ThemNhanVien()
        {
          //  if (!check()) { return RedirectToAction("Loi404", "Admin"); }
            return View();
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> ThemNhanVien(TaiKhoan nhanVien)
        {
            if (ModelState.IsValid)
            {
                // Kiểm tra các trường bắt buộc
                if (string.IsNullOrEmpty(nhanVien.Username) ||
                    string.IsNullOrEmpty(nhanVien.Password) ||
                    string.IsNullOrEmpty(nhanVien.Email) ||
                    string.IsNullOrEmpty(nhanVien.SoDienThoai))
                {
                    ModelState.AddModelError("", "Vui lòng điền đầy đủ thông tin.");
                    return View(nhanVien);
                }

                // Gửi nhân viên mới qua API
                using (var client = new HttpClient())
                {
                    var data = new
                    {
                        Username = nhanVien.Username,
                        Password = nhanVien.Password,
                        HoTen = nhanVien.HoTen,
                        DiaChi = nhanVien.DiaChi,
                        Email = nhanVien.Email,
                        SoDienThoai = nhanVien.SoDienThoai,
                        MaQuyen = nhanVien.MaQuyen,
                        NgayTao = DateTime.Now,
                        TrangThai = true
                    };

                    var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                    var response = await client.PostAsync("http://127.0.0.1:5000/api/nhanvien", content);
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic responseData = JsonConvert.DeserializeObject(result);

                    bool success = Convert.ToBoolean(responseData.success);

                    if (success)
                    {
                        return RedirectToAction("QuanLyNhanVien");
                    }
                    else
                    {
                        
                        ModelState.AddModelError("", responseData.message.ToString());
                        return View(nhanVien);
                    }
                }
            }

            return View(nhanVien);
        }



        public async Task<ActionResult> KhoaTaiKhoan(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.PutAsync("http://127.0.0.1:5000/api/khoa-tai-khoan/" + id, null);
                var result = await response.Content.ReadAsStringAsync();
                dynamic json = JsonConvert.DeserializeObject(result);
                TempData["Message"] = json.message;
            }
            return RedirectToAction("QuanLyNhanVien");
        }

        public async Task<ActionResult> MoKhoaTaiKhoan(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.PutAsync("http://127.0.0.1:5000/api/mo-khoa-tai-khoan/" + id, null);
                var result = await response.Content.ReadAsStringAsync();
                dynamic json = JsonConvert.DeserializeObject(result);
                TempData["Message"] = json.message;
            }
            return RedirectToAction("QuanLyNhanVien");
        }

        // GET: Đổi mật khẩu
        public ActionResult DoiMatKhau()
        {
          //  if (!check()) { return RedirectToAction("Loi404", "Admin"); }
            return View();
        }
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<ActionResult> DoiMatKhau(string matKhauCu, string matKhauMoi, string xacNhanMatKhau)
        {
            string taiKhoan = (string)Session["Admin"]; // Lấy username từ session

            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000/"); // Thay bằng địa chỉ thực của API

                var content = new StringContent(JsonConvert.SerializeObject(new
                {
                    username = taiKhoan,
                    matkhaucu = matKhauCu,
                    matkhaumoi = matKhauMoi,
                    xacnhanmk = xacNhanMatKhau
                }), Encoding.UTF8, "application/json");

                var response = await client.PostAsync("api/doi-mat-khau", content);
                var result = await response.Content.ReadAsStringAsync();

                dynamic json = JsonConvert.DeserializeObject(result);
                ViewBag.Message = json.message;

                if ((bool)json.success)
                {
                    return View(); // hoặc RedirectToAction("SuccessPage");
                }

                return View(); // Giữ nguyên nếu lỗi
            }
        }

        // 1. Cập nhật trạng thái đơn hàng theo luồng mới
        public async Task<ActionResult> CapNhatTrangThaiDonHang(int id, string trangThai)
        {
            using (var client = new HttpClient())
            {
                var postData = new
                {
                    MaDonHang = id,
                    TrangThai = trangThai
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PutAsync("http://127.0.0.1:5000/api/update_order_status_new", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                if ((bool)data.success)
                    return Json(new { success = true, message = "Cập nhật thành công" });
                else
                    return Json(new { success = false, message = data.message });
            }
        }

        // 2. Quản lý đơn đổi trả
        public async Task<ActionResult> QuanLyDoiTra(int page = 1, int pageSize = 10, string status = null)
        {
            using (var client = new HttpClient())
            {
                var url = $"http://127.0.0.1:5000/api/get_return_requests?page={page}&pageSize={pageSize}&status={status}";
                var response = await client.GetAsync(url);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);

                    if (data.success == true)
                    {
                        ViewBag.Returns = data.returns;
                        ViewBag.CurrentPage = page;
                        ViewBag.Status = status;
                        return View();
                    }
                }

                ViewBag.Message = "Không thể lấy dữ liệu đổi trả.";
                return View();
            }
        }
        // Thêm vào Controller
        public async Task<ActionResult> ChiTietDoiTra(int id)
        {
            using (var client = new HttpClient())
            {
                var response = await client.GetAsync($"http://127.0.0.1:5000/api/get_return_detail/{id}");
                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);
                    if (data.success == true)
                    {
                        return PartialView("_ReturnDetailPartial", data.returnDetail);
                    }
                }
                return Json(new { success = false, message = "Không thể lấy thông tin chi tiết" });
            }
        }
        // 3. Cập nhật trạng thái đổi trả
        [HttpPost]
        public async Task<JsonResult> CapNhatTrangThaiDoiTra(int maDoiTra, string trangThai, string ghiChu = "")
        {
            using (var client = new HttpClient())
            {
                var data = new
                {
                    maDoiTra = maDoiTra,   
                    trangThai = trangThai,  
                    ghiChu = ghiChu
                };
                var content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json");
                var response = await client.PutAsync("http://127.0.0.1:5000/api/update_return_status", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic responseData = JsonConvert.DeserializeObject(result);
                return Json(new { success = responseData.success, message = responseData.message });
            }
        }

        // 4. Quản lý đánh giá sản phẩm
        public async Task<ActionResult> QuanLyDanhGia(int page = 1, int pageSize = 10, int? productId = null)
        {
            using (var client = new HttpClient())
            {
                string url = $"http://127.0.0.1:5000/api/get_all_reviews?page={page}&pageSize={pageSize}";
                if (productId.HasValue)
                {
                    url += $"&productId={productId}";
                }

                var response = await client.GetAsync(url);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);

                    ViewBag.Reviews = data.reviews;
                    ViewBag.CurrentPage = page;
                    ViewBag.ProductId = productId;
                    return View();
                }

                ViewBag.Message = "Không thể lấy dữ liệu đánh giá.";
                return View();
            }
        }

        // 5. Xóa đánh giá không phù hợp
        [HttpPost]
        public async Task<JsonResult> XoaDanhGia(int maDanhGia)
        {
            using (var client = new HttpClient())
            {
                var response = await client.DeleteAsync($"http://127.0.0.1:5000/api/delete_review/{maDanhGia}");
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                return Json(new { success = data.success, message = data.message });
            }
        }

        // 6. Cập nhật QuanLyDonHang với trạng thái mới
        public async Task<ActionResult> QuanLyDonHangEnhanced(int page = 1, int pageSize = 5, string searchTerm = null, string status = null)
        {
            using (var client = new HttpClient())
            {
                var postData = new
                {
                    page,
                    pageSize,
                    searchTerm,
                    status
                };

                var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");
                var response = await client.PostAsync("http://127.0.0.1:5000/api/get_orders", content);
                var result = await response.Content.ReadAsStringAsync();
                dynamic data = JsonConvert.DeserializeObject(result);

                ViewBag.CurrentPage = page;
                ViewBag.TotalPages = (int)Math.Ceiling((double)data.total / pageSize);
                ViewBag.SearchTerm = searchTerm;
                ViewBag.Status = status;

                // Danh sách trạng thái mới
                ViewBag.StatusList = new List<string>
        {
            "Đặt hàng thành công",
            "Đang chuẩn bị hàng",
            "Đã giao cho đơn vị vận chuyển",
            "Đơn hàng sẽ sớm được giao đến bạn",
            "Đã giao",
            "Đã hủy"
        };

                return View(data.orders);
            }
        }

        // 7. Thống kê đánh giá
        public async Task<ActionResult> ThongKeDanhGia()
        {
            using (var client = new HttpClient())
            {
                var response = await client.GetAsync("http://127.0.0.1:5000/api/review_statistics");

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);

                    ViewBag.TotalReviews = data.totalReviews;
                    ViewBag.AverageRating = data.averageRating;
                    ViewBag.RatingDistribution = data.ratingDistribution;
                    ViewBag.TopRatedProducts = data.topRatedProducts;

                    return View();
                }

                return View();
            }
        }

    }
}