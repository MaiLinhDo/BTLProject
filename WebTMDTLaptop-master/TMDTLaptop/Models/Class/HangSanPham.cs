using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
	public class HangSanPham
	{
        public int MaHang { get; set; }
        public string TenHang { get; set; }
        public Nullable<bool> TrangThai { get; set; }
        public Nullable<System.DateTime> NgayTao { get; set; }
    }
}