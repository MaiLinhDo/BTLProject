using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    public partial class ChiTietGioHang
    {
        public int MaChiTiet { get; set; }
        public Nullable<int> MaGioHang { get; set; }
        public Nullable<int> MaSanPham { get; set; }
        public Nullable<int> SoLuong { get; set; }
        public Nullable<decimal> Gia { get; set; }
        public Nullable<decimal> GiaMoi { get; set; }

    
    }
}