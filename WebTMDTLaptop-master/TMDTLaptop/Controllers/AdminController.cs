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






    }
}