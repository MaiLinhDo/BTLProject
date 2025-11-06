using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    [Table("DanhGiaSanPham")]
    public class DanhGiaSanPham
    {
        [Key]
        public int MaDanhGia { get; set; }

        [Required]
        public int MaTaiKhoan { get; set; }

        [Required]
        public int MaSanPham { get; set; }

        [Required]
        [Range(1, 5, ErrorMessage = "Điểm đánh giá phải từ 1 đến 5")]
        public int DiemDanhGia { get; set; }

        [Required]
        public string BinhLuan { get; set; }

        public DateTime NgayDanhGia { get; set; } = DateTime.Now;

        // Navigation properties
        [ForeignKey("MaTaiKhoan")]
        public virtual TaiKhoan TaiKhoan { get; set; }

        [ForeignKey("MaSanPham")]
        public virtual SanPham SanPham { get; set; }
    }
}