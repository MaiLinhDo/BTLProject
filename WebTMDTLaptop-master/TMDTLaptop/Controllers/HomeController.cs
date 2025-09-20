using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Mail;
using System.Net;
using System.Web;
using System.Web.Mvc;
using TMDTLaptop.Models;
using TMDTLaptop.Models.Class;
using System.Web.Services.Description;
using System.Data.Entity;
using Microsoft.Owin.Security;
using Microsoft.Owin.Security.Google;
using System.Security.Claims;
using Newtonsoft.Json.Linq;
using System.Net.Http;
using System.Diagnostics;
using Newtonsoft.Json;
using System.Threading.Tasks;
using System.Net.Http.Headers;
using System.Text;
using System.Net.Sockets;
using System.IO;
namespace TMDTLaptop.Controllers
{
    public class HomeController : Controller
    {
        
      
        public async Task<ActionResult> Index()
        {
           
            return View();
        }
       
        



    }
}