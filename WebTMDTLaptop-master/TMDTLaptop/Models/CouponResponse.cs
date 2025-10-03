using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using TMDTLaptop.Models.Class;

namespace TMDTLaptop.Models
{

    public class CouponResponse
    {
        public bool success { get; set; }
        public string message { get; set; }
        public Voucher coupon { get; set; }
    }
}