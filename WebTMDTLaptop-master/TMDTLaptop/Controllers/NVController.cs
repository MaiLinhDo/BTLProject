using OfficeOpenXml;
using System;
using System.Collections.Generic;
using System.Data.Entity;
using System.IO;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using TMDTLaptop.Models;
using iText.Kernel.Pdf;
using iText.Layout;
using iText.Layout.Element;
using iText.IO.Font;
using iText.IO.Font.Constants;
using iText.Kernel.Font;
using iText.Layout.Properties;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
namespace TMDTLaptop.Controllers
{
    public class NVController : Controller
    {
    
        public bool check()
        {
            if (Session["Admin"] == null) { return false; }
            return true;
        }
        // GET: NV
        public async Task<ActionResult> Index()
        {
            if (!check()) { return RedirectToAction("Loi404", "ChamSocKH"); }

            using (var client = new HttpClient())
            {
                client.BaseAddress = new Uri("http://127.0.0.1:5000");
                var response = await client.GetAsync("/api/revenue/today");

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();

                    // Dùng Newtonsoft.Json để parse dữ liệu trả về
                    dynamic data = JsonConvert.DeserializeObject(json);

                    // Parse doanh thu theo sản phẩm
                    var revenueByProduct = ((JArray)data.revenueByProduct).ToObject<List<RevenueByProductViewModel>>();
                    var revenueByCategory = ((JArray)data.revenueByCategory).ToObject<List<RevenueByCategoryViewModel>>();

                    ViewBag.RevenueByProduct = revenueByProduct;
                    ViewBag.RevenueByCategory = revenueByCategory;
                }
                else
                {
                    ViewBag.RevenueByProduct = new List<RevenueByProductViewModel>();
                    ViewBag.RevenueByCategory = new List<RevenueByCategoryViewModel>();
                }
            }

            return View();
        }

        // Thêm action xuất file Excel

        public async Task<ActionResult> DuyetDonHang(int id)
        {
            using (var client = new HttpClient())
            {
                var payload = new
                {
                    MaDonHang = id,
                    TrangThai = "Đã Giao"
                };

                var response = await client.PutAsJsonAsync("http://127.0.0.1:5000/api/update_order_status", payload);

                if (response.IsSuccessStatusCode)
                {
                    return RedirectToAction("QuanLyDonHang", "Admin");
                }
                else
                {
                    // Xử lý lỗi
                    return new HttpStatusCodeResult(500, "Cập nhật thất bại");
                }
            }
        }



    }
}