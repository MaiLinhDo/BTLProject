using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    [Table("ChiTietDoiTra")]
    public class ChiTietDoiTra
    {
        [Key]
        public int MaChiTiet { get; set; }

        [Required]
        public int MaDoiTra { get; set; }

        [Required]
        public int MaSanPham { get; set; }

        [Required]
        public int SoLuong { get; set; }

        [StringLength(255)]
        public string LyDoChiTiet { get; set; }

        // Navigation properties
        [ForeignKey("MaDoiTra")]
        public virtual DonDoiTra DonDoiTra { get; set; }

        [ForeignKey("MaSanPham")]
        public virtual SanPham SanPham { get; set; }
    }
}