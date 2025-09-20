using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
	public class GioHang
	{
        public int MaGioHang { get; set; }
        public Nullable<int> MaTaiKhoan { get; set; }
        public Nullable<System.DateTime> NgayTao { get; set; }
        public Nullable<decimal> TongTien { get; set; }
    }
}