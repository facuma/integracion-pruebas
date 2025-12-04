using System;
using System.Collections.Generic;

namespace Compras.Domain.Entities
{
    public class Order
    {
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public string Status { get; set; } // confirmed, shipped, delivered, cancelled
        public decimal Total { get; set; }
        public int UserId { get; set; }

        public int? ReservaId { get; set; } // ID de reserva en Stock API
        public int? ShippingId { get; set; } // ID de envío en Logística API

        public ICollection<CartItem> Items { get; set; } = new List<CartItem>();

        public string TrackingInfo { get; set; }
    }
}
