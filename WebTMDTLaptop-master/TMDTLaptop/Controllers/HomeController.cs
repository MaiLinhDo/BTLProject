using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Mail;
using System.Net;
using System.Web;
using System.Web.Mvc;
using TMDTLaptop.Models;
using TMDTLaptop.Models.Class;
using System.Web.Services.Description;
using System.Data.Entity;
using Microsoft.Owin.Security;
using Microsoft.Owin.Security.Google;
using System.Security.Claims;
using Newtonsoft.Json.Linq;
using System.Net.Http;
using System.Diagnostics;
using Newtonsoft.Json;
using System.Threading.Tasks;
using System.Net.Http.Headers;
using System.Text;
using System.Net.Sockets;
using System.IO;
namespace TMDTLaptop.Controllers
{
    public class HomeController : Controller
    {
        
      
        public async Task<ActionResult> Index()
        {
            List<SanPham> products = new List<SanPham>();
            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000/");

               
                // Gọi API Product
                var productRes = await client.GetAsync("api/products");
                if (productRes.IsSuccessStatusCode)
                {
                    var data = await productRes.Content.ReadAsStringAsync();
                    products = JsonConvert.DeserializeObject<List<SanPham>>(data);
                }
            }
            return View(products);
        }

        // DatHangThanhCong: Xử lý đặt hàng
        public ActionResult DatHang(string paymentMethod)
        {
            var username = Session["Username"] as string;
            if (string.IsNullOrEmpty(username)) return RedirectToAction("DangNhap", "Home");


            HttpClient client = new HttpClient(); // gửi các yc http(get, post, ...)


            string apiUrl = $"http://127.0.0.1:5000/api/check_username?username={username}";

            HttpResponseMessage response = client.GetAsync(apiUrl).Result; // gửi yc get đến url và nhận phản hồi dưới dạng HttpResponseMessage

            if (response.IsSuccessStatusCode)
            {
                string responseBody = response.Content.ReadAsStringAsync().Result; //Đọc nội dung của phản hồi HTTP (thường là JSON) dưới dạng chuỗi (string).

                // Dùng dynamic để không cần tạo class
                dynamic user = JsonConvert.DeserializeObject(responseBody); //Dùng thư viện Newtonsoft.Json để giải mã JSON từ chuỗi responseBody thành một đối tượng dynamic.


                if (user == null) return HttpNotFound("Người dùng không tìm thấy.");
                if (user.TrangThai == false) return HttpNotFound("Tài khoản của bạn đã bị khóa.");
                if (user.DiaChi == null || user.SoDienThoai == null || user.DiaChi == "" || user.SoDienThoai == "") return RedirectToAction("HoSo", "Home", new { mess = "Bạn cần nhập đầy đủ thông tin" });

                // Tiếp tục xử lý như cũ
                var cart = Session["Cart"] as List<ModelGioHang>;
                if (cart == null || !cart.Any()) return RedirectToAction("GioHang", "Home");

                decimal tongTien = (decimal)cart.Sum(item => item.SoLuong * item.Gia);
                Debug.WriteLine($"Tổng tiền trước giảm giá: {tongTien}"); // Debug tổng tiền
                var voucher = Session["CouponDH"] as Voucher;
                if (voucher != null)
                {
                    string apivc = $"http://127.0.0.1:5000/api/voucher?code={voucher.Code}";
                    HttpResponseMessage responsevc = client.GetAsync(apivc).Result;
                    Debug.WriteLine(responsevc);
                    if (responsevc.IsSuccessStatusCode)
                    {
                        string updatevc = "http://127.0.0.1:5000/api/voucher/update";
                        var json = $"{{\"code\":\"{voucher.Code}\"}}";
                        var contentvc = new StringContent(json, Encoding.UTF8, "application/json");
                        HttpResponseMessage updateResponse = client.PostAsync(updatevc, contentvc).Result;

                        if (updateResponse.IsSuccessStatusCode)
                        {
                            tongTien -= (decimal)(tongTien * voucher.GiamGia / 100);

                        }
                    }
                    else
                    {
                        return HttpNotFound("Voucher không tìm thấy.");
                    }

                }

                if (paymentMethod == "VNPAY")
                {
                    Session["PendingOrder"] = new DonHang
                    {
                        MaTaiKhoan = user.MaTaiKhoan,
                        NgayDatHang = DateTime.Now,
                        TongTien = tongTien,
                        DiaChiGiaoHang = user.DiaChi,
                        SoDienThoai = user.SoDienThoai,
                        TrangThai = "Chờ thanh toán",
                        MaVoucher = voucher?.MaVoucher
                    };
                    return RedirectToAction("ThanhToanQuaThe", "ThanhToan", new { amount = tongTien });


                }

                // Chuẩn bị dữ liệu gửi sang Flask
                var payload = new
                {
                    MaTaiKhoan = user.MaTaiKhoan,
                    NgayDatHang = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    TongTien = tongTien,
                    DiaChiGiaoHang = user.DiaChi,
                    SoDienThoai = user.SoDienThoai,
                    TrangThai = "Đặt hàng thành công",
                    MaVoucher = voucher?.MaVoucher,
                    ChiTietDonHang = cart.Select(item => new
                    {
                        MaSanPham = item.MaSanPham,
                        SoLuong = item.SoLuong,
                        Gia = item.Gia
                    }).ToList()
                };

                // Gửi dữ liệu POST sang Flask API
                var content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
                response = client.PostAsync("http://127.0.0.1:5000/api/them_donhang", content).Result;

                if (response.IsSuccessStatusCode)
                {
                    responseBody = response.Content.ReadAsStringAsync().Result;
                    dynamic result = JsonConvert.DeserializeObject(responseBody);
                    DonHang donhang = result["order"].ToObject<DonHang>();
                    Session.Remove("Cart");
                    Session.Remove("CouponDH");
                    return RedirectToAction("DatHangThanhCong", donhang);

                }
                else
                {
                    // Thông báo lỗi
                    string error = response.Content.ReadAsStringAsync().Result;
                    throw new Exception("Không thể tạo đơn hàng: " + error);
                }

            }

            return View();
        }

        public async Task<ActionResult> DatHangThanhCong(DonHang donHang)
        {
            string apiUrl = "http://127.0.0.1:5000/api/get_order_detail";

            using (var client = new HttpClient())
            {
                var requestData = new
                {
                    orderId = donHang.MaDonHang
                };

                var content = new StringContent(
                    Newtonsoft.Json.JsonConvert.SerializeObject(requestData),
                    Encoding.UTF8,
                    "application/json"
                );

                var response = await client.PostAsync(apiUrl, content);

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    dynamic result = JsonConvert.DeserializeObject(json);

                    ViewBag.OrderId = result.order.MaDonHang;
                    ViewBag.OrderDetails = new List<string>();

                    foreach (var item in result.details)
                    {
                        string line = $"{item.TenSanPham}|{item.Gia}|{item.SoLuong}|{item.Gia * item.SoLuong}";
                        ViewBag.OrderDetails.Add(line);
                    }

                    ViewBag.TotalAmount = result.order.TongTien;
                    ViewBag.MaVoucher = result.code;
                    ViewBag.phantram = result.giamGia ?? 0;


                    return View(donHang); // donHang chỉ để truyền lại thôi
                }
                else
                {
                    ViewBag.Error = "Không lấy được dữ liệu đơn hàng.";
                    return View("Error");
                }
            }
        }

        public ActionResult GetDanhMuc()
        {
            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000/");
                client.DefaultRequestHeaders.Accept.Clear();
                client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

                try
                {
                    var response = client.GetAsync("api/categories").Result;

                    if (response.IsSuccessStatusCode)
                    {
                        var data = response.Content.ReadAsStringAsync().Result;

                        // Giải mã JSON thành List<DanhMucSanPham>
                        var danhMucList = JsonConvert.DeserializeObject<List<DanhMucSanPham>>(data);

                        return PartialView("_DanhMucPartial", danhMucList);
                    }
                    else
                    {
                        return PartialView("_DanhMucPartial", new List<DanhMucSanPham>());
                    }
                }
                catch (Exception ex)
                {

                    return PartialView("_DanhMucPartial", new List<DanhMucSanPham>());
                }
            }
        }

        public ActionResult About()
        {
            ViewBag.Message = "Your application description page.";

            return View();
        }

        public async Task<ActionResult> CuaHang(int id, string search = "", decimal? minPrice = null, decimal? maxPrice = null, int? brand = null, int page = 1, int pageSize = 8)
        {
            string apiUrl = "http://127.0.0.1:5000/api/products_user";
            var client = new HttpClient();
            var queryString = $"?id={id}&search={search}&minPrice={minPrice}&maxPrice={maxPrice}&brand={brand}&page={page}&pageSize={pageSize}";

            try
            {
                // Gửi yêu cầu GET đến API sản phẩm
                var response = await client.GetStringAsync(apiUrl + queryString);
                Debug.WriteLine(response);
                var jsonResponse = JObject.Parse(response);

                if (jsonResponse["products"] == null || !jsonResponse["products"].Any())
                {
                    return RedirectToAction("Error", "Home");
                }

                var productsToDisplay = jsonResponse["products"].ToObject<List<SanPham>>();

                // Gán các ViewBag cho phân trang và thông tin tìm kiếm
                ViewBag.DanhMuc = id;
                ViewBag.TotalPages = jsonResponse["totalPages"].Value<int>();
                ViewBag.CurrentPage = page;
                ViewBag.TotalProducts = jsonResponse["totalProducts"].Value<int>();
                ViewBag.Search = search;
                ViewBag.MinPrice = minPrice;
                ViewBag.MaxPrice = maxPrice;
                ViewBag.Brand = brand?.ToString();

                // Gọi API lấy danh mục sản phẩm (Brands)
                var categoriesResponse = await client.GetStringAsync("http://127.0.0.1:5000/api/get_categories");
                var categoriesJsonResponse = JObject.Parse(categoriesResponse);

                if (categoriesJsonResponse["categories"] == null || !categoriesJsonResponse["categories"].Any())
                {
                    return RedirectToAction("Error", "Home");
                }

                var categories = categoriesJsonResponse["categories"].ToObject<List<HangSanPham>>();
                ViewBag.Brands = categories;

                return View(productsToDisplay);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Lỗi khi gọi API: {ex.Message}");
                return RedirectToAction("Error", "Home");
            }
        }
        public async Task<ActionResult> ChiTietSanPham(int id, int reviewPage = 1)
        {
            var httpClient = new HttpClient();
            var jsonData = new { productId = id };

            var response = httpClient.PostAsJsonAsync("http://127.0.0.1:5000/api/get_detail_product", jsonData).Result;

            if (response.IsSuccessStatusCode)
            {
                var result = response.Content.ReadAsAsync<dynamic>().Result;
                var sanPham = JsonConvert.DeserializeObject<TMDTLaptop.Models.Class.SanPham>(result.product.ToString());
                var sanPhamCungGia = result.similarProducts;

                // Lấy đánh giá sản phẩm
                var reviewResponse = await httpClient.GetAsync($"http://127.0.0.1:5000/api/get_reviews/{id}?page={reviewPage}");
                if (reviewResponse.IsSuccessStatusCode)
                {
                    var reviewResult = await reviewResponse.Content.ReadAsStringAsync();
                    dynamic reviewData = JsonConvert.DeserializeObject(reviewResult);

                    ViewBag.Reviews = reviewData.reviews;
                    ViewBag.AverageRating = (double)reviewData.averageRating;
                    ViewBag.TotalReviews = (int)reviewData.totalReviews;
                    ViewBag.ReviewCurrentPage = reviewPage;
                    ViewBag.ReviewTotalPages = reviewData.totalPages;

                    // Tính phân bố rating cho biểu đồ
                    if (reviewData.ratingDistribution != null)
                    {
                        ViewBag.RatingDistribution = reviewData.ratingDistribution;
                    }
                }

                ViewBag.SanPhamCungGia = sanPhamCungGia;
                return View(sanPham);
            }

            return HttpNotFound();
        }
        public async Task<ActionResult> ChiTietSanPhamEnhanced(int id)
        {
            
            var httpClient = new HttpClient();
            var jsonData = new { productId = id };

            var response = httpClient.PostAsJsonAsync("http://127.0.0.1:5000/api/get_detail_product", jsonData).Result;

            if (response.IsSuccessStatusCode)
            {
                var result = response.Content.ReadAsAsync<dynamic>().Result;
                var sanPham = JsonConvert.DeserializeObject<TMDTLaptop.Models.Class.SanPham>(result.product.ToString());
                var sanPhamCungGia = result.similarProducts;

               
                ViewBag.SanPhamCungGia = sanPhamCungGia;
                return View(sanPham);
            }

            return HttpNotFound();
        }



        public async Task<ActionResult> GioHang()
        {
            string username = Session["Username"] as string;
            List<ModelGioHang> cart = Session["Cart"] as List<ModelGioHang> ?? new List<ModelGioHang>();
            List<Voucher> vouchers = new List<Voucher>(); // Thêm dòng này

            // Nếu người dùng đã đăng nhập
            if (!string.IsNullOrEmpty(username))
            {
                using (var httpClient = new HttpClient())
                {
                    // Lấy giỏ hàng
                    var requestData = new { username = username };
                    var jsonContent = new StringContent(
                        JsonConvert.SerializeObject(requestData),
                        Encoding.UTF8,
                        "application/json");

                    var response = await httpClient.PostAsync("http://127.0.0.1:5000/api/giohang", jsonContent);

                    if (response.IsSuccessStatusCode)
                    {
                        var jsonString = await response.Content.ReadAsStringAsync();
                        cart = JsonConvert.DeserializeObject<List<ModelGioHang>>(jsonString);
                        if (cart != null && cart.Any())
                        {
                            Session["Cart"] = cart;
                        }
                    }

                    // Lấy danh sách voucher - Thêm đoạn này
                    var voucherResponse = await httpClient.GetAsync("http://127.0.0.1:5000/api/vouchers");
                    if (voucherResponse.IsSuccessStatusCode)
                    {
                        var voucherData = await voucherResponse.Content.ReadAsStringAsync();
                        vouchers = JsonConvert.DeserializeObject<List<Voucher>>(voucherData);
                    }
                }
            }

            cart = Session["Cart"] as List<ModelGioHang>;
            if (cart != null)
            {
                var voucher = Session["Coupon"] as Voucher;
                Session["CouponDH"] = voucher;
                decimal tongTien = (decimal)cart.Sum(item => item.SoLuong * item.Gia);

                if (voucher != null)
                {
                    tongTien -= (decimal)(tongTien * voucher.GiamGia / 100);
                }
                ViewBag.TongTien = tongTien;
                Session.Remove("Coupon");
            }
            else
            {
                ViewBag.TongTien = 0;
            }

            ViewBag.Cart = cart;
            ViewBag.Voucher = vouchers; // Thêm dòng này
            return View();
        }
        [HttpPost]
        public async Task<ActionResult> AddToCart(int productId, int quantity)
        {
            var httpClient = new HttpClient();
            var response = await httpClient.PostAsJsonAsync("http://127.0.0.1:5000/api/get_product", new { productId = productId });
            var product = new SanPham();
            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                dynamic result = JsonConvert.DeserializeObject(json);
                product = ((JObject)result.product).ToObject<SanPham>();

            }

            if (product == null || product.SoLuong == 0 || quantity > product.SoLuong)
            {
                TempData["Message"] = "Sản phẩm không hợp lệ hoặc hết hàng.";
                Debug.WriteLine($"Không thể thêm sản phẩm {productId}, số lượng yêu cầu {quantity}, số lượng tồn kho {product?.SoLuong ?? 0}");
                return RedirectToAction("ChiTietSanPham", "Home", new { id = productId });
            }

            var cart = Session["Cart"] as List<ModelGioHang> ?? new List<ModelGioHang>();
            var cartItem = cart.SingleOrDefault(ci => ci.MaSanPham == productId);

            if (cartItem == null)
            {
                cart.Add(new ModelGioHang { MaSanPham = productId, SoLuong = quantity, Gia = product.GiaMoi ?? product.Gia, TenSanPham = product.TenSanPham, HinhAnh = product.HinhAnh });
                Debug.WriteLine($"Thêm sản phẩm mới vào giỏ: ID {productId}, Số lượng {quantity}, Giá {(product.GiaMoi ?? product.Gia)}");
            }
            else
            {
                cartItem.SoLuong += quantity;
                Debug.WriteLine($"Cập nhật số lượng sản phẩm {productId}: {cartItem.SoLuong}");
            }

            Debug.WriteLine($"Giỏ hàng hiện có {cart.Count} sản phẩm.");

            Session["Cart"] = cart;
            return RedirectToAction("GioHang", "Home");
        }
        [HttpPost]
        public async Task<JsonResult> AddToCartJson(int productId, int quantity = 1)
        {
            try
            {
                Debug.WriteLine($"AddToCart called: productId={productId}, quantity={quantity}");

                var httpClient = new HttpClient();
                var response = await httpClient.PostAsJsonAsync("http://127.0.0.1:5000/api/get_product", new { productId = productId });
                var product = new SanPham();

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    dynamic result = JsonConvert.DeserializeObject(json);
                    product = ((JObject)result.product).ToObject<SanPham>();
                }

                if (product == null)
                {
                    Debug.WriteLine($"Không tìm thấy sản phẩm với ID: {productId}");
                    return Json(new { success = false, message = "Không tìm thấy sản phẩm." });
                }

                if (product.SoLuong == 0)
                {
                    Debug.WriteLine($"Sản phẩm {productId} đã hết hàng");
                    return Json(new { success = false, message = "Sản phẩm đã hết hàng." });
                }

                if (quantity > product.SoLuong)
                {
                    Debug.WriteLine($"Số lượng yêu cầu {quantity} vượt quá tồn kho {product.SoLuong}");
                    return Json(new
                    {
                        success = false,
                        message = $"Chỉ còn {product.SoLuong} sản phẩm trong kho."
                    });
                }

                // Lấy giỏ hàng từ session
                var cart = Session["Cart"] as List<ModelGioHang> ?? new List<ModelGioHang>();
                var cartItem = cart.SingleOrDefault(ci => ci.MaSanPham == productId);

                if (cartItem == null)
                {
                    // Thêm sản phẩm mới vào giỏ
                    cart.Add(new ModelGioHang
                    {
                        MaSanPham = productId,
                        SoLuong = quantity,
                        Gia = product.GiaMoi ?? product.Gia,
                        TenSanPham = product.TenSanPham,
                        HinhAnh = product.HinhAnh
                    });
                    Debug.WriteLine($"Thêm sản phẩm mới vào giỏ: ID {productId}, Số lượng {quantity}");
                }
                else
                {
                    // Kiểm tra tổng số lượng sau khi cộng thêm
                    int newTotalQuantity = cartItem.SoLuong + quantity;
                    if (newTotalQuantity > product.SoLuong)
                    {
                        return Json(new
                        {
                            success = false,
                            message = $"Chỉ còn {product.SoLuong} sản phẩm trong kho. Bạn đã có {cartItem.SoLuong} trong giỏ hàng."
                        });
                    }

                    cartItem.SoLuong = newTotalQuantity;
                    Debug.WriteLine($"Cập nhật số lượng sản phẩm {productId}: {cartItem.SoLuong}");
                }

                // Lưu giỏ hàng vào session
                Session["Cart"] = cart;

                // Tính tổng số items trong giỏ hàng
                int totalItems = cart.Sum(x => x.SoLuong);

                Debug.WriteLine($"Giỏ hàng hiện có {cart.Count} loại sản phẩm, tổng {totalItems} items");

                return Json(new
                {
                    success = true,
                    message = "Sản phẩm đã được thêm vào giỏ hàng!",
                    cartItemCount = totalItems,
                    productName = product.TenSanPham
                });
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error in AddToCart: {ex.Message}");
                return Json(new
                {
                    success = false,
                    message = "Có lỗi xảy ra khi thêm sản phẩm vào giỏ hàng."
                });
            }
        }

        public JsonResult XoaGioHang(int id)
        {
            var cart = Session["Cart"] as List<ModelGioHang>;
            if (cart != null)
            {
                cart.RemoveAll(item => item.MaSanPham == id);
                Session["Cart"] = cart;
            }
            return Json(new { success = true, message = "Xóa sản phẩm trong giỏ hàng thành công" });
        }

        [HttpPost]
        public async Task<JsonResult> CapNhatGioHang(int productId, int quantity = 1)
        {
            var cart = Session["Cart"] as List<ModelGioHang>;
            if (cart == null)
            {
                return Json(new { success = false, message = "Giỏ hàng không tồn tại." }, JsonRequestBehavior.AllowGet);
            }

            var cartItem = cart.SingleOrDefault(ci => ci.MaSanPham == productId);
            if (cartItem != null)
            {
                // Gọi API Flask để lấy thông tin sản phẩm
                using (var client = new HttpClient())
                {
                    var apiUrl = "http://127.0.0.1:5000/api/get_product";
                    var postData = new
                    {
                        productId = productId
                    };

                    var content = new StringContent(JsonConvert.SerializeObject(postData), Encoding.UTF8, "application/json");

                    var response = await client.PostAsync(apiUrl, content);
                    var result = await response.Content.ReadAsStringAsync();
                    dynamic data = JsonConvert.DeserializeObject(result);

                    if (data.success == true)
                    {
                        int soLuongTonKho = data.product.SoLuong;

                        if (quantity <= soLuongTonKho)
                        {
                            cartItem.SoLuong = quantity;
                            Session["Cart"] = cart;
                            return Json(new { success = true, message = "Cập nhật thành công." }, JsonRequestBehavior.AllowGet);
                        }
                        else
                        {
                            return Json(new { success = false, message = "Số lượng vượt quá tồn kho." }, JsonRequestBehavior.AllowGet);
                        }
                    }
                    else
                    {
                        return Json(new { success = false, message = "Không tìm thấy sản phẩm." }, JsonRequestBehavior.AllowGet);
                    }
                }
            }

            return Json(new { success = false, message = "Sản phẩm không tồn tại." }, JsonRequestBehavior.AllowGet);
        }

        [HttpPost]
        public async Task<JsonResult> ApplyCoupon(string coupon)
        {
            try
            {
                if (string.IsNullOrEmpty(coupon))
                {
                    return Json(new
                    {
                        success = false,
                        message = "Vui lòng nhập mã giảm giá."
                    }, JsonRequestBehavior.AllowGet);
                }

                System.Diagnostics.Debug.WriteLine($"ApplyCoupon called with coupon: {coupon}");

                // Clear existing coupon first
                Session["Coupon"] = null;

                using (var httpClient = new HttpClient())
                {
                    // Add timeout to prevent hanging requests
                    httpClient.Timeout = TimeSpan.FromSeconds(10);

                    var apiRequestData = new { coupon = coupon };
                    var jsonContent = new StringContent(
                        JsonConvert.SerializeObject(apiRequestData),
                        Encoding.UTF8,
                        "application/json");

                    var response = await httpClient.PostAsync("http://127.0.0.1:5000/api/apply_coupon", jsonContent);
                    var responseContent = await response.Content.ReadAsStringAsync();

                    System.Diagnostics.Debug.WriteLine($"API Response Status: {response.StatusCode}");
                    System.Diagnostics.Debug.WriteLine($"API Response Content: {responseContent}");

                    if (!response.IsSuccessStatusCode)
                    {
                        dynamic errorResult = null;
                        try
                        {
                            errorResult = JsonConvert.DeserializeObject(responseContent);
                        }
                        catch (JsonException)
                        {
                            // If response is not valid JSON, use default message
                        }

                        return Json(new
                        {
                            success = false,
                            message = (string)(errorResult?.message ?? "Mã giảm giá không hợp lệ hoặc đã hết hạn.")
                        }, JsonRequestBehavior.AllowGet);
                    }

                    var result = JsonConvert.DeserializeObject<CouponResponse>(responseContent);

                    if (result?.success == true && result.coupon != null)
                    {
                        // Only set session if coupon is valid
                        Session["Coupon"] = result.coupon;

                        return Json(new
                        {
                            success = true,
                            message = "Áp dụng mã giảm giá thành công!",
                            coupon = new
                            {
                                code = result.coupon.Code,
                                giamGia = result.coupon.GiamGia,
                                moTa = result.coupon.MoTa
                            }
                        }, JsonRequestBehavior.AllowGet);
                    }

                    return Json(new
                    {
                        success = false,
                        message = result?.message ?? "Mã giảm giá không hợp lệ."
                    }, JsonRequestBehavior.AllowGet);
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Exception: {ex.Message}");
                return Json(new
                {
                    success = false,
                    message = "Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng và thử lại."
                }, JsonRequestBehavior.AllowGet);
            }
            catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
            {
                System.Diagnostics.Debug.WriteLine($"Timeout Exception: {ex.Message}");
                return Json(new
                {
                    success = false,
                    message = "Kết nối quá chậm. Vui lòng thử lại sau."
                }, JsonRequestBehavior.AllowGet);
            }
            catch (JsonException ex)
            {
                System.Diagnostics.Debug.WriteLine($"JSON Exception: {ex.Message}");
                return Json(new
                {
                    success = false,
                    message = "Dữ liệu trả về từ server không hợp lệ."
                }, JsonRequestBehavior.AllowGet);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"General Exception: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Stack trace: {ex.StackTrace}");
                return Json(new
                {
                    success = false,
                    message = "Có lỗi xảy ra. Vui lòng thử lại sau."
                }, JsonRequestBehavior.AllowGet);
            }
        }

        public ActionResult ChiTietDonHang(int id)
        {
            var httpClient = new HttpClient();
            var jsonData = new { orderId = id };

            var response = httpClient.PostAsJsonAsync("http://127.0.0.1:5000/api/get_order_detail", jsonData).Result;

            if (response.IsSuccessStatusCode)
            {
                var result = response.Content.ReadAsAsync<dynamic>().Result;

                var order = result.order;
                var chiTietDonHang = result.details;
                var giamGia = result.giamGia;

                ViewBag.Order = order;
                ViewBag.ChiTietDonHang = chiTietDonHang;
                ViewBag.GiamGia = giamGia;

                return View();
            }

            return HttpNotFound("Không thể lấy thông tin đơn hàng từ API.");
        }

        // 1. Lấy đơn hàng với thông tin có thể đổi trả/đánh giá
        public async Task<ActionResult> DonHangCuaToi(int page = 1)
        {
            var username = Session["Username"] as string;
            if (string.IsNullOrEmpty(username)) return RedirectToAction("DangNhap", "Home");

            // Chỉ cần trả về View, JavaScript sẽ tự động load data
            ViewBag.CurrentPage = page;
            return View();
        }


    }
}