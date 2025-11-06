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
                case "Đang chuẩn bị hàng": return "badge-info";
                case "Đã giao cho đơn vị vận chuyển": return "badge-warning";
                case "Đơn hàng sẽ sớm được giao đến bạn": return "badge-secondary";
                case "Đã giao": return "badge-success";
                case "Đã hủy": return "badge-danger";
                case "Đã trả hàng": return "badge-dark";
                default: return "badge-secondary";
            }
        }

        public static List<string> GetNextValidStatuses(string currentStatus)
        {
            switch (currentStatus)
            {
                case "Đặt hàng thành công":
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
                    return new List<string>();
            }
        }

        public static bool CanCancelOrder(string status)
        {
            return status == "Đặt hàng thành công" || status == "Đang chuẩn bị hàng";
        }
    }
}