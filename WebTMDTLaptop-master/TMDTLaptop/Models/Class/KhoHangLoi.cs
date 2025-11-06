using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    [Table("KhoHangLoi")]
    public class KhoHangLoi
    {
        [Key]
        public int MaKhoLoi { get; set; }

        [Required]
        public int MaSanPham { get; set; }

        [Required]
        public int SoLuong { get; set; }

        public DateTime NgayNhap { get; set; } = DateTime.Now;

        [StringLength(255)]
        public string LyDo { get; set; }

        // Navigation property
        [ForeignKey("MaSanPham")]
        public virtual SanPham SanPham { get; set; }
    }
}