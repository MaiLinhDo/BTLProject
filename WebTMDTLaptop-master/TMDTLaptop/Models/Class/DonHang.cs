using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
	public class DonHang
	{
        public int MaDonHang { get; set; }
        public Nullable<int> MaTaiKhoan { get; set; }
        public Nullable<System.DateTime> NgayDatHang { get; set; }
        public Nullable<decimal> TongTien { get; set; }
        public Nullable<int> MaVoucher { get; set; }
        public string DiaChiGiaoHang { get; set; }
        public string SoDienThoai { get; set; }
        public string TrangThai { get; set; }
    }
}