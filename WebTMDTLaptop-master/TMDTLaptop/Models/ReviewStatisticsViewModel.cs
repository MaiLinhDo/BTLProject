using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models
{
    public class ReviewStatisticsViewModel
    {
        public int TotalReviews { get; set; }
        public double AverageRating { get; set; }
        public double FiveStarPercentage { get; set; }
        public int ThisMonthReviews { get; set; }
        public List<RatingDistribution> RatingDistribution { get; set; }
        public List<TopRatedProduct> TopRatedProducts { get; set; }
        public List<TopRatedProduct> LowRatedProducts { get; set; }
        public List<RecentReview> RecentReviews { get; set; }
    }
    public class RatingDistribution
    {
        public int Stars { get; set; }
        public int Count { get; set; }
        public double Percentage { get; set; }
    }

    public class TopRatedProduct
    {
        public int MaSanPham { get; set; }
        public string TenSanPham { get; set; }
        public string HinhAnh { get; set; }
        public double AverageRating { get; set; }
        public int TotalReviews { get; set; }
    }

    public class RecentReview
    {
        public int DiemDanhGia { get; set; }
        public string BinhLuan { get; set; }
        public string NgayDanhGia { get; set; }
        public string HoTen { get; set; }
        public string TenSanPham { get; set; }
        public int MaSanPham { get; set; }
        public string HinhAnh { get; set; }
    }

    // ViewModel cho đơn hàng có action
    public class OrderWithActionsViewModel
    {
        public int MaDonHang { get; set; }
        public string NgayDatHang { get; set; }
        public decimal TongTien { get; set; }
        public string TrangThai { get; set; }
        public string DiaChiGiaoHang { get; set; }
        public int SoNgayTuLucDat { get; set; }
        public int? SoNgayTuLucNhan { get; set; }
        public List<OrderProductViewModel> Products { get; set; }
        public OrderActionsViewModel Actions { get; set; }
    }

    public class OrderProductViewModel
    {
        public int MaSanPham { get; set; }
        public string TenSanPham { get; set; }
        public int SoLuong { get; set; }
        public decimal Gia { get; set; }
        public string HinhAnh { get; set; }
    }

    public class OrderActionsViewModel
    {
        public bool CanCancel { get; set; }
        public bool CanConfirmReceived { get; set; }
        public bool CanReturn { get; set; }
        public bool CanReview { get; set; }
        public bool CanWarranty { get; set; }
    }
}