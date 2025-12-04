using Compras.Application.DTOs;
using Compras.Application.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace Compras.Infrastructure.Services
{
    public class LogisticaService : ILogisticaService
    {
        private readonly HttpClient _httpClient;
        private readonly IConfiguration _configuration;
        private readonly ILogger<LogisticaService> _logger;

        public LogisticaService(HttpClient httpClient, IConfiguration configuration, ILogger<LogisticaService> logger)
        {
            _httpClient = httpClient;
            _configuration = configuration;
            _logger = logger;

            var baseUrl = _configuration["ExternalApis:Logistica:BaseUrl"];

            if (string.IsNullOrEmpty(baseUrl))
            {
                baseUrl = "http://localhost:5002/";
            }

            _httpClient.BaseAddress = new Uri(baseUrl);
            _httpClient.DefaultRequestHeaders.Add("Accept", "application/json");
        }

        private async Task<string> ObtenerTokenKeycloakAsync()
        {
            try
            {
                var tokenEndpoint = _configuration["ExternalApis:Logistica:TokenEndpoint"];
                var clientId = _configuration["ExternalApis:Logistica:ClientId"];
                var clientSecret = _configuration["ExternalApis:Logistica:ClientSecret"];

                var keycloakRequest = new HttpRequestMessage(HttpMethod.Post, tokenEndpoint);
                var collection = new List<KeyValuePair<string, string>>
                {
                    new("grant_type", "client_credentials"),
                    new("client_id", clientId),
                    new("client_secret", clientSecret)
                };
                keycloakRequest.Content = new FormUrlEncodedContent(collection);

                using var tokenClient = new HttpClient();
                var response = await tokenClient.SendAsync(keycloakRequest);

                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    using var doc = JsonDocument.Parse(content);
                    return doc.RootElement.GetProperty("access_token").GetString();
                }

                _logger.LogError($"Fallo Keycloak: {response.StatusCode}");
                return string.Empty;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error conectando a Keycloak");
                return string.Empty;
            }
        }

        private async Task<HttpResponseMessage> SendAuthenticatedRequestAsync(HttpRequestMessage request)
        {
            var token = await ObtenerTokenKeycloakAsync();

            if (!string.IsNullOrEmpty(token))
            {
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            }
            else
            {
                _logger.LogWarning("No se pudo obtener token, intentando request anónimo (probable 401).");
            }

            return await _httpClient.SendAsync(request);
        }

        public async Task<ShippingCostResponse> CalcularCostoEnvioAsync(ShippingCostRequest request)
        {
            try
            {
                _logger.LogInformation("💰 Calculando costo de envío en Logística API...");

                var deliveryAddress = new
                {
                    street = request.DeliveryAddress.Street,
                    number = ExtractStreetNumber(request.DeliveryAddress.Street),
                    postal_code = request.DeliveryAddress.PostalCode,
                    locality_name = request.DeliveryAddress.City
                };
                var productos = request.Products?.Select(p => new { product_id = p.Id, quantity = p.Quantity }).ToList();
                var costoRequest = new { delivery_address = deliveryAddress, products = productos };

                var jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase, WriteIndented = false };
                var json = JsonSerializer.Serialize(costoRequest, jsonOptions);
                _logger.LogInformation($"🧮 JSON para cálculo: {json}");

                var httpRequest = new HttpRequestMessage(HttpMethod.Post, "shipping/cost");
                httpRequest.Content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await SendAuthenticatedRequestAsync(httpRequest);

                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    _logger.LogInformation($"✅ Costo calculado: {responseContent}");

                    var costoApiResponse = JsonSerializer.Deserialize<CostoEnvioApiResponse>(responseContent, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                    return new ShippingCostResponse {
                        Currency = costoApiResponse.currency, TotalCost = (decimal)costoApiResponse.total_cost,
                        TransportType = costoApiResponse.transport_type,
                        Products = costoApiResponse.products?.Select(p => new ProductCost { Id = p.id, Cost = (decimal)p.cost }).ToList() ?? new List<ProductCost>()
                    };
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogWarning($"⚠️ Error calculando costo: {response.StatusCode} - {errorContent}");
                    return CalcularCostoPrueba(request);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "⚠️ Logística API no disponible - Usando cálculo de prueba");
                return CalcularCostoPrueba(request);
            }
        }

        public async Task<CreateShippingResponse> CrearEnvioAsync(CreateShippingRequest request)
        {
            try
            {
                _logger.LogInformation("🚚 CREANDO ENVÍO EN LOGÍSTICA API...");

                var envioRequest = new
                {
                    order_id = request.OrderId,
                    user_id = request.UserId,
                    delivery_address = new
                    {
                        street = request.DeliveryAddress.Street,
                        number = request.DeliveryAddress.Number,
                        postal_code = request.DeliveryAddress.PostalCode,
                        locality_name = request.DeliveryAddress.LocalityName
                    },
                    transport_type = request.TransportType?.ToLower() ?? "truck",
                    products = request.Products?.Select(p => new { id = p.Id, quantity = p.Quantity }).ToList()
                };

                var jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase, WriteIndented = false };
                var json = JsonSerializer.Serialize(envioRequest, jsonOptions);
                _logger.LogInformation($"📦 JSON para creación: {json}");

                var httpRequest = new HttpRequestMessage(HttpMethod.Post, "shipping");
                httpRequest.Content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await SendAuthenticatedRequestAsync(httpRequest);

                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    _logger.LogInformation($"🎉 ¡ENVÍO CREADO EXITOSAMENTE!: {responseContent}");

                    try
                    {
                         var envioApiResponse = JsonSerializer.Deserialize<EnvioCreadoApiResponse>(responseContent, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                         decimal shippingCost = await ObtenerCostoEstimadoAsync(request);

                         return new CreateShippingResponse
                         {
                             ShippingId = envioApiResponse.shipping_id, Status = envioApiResponse.status,
                             TransportType = envioApiResponse.transport_type, EstimatedDeliveryAt = envioApiResponse.estimated_delivery_at,
                             ShippingCost = shippingCost
                         };
                    }
                    catch (JsonException jsonEx)
                    {
                        _logger.LogWarning(jsonEx, "⚠️ Error deserializando respuesta real");
                        return GenerateFallbackResponse(request, "Error de deserialización");
                    }
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogError($"❌ ERROR CREANDO ENVÍO: {response.StatusCode} - {errorContent}");
                    return GenerateFallbackResponse(request, errorContent);
                }
            }
            catch (HttpRequestException httpEx)
            {
                 _logger.LogError(httpEx, "💥 Error de conexión con Logística API");
                 return GenerateFallbackResponse(request, "Error de conexión");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "💥 Error inesperado en CrearEnvioAsync");
                return GenerateFallbackResponse(request, $"Error interno: {ex.Message}");
            }
        }

        public async Task<ShippingDetail> ObtenerSeguimientoAsync(int shippingId)
        {
            try
            {
                _logger.LogInformation($"🔍 Obteniendo seguimiento para envío {shippingId}...");

                var httpRequest = new HttpRequestMessage(HttpMethod.Get, $"shipping/{shippingId}");
                var response = await SendAuthenticatedRequestAsync(httpRequest);

                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();

                    var seguimientoApiResponse = JsonSerializer.Deserialize<ShippingDetailApiResponse>(responseContent, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                    return new ShippingDetail 
                    { 
                        ShippingId = seguimientoApiResponse.shipping_id, Status = seguimientoApiResponse.status,
                        EstimatedDeliveryAt = seguimientoApiResponse.estimated_delivery_at, TrackingNumber = seguimientoApiResponse.tracking_number,
                        CarrierName = seguimientoApiResponse.carrier_name
                    };
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogWarning($"⚠️ Error obteniendo seguimiento: {response.StatusCode} - {errorContent}");
                    return ObtenerSeguimientoPrueba(shippingId);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, $"⚠️ Error obteniendo seguimiento {shippingId} - Usando datos de prueba");
                return ObtenerSeguimientoPrueba(shippingId);
            }
        }

        public async Task<List<TransportMethod>> ObtenerMetodosTransporteAsync()
        {
            try
            {
                _logger.LogInformation("🚛 Obteniendo métodos de transporte...");

                var httpRequest = new HttpRequestMessage(HttpMethod.Get, "shipping/transport-methods");
                var response = await SendAuthenticatedRequestAsync(httpRequest);

                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();

                    var transportMethods = JsonSerializer.Deserialize<TransportMethodsApiResponse>(responseContent, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                    _logger.LogInformation($"✅ {transportMethods.transport_methods?.Count ?? 0} métodos obtenidos");

                    return transportMethods.transport_methods?.Select(t => new TransportMethod { Type = t.type, Name = t.name, EstimatedDays = t.estimated_days }).ToList() ?? GetTransportMethodsDefault();
                }
                else
                {
                    _logger.LogWarning("⚠️ Error obteniendo métodos - Usando métodos por defecto");
                    return GetTransportMethodsDefault();
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "⚠️ Error obteniendo métodos de transporte - Usando por defecto");
                return GetTransportMethodsDefault();
            }
        }

        private async Task<decimal> ObtenerCostoEstimadoAsync(CreateShippingRequest request)
        {
            try
            {
                var costoRequest = new ShippingCostRequest
                {
                    DeliveryAddress = new Address
                    {
                        Street = request.DeliveryAddress.Street,
                        City = request.DeliveryAddress.LocalityName,
                        PostalCode = request.DeliveryAddress.PostalCode,
                        State = "", 
                        Country = "AR"
                    },
                    Products = request.Products?.Select(p => new ProductRequest
                    {
                        Id = p.Id,
                        Quantity = p.Quantity
                    }).ToList() ?? new List<ProductRequest>()
                };

                var costoResponse = await CalcularCostoEnvioAsync(costoRequest);
                return costoResponse.TotalCost;
            }
            catch
            {
                return CalculateRealisticShippingCost(request.Products, request.TransportType);
            }
        }

        private CreateShippingResponse GenerateFallbackResponse(CreateShippingRequest request, string reason)
        {
            _logger.LogWarning($"🔄 Usando respuesta de respaldo: {reason}");

            var random = new Random();
            return new CreateShippingResponse
            {
                ShippingId = 900000 + random.Next(1000, 9999),
                Status = "created_fallback",
                TransportType = request.TransportType,
                EstimatedDeliveryAt = DateTime.UtcNow.AddDays(3).ToString("yyyy-MM-ddTHH:mm:ssZ"),
                ShippingCost = CalculateRealisticShippingCost(request.Products, request.TransportType)
            };
        }

        private decimal CalculateRealisticShippingCost(List<ShippingProduct> products, string transportType)
        {
            var baseCost = transportType?.ToLower() switch
            {
                "air" => 5000.00m,
                "plane" => 5000.00m,
                "truck" => 3000.00m,
                "ship" => 2000.00m,
                "boat" => 2000.00m,
                _ => 3000.00m
            };

            var itemsCost = (products?.Sum(p => p.Quantity * 100) ?? 100);
            var distanceCost = 2000.00m;

            return baseCost + itemsCost + distanceCost;
        }

        private int ExtractStreetNumber(string street)
        {
            if (string.IsNullOrEmpty(street))
                return 0;

            var match = Regex.Match(street, @"\d+");
            if (match.Success && int.TryParse(match.Value, out int number))
            {
                return number <= 9999 ? number : 0;
            }

            return 0;
        }
        
        private List<TransportMethod> GetTransportMethodsDefault()
        {
            return new List<TransportMethod>
            {
                new TransportMethod { Type = "truck", Name = "Camión", EstimatedDays = "3-5" },
                new TransportMethod { Type = "plane", Name = "Avión", EstimatedDays = "1-2" },
                new TransportMethod { Type = "ship", Name = "Barco", EstimatedDays = "7-10" }
            };
        }

        private ShippingCostResponse CalcularCostoPrueba(ShippingCostRequest request)
        {
            return new ShippingCostResponse
            {
                Currency = "ARS",
                TotalCost = 6878.5M,
                TransportType = "truck",
                Products = request.Products.Select(p => new ProductCost
                {
                    Id = p.Id,
                    Cost = p.Quantity * 100.0M
                }).ToList()
            };
        }

        private ShippingDetail ObtenerSeguimientoPrueba(int shippingId)
        {
            return new ShippingDetail
            {
                ShippingId = shippingId,
                Status = "in_transit",
                EstimatedDeliveryAt = DateTime.UtcNow.AddDays(3).ToString("yyyy-MM-ddTHH:mm:ssZ"),
                TrackingNumber = $"TRACK-{shippingId}",
                CarrierName = "Transporte Local SA"
            };
        }

        private class CostoEnvioApiResponse
        {
            public string currency { get; set; }
            public float total_cost { get; set; }
            public string transport_type { get; set; }
            public List<ProductoCostoApi> products { get; set; }
        }

        private class ProductoCostoApi
        {
            public int id { get; set; }
            public float cost { get; set; }
        }

        private class EnvioCreadoApiResponse
        {
            public int shipping_id { get; set; }
            public string status { get; set; }
            public string transport_type { get; set; }
            public string estimated_delivery_at { get; set; }
        }

        private class ShippingDetailApiResponse
        {
            public int shipping_id { get; set; }
            public string status { get; set; }
            public string estimated_delivery_at { get; set; }
            public string tracking_number { get; set; }
            public string carrier_name { get; set; }
            public string transport_type { get; set; } 
            public float? total_cost { get; set; } 
            public string currency { get; set; }
        }

        private class TransportMethodsApiResponse
        {
            public List<TransportMethodApi> transport_methods { get; set; }
        }

        private class TransportMethodApi
        {
            public string? type { get; set; }
            public string? name { get; set; }
            public string? estimated_days { get; set; }
        }
    }
}
