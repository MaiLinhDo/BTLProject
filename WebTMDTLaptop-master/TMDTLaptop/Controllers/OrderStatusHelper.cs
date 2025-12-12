using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Controllers
{
    public static class OrderStatusHelper
    {
        public static string GetStatusDonTraBadgeClass(string status)
        {
            switch (status)
            {
                case "Chờ xử lý": return "badge-warning";
                case "Đã duyệt": return "badge-info";
                case "Chờ lấy hàng": return "badge-primary";
                case "Đang xử lý": return "badge-secondary";
                case "Đã xử lý": return "badge-success";
                case "Từ chối": return "badge-danger";
                default: return "badge-secondary";
            }
        }
        public static string GetStatusBadgeClass(string status)
        {
            switch (status)
            {
                case "Đặt hàng thành công": return "badge-primary";
                case "Đang chờ xử lý": return "badge-warning";
                case "Đã thanh toán": return "badge-success";
                case "Đang chuẩn bị hàng": return "badge-info";
                case "Đã giao cho đơn vị vận chuyển": return "badge-warning";
                case "Đơn hàng sẽ sớm được giao đến bạn": return "badge-secondary";
                case "Đã giao": return "badge-success";
                case "Đã hủy": return "badge-danger";
                case "Đã Hủy": return "badge-danger";
                case "Đã trả hàng": return "badge-dark";
                default: return "badge-secondary";
            }
        }

        public static List<string> GetNextValidStatuses(string currentStatus)
        {
            // Normalize chuỗi: trim và loại bỏ khoảng trắng thừa
            if (string.IsNullOrWhiteSpace(currentStatus))
                return new List<string>();
            
            currentStatus = currentStatus.Trim();
            
            switch (currentStatus)
            {
                case "Đặt hàng thành công":
                    return new List<string> { "Đang chờ xử lý", "Đang chuẩn bị hàng" };
                case "Đang chờ xử lý":
                    return new List<string> { "Đã thanh toán", "Đang chuẩn bị hàng" };
                case "Đã thanh toán":
                    return new List<string> { "Đang chuẩn bị hàng" };
                case "Đang chuẩn bị hàng":
                    return new List<string> { "Đã giao cho đơn vị vận chuyển" };
                case "Đã giao cho đơn vị vận chuyển":
                    return new List<string> { "Đơn hàng sẽ sớm được giao đến bạn" };
                case "Đơn hàng sẽ sớm được giao đến bạn":
                    return new List<string> { "Đã giao" };
                case "Đã giao":
                    return new List<string> { "Đã trả hàng" };
                default:
                    // Nếu không khớp, thử so sánh không phân biệt hoa thường
                    return GetNextValidStatusesCaseInsensitive(currentStatus);
            }
        }
        
        private static List<string> GetNextValidStatusesCaseInsensitive(string currentStatus)
        {
            // So sánh không phân biệt hoa thường
            if (string.IsNullOrWhiteSpace(currentStatus))
                return new List<string>();
            
            currentStatus = currentStatus.Trim();
            
            if (currentStatus.Equals("Đặt hàng thành công", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đang chờ xử lý", "Đang chuẩn bị hàng" };
            if (currentStatus.Equals("Đang chờ xử lý", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đã thanh toán", "Đang chuẩn bị hàng" };
            if (currentStatus.Equals("Đã thanh toán", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đang chuẩn bị hàng" };
            if (currentStatus.Equals("Đang chuẩn bị hàng", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đã giao cho đơn vị vận chuyển" };
            if (currentStatus.Equals("Đã giao cho đơn vị vận chuyển", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đơn hàng sẽ sớm được giao đến bạn" };
            if (currentStatus.Equals("Đơn hàng sẽ sớm được giao đến bạn", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đã giao" };
            if (currentStatus.Equals("Đã giao", StringComparison.OrdinalIgnoreCase))
                return new List<string> { "Đã trả hàng" };
            
            return new List<string>();
        }

        public static bool CanCancelOrder(string status)
        {
            if (string.IsNullOrWhiteSpace(status))
                return false;
            
            status = status.Trim();
            
            return status.Equals("Đặt hàng thành công", StringComparison.OrdinalIgnoreCase)
                || status.Equals("Đang chờ xử lý", StringComparison.OrdinalIgnoreCase)
                || status.Equals("Đã thanh toán", StringComparison.OrdinalIgnoreCase)
                || status.Equals("Đang chuẩn bị hàng", StringComparison.OrdinalIgnoreCase);
        }
    }
}