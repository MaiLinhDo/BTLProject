using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
	public class Voucher
	{
        public int MaVoucher { get; set; }
        public string Code { get; set; }
        public Nullable<decimal> GiamGia { get; set; }
        public Nullable<System.DateTime> NgayBatDau { get; set; }
        public Nullable<System.DateTime> NgayKetThuc { get; set; }
        public int SoLuongSuDung { get; set; }
        public int SoLuongSuDungToiDa { get; set; }
        public Nullable<bool> TrangThai { get; set; }
        public string MoTa { get; set; }
    }
}