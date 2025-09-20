using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
	public class TaiKhoan
	{
        public int MaTaiKhoan { get; set; }
        public string Username { get; set; }
        public string Password { get; set; }
        public Nullable<int> MaQuyen { get; set; }
        public string HoTen { get; set; }
        public string DiaChi { get; set; }
        public string SoDienThoai { get; set; }
        public string Email { get; set; }
        public Nullable<System.DateTime> NgayTao { get; set; }
        public Nullable<bool> TrangThai { get; set; }
    }
}