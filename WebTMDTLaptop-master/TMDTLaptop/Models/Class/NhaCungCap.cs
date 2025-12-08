using System;
using System.ComponentModel.DataAnnotations;

namespace TMDTLaptop.Models.Class
{
    public class NhaCungCap
    {
        public int MaNhaCungCap { get; set; }

        [Required(ErrorMessage = "Tên nhà cung cấp không được để trống.")]
        [StringLength(150)]
        public string TenNhaCungCap { get; set; }

        [StringLength(50)]
        public string MaSoThue { get; set; }

        [EmailAddress(ErrorMessage = "Email không hợp lệ.")]
        public string Email { get; set; }

        [Phone(ErrorMessage = "Số điện thoại không hợp lệ.")]
        public string SoDienThoai { get; set; }

        [StringLength(255)]
        public string DiaChi { get; set; }

        public bool? TrangThai { get; set; }

        public string GhiChu { get; set; }

        public DateTime? NgayTao { get; set; }
    }
}

