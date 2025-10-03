using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models
{
	public class ModelGioHang
	{
        public int MaChiTiet { get; set; }
        public int MaGioHang { get; set; }
        public int MaSanPham { get; set; }
        public string TenSanPham { get; set; }
        public int SoLuong { get; set; }
        public decimal Gia { get; set; }
        public decimal? GiaMoi { get; set; }

        public string HinhAnh { get; set; }
    }
}