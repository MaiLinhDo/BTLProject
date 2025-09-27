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
     
       
        // GET: Admin
        public async Task<ActionResult> Index()
        {
         
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




    }
}