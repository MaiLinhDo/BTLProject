using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Web;
using System.Web.Mvc;
using TMDTLaptop.Models;

namespace TMDTLaptop.Controllers
{
    public class LoginController : Controller
    {
      
        public ActionResult DangNhap()
        {
            return View();
        }
        public ActionResult DangXuat()
        {
            Session.Remove("Admin");
            return RedirectToAction("DangNhap","Login");
        }
        [HttpPost]
        public async Task<ActionResult> DangNhap(string tenDangNhap, string matKhau)
        {
            var client = new HttpClient();
          
                // Tạo nội dung JSON
                var json = new
                {
                    Username = tenDangNhap,
                    Password = matKhau
                };
                var content = new StringContent(JsonConvert.SerializeObject(json), Encoding.UTF8, "application/json");

                // Gửi POST request đến Flask API
                var response = await client.PostAsync("http://127.0.0.1:5000/api/dangnhap", content);
              
                if (response.IsSuccessStatusCode)
                {
                    var responseData = await response.Content.ReadAsStringAsync();
                    Debug.WriteLine(responseData);
                    dynamic result = JsonConvert.DeserializeObject(responseData);
                    if (result.success == false) 
                    {
                        // Nếu đăng nhập thất bại
                        ViewBag.ErrorMessage = result.message;
                        return View();
                    }
                    // Kiểm tra nếu kết quả trả về có tài khoản và đúng thông tin
                    if (result != null && result.user.Username != null)
                    {
                        bool trangThai = result.user.TrangThai;
                        Debug.WriteLine(trangThai);
                        int quyen = result.user.Quyen;

                        if (!trangThai)
                        {
                            ViewBag.ErrorMessage = "Tài khoản của bạn đã bị khóa!";
                            return View();
                        }

                        Session["Admin"] = result.user.Username.ToString();
                        Session["Quyen"] = quyen;

                        if (quyen == 1)
                            return RedirectToAction("Index", "Admin");
                        else if (quyen == 2)
                            return RedirectToAction("Index", "NV");
                    }
                 
                }
                else
                {
                   
                    return View();
                }
            ViewBag.ErrorMessage = "Tài khoản của bạn đã bị khóa!";
            return View();
        }

    }
}