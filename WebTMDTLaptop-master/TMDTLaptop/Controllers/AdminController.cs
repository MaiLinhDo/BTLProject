using System;
using System.Collections.Generic;
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
namespace TMDTLaptop.Controllers
{
    public class AdminController : Controller
    {


        public bool check()
        {
            if (Session["Admin"] == null) { return false; }
            return true;
        }
        // GET: Admin
        public async Task<ActionResult> Index()
        {


            using (var client = new HttpClient())
            {
                var now = DateTime.Now;
                var firstDayOfMonth = new DateTime(now.Year, now.Month, 1);
                var lastDayOfMonth = firstDayOfMonth.AddMonths(1).AddDays(-1);

                var payload = new
                {
                    startDate = firstDayOfMonth.ToString("yyyy-MM-dd"),
                    endDate = lastDayOfMonth.ToString("yyyy-MM-dd")
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
            }

            return View();
        }

        // GET: QuanLySanPham
        public async Task<ActionResult> QuanLySanPham(int page = 1, int pageSize = 5, string searchTerm = "")
        {
            //   if (!check()) return RedirectToAction("Loi404", "Admin");

            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000"); // Đổi thành base URL Flask của bạn

                var payload = new
                {
                    SearchTerm = searchTerm ?? "",
                    Page = page,
                    PageSize = pageSize
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

                if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode)
                {
                    var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                    var hangData = await hangResponse.Content.ReadAsStringAsync();

                    // Deserialise dữ liệu trả về thành danh sách
                    ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                    ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                }
                else
                {
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

                            if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode)
                            {
                                var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                                var hangData = await hangResponse.Content.ReadAsStringAsync();

                                // Deserialise dữ liệu trả về thành danh sách
                                ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                                ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                            }
                            ModelState.AddModelError("", "Lỗi khi tạo sản phẩm.");
                        }
                    }
                    else
                    {
                        var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                        var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");

                        if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode)
                        {
                            var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                            var hangData = await hangResponse.Content.ReadAsStringAsync();

                            // Deserialise dữ liệu trả về thành danh sách
                            ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                            ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                        }
                        ModelState.AddModelError("", "Lỗi khi gọi API.");
                    }
                }
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

                    if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode)
                    {
                        var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                        var hangData = await hangResponse.Content.ReadAsStringAsync();
                        ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                        ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
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
                using (var client = new HttpClient())
                using (var formData = new MultipartFormDataContent())
                {
                    // Thêm thông tin sản phẩm
                    formData.Add(new StringContent(model.TenSanPham), "TenSanPham");
                    formData.Add(new StringContent(model.MoTa ?? ""), "MoTa");
                    formData.Add(new StringContent(model.Gia.ToString()), "Gia");
                    formData.Add(new StringContent(model.MaDanhMuc.ToString()), "MaDanhMuc");
                    formData.Add(new StringContent(model.MaHang.ToString()), "MaHang");

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

                            if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode)
                            {
                                var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                                var hangData = await hangResponse.Content.ReadAsStringAsync();
                                ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                                ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                            }
                            ModelState.AddModelError("", "Lỗi khi cập nhật sản phẩm.");
                            return View(model);

                        }
                    }
                    else
                    {
                        var danhMucResponse = await client.GetAsync("http://127.0.0.1:5000/api/categories");
                        var hangResponse = await client.GetAsync("http://127.0.0.1:5000/api/get_hang");

                        if (danhMucResponse.IsSuccessStatusCode && hangResponse.IsSuccessStatusCode)
                        {
                            var danhMucData = await danhMucResponse.Content.ReadAsStringAsync();
                            var hangData = await hangResponse.Content.ReadAsStringAsync();
                            ViewBag.DanhMuc = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(danhMucData);
                            ViewBag.Hang = JsonConvert.DeserializeObject<List<HangSanPham>>(hangData);
                        }
                        ModelState.AddModelError("", "Lỗi khi gọi API.");
                        return View(model);

                    }
                }
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

    }
}