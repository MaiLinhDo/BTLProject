using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TMDTLaptop.Models.Class
{
    [Table("PhieuBaoHanh")]
    public class PhieuBaoHanh
    {
        [Key]
        public int MaPhieuBH { get; set; }

        [Required]
        public int MaDonHang { get; set; }

        [Required]
        public int MaTaiKhoan { get; set; }

        [Required]
        public int MaSanPham { get; set; }

        [Required]
        public int SoLuongBH { get; set; } = 1;

        [StringLength(500)]
        public string MoTaLoi { get; set; }

        public string HinhAnhLoi { get; set; } // JSON array

        public DateTime NgayTao { get; set; } = DateTime.Now;

        public DateTime? NgayBatDauBH { get; set; }

        public DateTime? NgayKetThucBH { get; set; }

        [StringLength(50)]
        public string TrangThai { get; set; } = "Chờ xử lý";

        [StringLength(255)]
        public string LyDoTuChoi { get; set; }

        public DateTime NgayCapNhat { get; set; } = DateTime.Now;

        public int? NhanVienXuLy { get; set; }

        // Navigation Properties
        [ForeignKey("MaDonHang")]
        public virtual DonHang DonHang { get; set; }

        [ForeignKey("MaTaiKhoan")]
        public virtual TaiKhoan TaiKhoan { get; set; }

        [ForeignKey("MaSanPham")]
        public virtual SanPham SanPham { get; set; }

        public virtual ICollection<LichSuBaoHanh> LichSuBaoHanhs { get; set; }
        public virtual ICollection<VanChuyenBaoHanh> VanChuyenBaoHanhs { get; set; }
        public virtual ICollection<XuLyNhaSanXuat> XuLyNhaSanXuats { get; set; }

        // Helper Properties
        [NotMapped]
        public bool ConBaoHanh => NgayKetThucBH.HasValue && NgayKetThucBH.Value > DateTime.Now;

        [NotMapped]
        public int SoNgayConLai => NgayKetThucBH.HasValue ?
            Math.Max(0, (NgayKetThucBH.Value - DateTime.Now).Days) : 0;
    }

    [Table("LichSuBaoHanh")]
    public class LichSuBaoHanh
    {
        [Key]
        public int MaLichSu { get; set; }

        [Required]
        public int MaPhieuBH { get; set; }

        [StringLength(50)]
        public string TrangThaiCu { get; set; }

        [StringLength(50)]
        public string TrangThaiMoi { get; set; }

        [StringLength(500)]
        public string MoTa { get; set; }

        public DateTime NgayCapNhat { get; set; } = DateTime.Now;

        public int? NguoiCapNhat { get; set; }

        // Navigation Property
        [ForeignKey("MaPhieuBH")]
        public virtual PhieuBaoHanh PhieuBaoHanh { get; set; }
    }

    [Table("VanChuyenBaoHanh")]
    public class VanChuyenBaoHanh
    {
        [Key]
        public int MaVanChuyen { get; set; }

        [Required]
        public int MaPhieuBH { get; set; }

        [StringLength(20)]
        public string LoaiVanChuyen { get; set; } // "Lấy hàng" hoặc "Trả hàng"

        [StringLength(100)]
        public string DonViVanChuyen { get; set; }

        [StringLength(50)]
        public string MaVanDon { get; set; }

        [StringLength(255)]
        public string DiaChiLayHang { get; set; }

        [StringLength(255)]
        public string DiaChiTraHang { get; set; }

        public DateTime? NgayLayHang { get; set; }

        public DateTime? NgayGiaoHang { get; set; }

        [StringLength(50)]
        public string TrangThaiVanChuyen { get; set; } = "Chờ lấy hàng";

        [StringLength(255)]
        public string GhiChu { get; set; }

        // Navigation Property
        [ForeignKey("MaPhieuBH")]
        public virtual PhieuBaoHanh PhieuBaoHanh { get; set; }
    }

    [Table("XuLyNhaSanXuat")]
    public class XuLyNhaSanXuat
    {
        [Key]
        public int MaXuLy { get; set; }

        [Required]
        public int MaPhieuBH { get; set; }

        [StringLength(100)]
        public string TenNhaSanXuat { get; set; }

        [StringLength(50)]
        public string MaPhieuNSX { get; set; }

        public DateTime? NgayGui { get; set; }

        public DateTime? NgayNhan { get; set; }

        public DateTime? NgayHoanTat { get; set; }

        [StringLength(50)]
        public string HinhThucXuLy { get; set; } // "Sửa chữa", "Thay thế", "Đổi mới"

        [StringLength(500)]
        public string MoTaXuLy { get; set; }

        [Column(TypeName = "decimal(18,2)")]
        public decimal ChiPhi { get; set; } = 0;

        [StringLength(50)]
        public string TrangThai { get; set; } = "Đang xử lý";

        // Navigation Property
        [ForeignKey("MaPhieuBH")]
        public virtual PhieuBaoHanh PhieuBaoHanh { get; set; }
    }

    // DTO classes for API
    public class TaoBaoHanhRequest
    {
        [Required]
        public int MaDonHang { get; set; }

        [Required]
        public int MaSanPham { get; set; }

        [Required]
        public int SoLuongBH { get; set; }

        [Required]
        [StringLength(500)]
        public string MoTaLoi { get; set; }

        public List<string> HinhAnhLoi { get; set; } = new List<string>();
    }

    public class CapNhatTrangThaiRequest
    {
        [Required]
        public int MaPhieuBH { get; set; }

        [Required]
        [StringLength(50)]
        public string TrangThai { get; set; }

        [StringLength(255)]
        public string LyDoTuChoi { get; set; }

        [StringLength(500)]
        public string GhiChu { get; set; }
    }

    public class BaoHanhResponse
    {
        public int MaPhieuBH { get; set; }
        public int MaDonHang { get; set; }
        public string TenSanPham { get; set; }
        public string TenKhachHang { get; set; }
        public int SoLuongBH { get; set; }
        public string MoTaLoi { get; set; }
        public List<string> HinhAnhLoi { get; set; }
        public DateTime NgayTao { get; set; }
        public DateTime? NgayBatDauBH { get; set; }
        public DateTime? NgayKetThucBH { get; set; }
        public string TrangThai { get; set; }
        public string LyDoTuChoi { get; set; }
        public bool ConBaoHanh { get; set; }
        public int SoNgayConLai { get; set; }
        public List<LichSuBaoHanhResponse> LichSu { get; set; }
    }

    public class LichSuBaoHanhResponse
    {
        public string TrangThaiCu { get; set; }
        public string TrangThaiMoi { get; set; }
        public string MoTa { get; set; }
        public DateTime NgayCapNhat { get; set; }
        public string NguoiCapNhat { get; set; }
    }

    public class ThongKeBaoHanhResponse
    {
        public int TongPhieuBH { get; set; }
        public int ChoXuLy { get; set; }
        public int DangBaoHanh { get; set; }
        public int HoanTat { get; set; }
        public int TuChoi { get; set; }
        public decimal TongChiPhi { get; set; }
        public List<ThongKeSanPhamBH> TopSanPhamLoi { get; set; }
        public List<ThongKeTheoThang> BieuDoThang { get; set; }
    }

    public class ThongKeSanPhamBH
    {
        public string TenSanPham { get; set; }
        public int SoLuongBH { get; set; }
        public decimal TiLeBaoHanh { get; set; }
    }

    public class ThongKeTheoThang
    {
        public int Thang { get; set; }
        public int Nam { get; set; }
        public int SoLuongBH { get; set; }
        public decimal ChiPhi { get; set; }
    }
}