using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    [Table("DonDoiTra")]
    public class DonDoiTra
    {
        [Key]
        public int MaDoiTra { get; set; }

        [Required]
        public int MaDonHang { get; set; }

        [Required]
        [StringLength(20)]
        public string LoaiYeuCau { get; set; } // "Đổi" hoặc "Trả"

        [Required]
        [StringLength(255)]
        public string LyDo { get; set; }

        public string MoTa { get; set; }

        [StringLength(255)]
        public string HinhAnh { get; set; }

        public DateTime NgayTao { get; set; } = DateTime.Now;

        public DateTime? NgayCapNhat { get; set; }

        public DateTime? NgayHoanTat { get; set; }

        [StringLength(50)]
        public string TrangThai { get; set; } = "Chờ xử lý";

        public string GhiChuNhanVien { get; set; }

        // Navigation property
        [ForeignKey("MaDonHang")]
        public virtual DonHang DonHang { get; set; }
    }
}