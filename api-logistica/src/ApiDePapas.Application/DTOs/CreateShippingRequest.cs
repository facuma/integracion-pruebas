using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

using ApiDePapas.Domain.Entities;

namespace ApiDePapas.Application.DTOs
{
    public class CreateShippingRequest
    {
        [JsonPropertyName("order_id")]
        [Required]
        public int order_id { get; set; }

        [JsonPropertyName("user_id")]
        [Required]
        public int user_id { get; set; }

        [JsonPropertyName("delivery_address")]
        [Required]
        public DeliveryAddressRequest delivery_address { get; set; } = null!;

        [JsonPropertyName("transport_type")]
        [Required]
        public TransportType transport_type { get; set; }

        [JsonPropertyName("products")]
        [Required]
        public List<ProductRequest> products { get; set; } = new();
    }
}