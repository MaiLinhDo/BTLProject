using System;
using System.Collections.Generic;
using System.Data;
using System.Data.Entity;
using System.Data.Entity.Infrastructure;
using System.Drawing.Printing;
using System.IO;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using System.Web.UI;
using TMDTLaptop.Models;
using TMDTLaptop.Models.Class;
using OfficeOpenXml;
using Newtonsoft.Json;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
namespace TMDTLaptop.Controllers
{
    public class AdminController : Controller
    {
     
       
        // GET: Admin
        public async Task<ActionResult> Index()
        {
         
            return View();
        }






    }
}