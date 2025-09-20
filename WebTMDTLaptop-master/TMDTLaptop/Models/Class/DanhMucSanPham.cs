using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace TMDTLaptop.Models.Class
{
    public partial class DanhMucSanPham
    {
  

        public int MaDanhMuc { get; set; }
        public string TenDanhMuc { get; set; }
        public Nullable<bool> TrangThai { get; set; }
        public Nullable<System.DateTime> NgayTao { get; set; }

    }
}