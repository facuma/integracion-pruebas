using System;

namespace Compras.Application.DTOs
{
    public class UserProfileUpdate
    {
        public string Phone { get; set; } = string.Empty;
        public string Dni { get; set; } = string.Empty;
        public DateTime BirthDate { get; set; }
    }
}
