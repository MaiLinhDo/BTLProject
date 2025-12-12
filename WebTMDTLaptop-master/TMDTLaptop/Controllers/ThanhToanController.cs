using TMDTLaptop.Models;
using TMDTLaptop.Models.Class;
using System;
using System.Collections.Generic;
using System.Configuration;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using Newtonsoft.Json;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace TMDTLaptop.Controllers
{
    public class ThanhToanController : Controller
    {   // GET: ThanhToan

        // ThanhToanQuaThe: Xử lý thanh toán VNPay
        public ActionResult ThanhToanQuaThe(decimal amount)
        {
            string vnp_Returnurl = ConfigurationManager.AppSettings["vnp_Returnurl"];   //URL để VNPay chuyển hướng lại sau khi thanh toán.
            string vnp_Url = ConfigurationManager.AppSettings["vnp_Url"];   // URL endpoint để gửi yêu cầu.
            string vnp_TmnCode = ConfigurationManager.AppSettings["vnp_TmnCode"];   // Mã Terminal Code mà VNPay cấp cho bạn.
            string vnp_HashSecret = ConfigurationManager.AppSettings["vnp_HashSecret"]; // Mã bí mật để ký dữ liệu gửi đi.

            VnPayLibrary vnpay = new VnPayLibrary();
            long madonhang = DateTime.Now.Ticks;    //Tạo mã đơn hàng dựa vào thời gian để đảm bảo duy nhất.
            vnpay.AddRequestData("vnp_Version", VnPayLibrary.VERSION);
            vnpay.AddRequestData("vnp_Command", "pay");
            vnpay.AddRequestData("vnp_TmnCode", vnp_TmnCode);
            vnpay.AddRequestData("vnp_Amount", ((long)amount * 100).ToString());  // Tổng tiền phải nhân 100 vì VNPay tính bằng đơn vị nhỏ nhất của tiền Việt (tức là đồng → xu).
            vnpay.AddRequestData("vnp_CreateDate", DateTime.Now.ToString("yyyyMMddHHmmss"));
            vnpay.AddRequestData("vnp_CurrCode", "VND");
            vnpay.AddRequestData("vnp_IpAddr", Utils.GetIpAddress());
            vnpay.AddRequestData("vnp_Locale", "vn");
            vnpay.AddRequestData("vnp_OrderInfo", "Thanh toán đơn hàng: " + madonhang);
            vnpay.AddRequestData("vnp_OrderType", "other");
            vnpay.AddRequestData("vnp_ReturnUrl", vnp_Returnurl);
            vnpay.AddRequestData("vnp_TxnRef", madonhang.ToString());

            string paymentUrl = vnpay.CreateRequestUrl(vnp_Url, vnp_HashSecret);    //Tạo URL có đầy đủ thông tin và mã hóa chữ ký bảo mật.
            return Redirect(paymentUrl); // chuyển hướng đến trang của VNPay để thanh toán
        }

        public async Task<ActionResult> Return()
        {
            if (Request.QueryString.Count > 0)
            {
                string vnp_HashSecret = ConfigurationManager.AppSettings["vnp_HashSecret"];
                var vnpayData = Request.QueryString;
                VnPayLibrary vnpay = new VnPayLibrary();

                foreach (string s in vnpayData)
                {
                    if (!string.IsNullOrEmpty(s) && s.StartsWith("vnp_"))
                        vnpay.AddResponseData(s, vnpayData[s]);
                }

                string vnp_ResponseCode = vnpay.GetResponseData("vnp_ResponseCode");
                string vnp_TransactionStatus = vnpay.GetResponseData("vnp_TransactionStatus");
                string vnp_SecureHash = Request.QueryString["vnp_SecureHash"];
                bool checkSignature = vnpay.ValidateSignature(vnp_SecureHash, vnp_HashSecret);

                if (checkSignature && vnp_ResponseCode == "00" && vnp_TransactionStatus == "00")
                {
                    var pendingOrder = Session["PendingOrder"] as DonHang;
                    var cart = Session["Cart"] as List<ModelGioHang>;
                    if (cart == null || !cart.Any()) return RedirectToAction("GioHang", "Home");
                    if (pendingOrder != null)
                    {
                        pendingOrder.TrangThai = "Đã thanh toán";

                        // Gửi thông tin đơn hàng qua API Flask
                        HttpClient client = new HttpClient();
                        var orderPayload = new
                        {
                            MaDonHang = pendingOrder.MaDonHang,
                            MaTaiKhoan = pendingOrder.MaTaiKhoan,
                            NgayDatHang = pendingOrder.NgayDatHang.Value.ToString("yyyy-MM-dd HH:mm:ss"),
                            TongTien = pendingOrder.TongTien,
                            DiaChiGiaoHang = pendingOrder.DiaChiGiaoHang,
                            SoDienThoai = pendingOrder.SoDienThoai,
                            TrangThai = pendingOrder.TrangThai,
                            MaVoucher = pendingOrder.MaVoucher,
                            HinhThucThanhToan = "VNPAY", // Thanh toán qua VNPay
                            ChiTietDonHang = cart.Select(item => new
                            {
                                MaSanPham = item.MaSanPham,
                                SoLuong = item.SoLuong,
                                Gia = item.Gia
                            }).ToList()
                        };
                        // Gửi dữ liệu POST sang Flask API
                        var content = new StringContent(JsonConvert.SerializeObject(orderPayload), Encoding.UTF8, "application/json");
                        var response = client.PostAsync("http://127.0.0.1:5000/api/them_donhang", content).Result;

                        if (response.IsSuccessStatusCode)
                        {
                            var responseBody = response.Content.ReadAsStringAsync().Result;
                            dynamic result = JsonConvert.DeserializeObject(responseBody);
                            DonHang donhang = result["order"].ToObject<DonHang>();
                            Session.Remove("Cart");
                            Session.Remove("CouponDH");
                            return RedirectToAction("DatHangThanhCong","Home", donhang );
                            // Bạn có thể lưu maDonHang hoặc chuyển hướng người dùng tại đây
                        }
                        else
                        {
                            ModelState.AddModelError("", "Lỗi khi gửi đơn hàng đến API.");
                            return RedirectToAction("QuanLySanPham");
                        }
                    }
                }
                else
                {
                    ViewBag.InnerText = "Có lỗi xảy ra khi thanh toán. Mã lỗi: " + vnp_ResponseCode;
                }
            }
            return View();
        }


    }
}