using System.ComponentModel.DataAnnotations;

namespace TMDTLaptop.Models.Class
{
    public class ThongSoKyThuat
    {
        public int MaThongSo { get; set; }

        [Required(ErrorMessage = "Tên thông số không được để trống.")]
        public string TenThongSo { get; set; }

        public string DonVi { get; set; }

        public string MoTa { get; set; }

        public int? ThuTu { get; set; }

        public bool? TrangThai { get; set; }

        // Giá trị dùng cho màn hình nhập sản phẩm
        public string GiaTri { get; set; }
    }
}

