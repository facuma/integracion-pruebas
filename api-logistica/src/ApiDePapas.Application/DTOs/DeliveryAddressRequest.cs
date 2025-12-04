using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace ApiDePapas.Application.DTOs
{
    public class DeliveryAddressRequest
    {
        [JsonPropertyName("street")]
        [Required]
        public string street { get; set; } = string.Empty;

        [JsonPropertyName("number")]
        [Required]
        public int number { get; set; }

        [JsonPropertyName("postal_code")]
        [Required]
        public string postal_code { get; set; } = string.Empty;

        [JsonPropertyName("locality_name")]
        [Required]
        public string locality_name { get; set; } = string.Empty;
    }
}