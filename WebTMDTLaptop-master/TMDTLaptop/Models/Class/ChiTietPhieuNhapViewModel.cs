using System.Collections.Generic;

namespace TMDTLaptop.Models.Class
{
    public class ChiTietPhieuNhapViewModel
    {
        public int MaChiTiet { get; set; }
        public int MaPhieuNhap { get; set; }
        public int MaSanPham { get; set; }
        public string TenSanPham { get; set; }
        public int SoLuong { get; set; }
        public decimal GiaNhap { get; set; }
        public decimal TongTien { get; set; }
        public List<string> SerialNumbers { get; set; }
    }
}

