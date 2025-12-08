using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
	public class PhieuNhapKho
	{
        public int MaPhieuNhap { get; set; }
        public System.DateTime NgayNhap { get; set; }
        public decimal TongTien { get; set; }
        public string GhiChu { get; set; }
        public int? MaNhaCungCap { get; set; }
        public string TenNhaCungCap { get; set; }
        public string SoDienThoaiNCC { get; set; }
        public string EmailNCC { get; set; }
    }
}