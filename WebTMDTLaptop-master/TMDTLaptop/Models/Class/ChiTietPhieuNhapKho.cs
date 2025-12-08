using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    public partial class ChiTietPhieuNhapKho
    {
        public int MaChiTiet { get; set; }
        public Nullable<int> MaPhieuNhap { get; set; }
        public int MaSanPham { get; set; }
        public int SoLuong { get; set; }
        public decimal GiaNhap { get; set; }
        public Nullable<decimal> TongTien { get; set; }

        public string SerialNumbers { get; set; }
    }
}