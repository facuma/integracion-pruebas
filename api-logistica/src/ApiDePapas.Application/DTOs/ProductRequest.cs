using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace ApiDePapas.Application.DTOs
{
    public class ProductRequest
    {
        [JsonPropertyName("id")]
        [Required]
        public int id { get; set; }

        [JsonPropertyName("quantity")]
        [Required]
        [Range(1, int.MaxValue, ErrorMessage = "Quantity must be at least 1")]
        public int quantity { get; set; }
    }
}