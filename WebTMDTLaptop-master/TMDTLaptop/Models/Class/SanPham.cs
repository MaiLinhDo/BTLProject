using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;
using System.Web.Mvc;

namespace TMDTLaptop.Models.Class
{
	public class SanPham
	{

        public int MaSanPham { get; set; }

        [Required(ErrorMessage = "Tên sản phẩm không được để trống.")]
        public string TenSanPham { get; set; }

        [AllowHtml]
        public string MoTa { get; set; }

        [Required(ErrorMessage = "Giá không được để trống.")]
        [Range(0, double.MaxValue, ErrorMessage = "Giá phải là số dương.")]
        public decimal Gia { get; set; }

        public Nullable<decimal> GiaMoi { get; set; }

        public string HinhAnh { get; set; }

        [Required(ErrorMessage = "Bạn phải chọn hãng.")]
        public Nullable<int> MaHang { get; set; }

        [Required(ErrorMessage = "Bạn phải chọn danh mục.")]
        public Nullable<int> MaDanhMuc { get; set; }

        public Nullable<System.DateTime> NgayTao { get; set; }
        public Nullable<bool> TrangThai { get; set; }

        [Required(ErrorMessage = "Số lượng không được để trống.")]
        [Range(0, int.MaxValue, ErrorMessage = "Số lượng phải là số nguyên không âm.")]
        public Nullable<int> SoLuong { get; set; }
        public double? TrungBinhSao { get; set; }
        public int? SoLuongDanhGia { get; set; }

        // Helper method để lấy số sao đầy
        public int SaoDay => (int)Math.Floor((decimal)TrungBinhSao.GetValueOrDefault());

        // Helper method để lấy số sao rỗng
        public int SaoRong => Math.Max(0, 5 - SaoDay);
    }
}