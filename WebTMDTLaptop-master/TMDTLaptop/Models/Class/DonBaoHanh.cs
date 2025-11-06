using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    [Table("DonBaoHanh")]
    public class DonBaoHanh
    {
        [Key]
        public int MaBaoHanh { get; set; }

        [Required]
        public int MaDonHang { get; set; }

        [Required]
        public int MaSanPham { get; set; }

        [Required]
        public string MoTaLoi { get; set; }

        [StringLength(255)]
        public string HinhAnh { get; set; }

        public DateTime NgayTao { get; set; } = DateTime.Now;

        public DateTime? NgayCapNhat { get; set; }

        public DateTime? NgayHoanTat { get; set; }

        [StringLength(50)]
        public string TrangThai { get; set; } = "Chờ xử lý";

        public string GhiChu { get; set; }

        // Navigation properties
        [ForeignKey("MaDonHang")]
        public virtual DonHang DonHang { get; set; }

        [ForeignKey("MaSanPham")]
        public virtual SanPham SanPham { get; set; }
    }
}