using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Compras.Infrastructure.Data;
using Compras.Domain.Entities;
using Compras.Application.DTOs;
using Compras.Application.Interfaces;
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;

namespace Compras.Api.Controllers
{
    [ApiController]
    [Route("api/shopcart")]
    public class OrderController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly IStockService _stockService;
        private readonly ILogisticaService _logisticaService;
        private readonly ILogger<OrderController> _logger;

        public OrderController(
            ApplicationDbContext context,
            IStockService stockService,
            ILogisticaService logisticaService,
            ILogger<OrderController> logger)
        {
            _context = context;
            _stockService = stockService;
            _logisticaService = logisticaService;
            _logger = logger;
        }

        // GET: api/shopcart/transport-methods
        [HttpGet("transport-methods")]
        public async Task<IActionResult> GetTransportMethods()
        {
            try
            {
                _logger.LogInformation(" Obteniendo métodos de transporte...");
                var methods = await _logisticaService.ObtenerMetodosTransporteAsync();
                return Ok(methods);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, " Error obteniendo métodos de transporte");
                return StatusCode(500, new
                {
                    error = "Error obteniendo métodos de transporte",
                    code = "TRANSPORT_METHODS_ERROR"
                });
            }
        }

        // GET: api/shopcart/history
        [HttpGet("history")]
        [Authorize]
        public async Task<IActionResult> GetOrderHistory()
        {
            try
            {
                var userId = await GetCurrentUserId();
                if (userId == null)
                    return Unauthorized(new { error = "No autorizado", code = "UNAUTHORIZED" });

                var orders = await _context.Orders
                    .Include(o => o.Items)
                    .ThenInclude(i => i.Product)
                    .Where(o => o.UserId == userId.Value)
                    .OrderByDescending(o => o.Date)
                    .ToListAsync();

                return Ok(orders);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, " Error obteniendo historial de pedidos");
                return StatusCode(500, new
                {
                    error = "Error interno del servidor",
                    code = "INTERNAL_ERROR"
                });
            }
        }

        // GET: api/shopcart/history/{id}
        [HttpGet("history/{id}")]
        [Authorize]
        public async Task<IActionResult> GetOrderDetails(int id)
        {
            try
            {
                var userId = await GetCurrentUserId();
                if (userId == null)
                    return Unauthorized(new { error = "No autorizado", code = "UNAUTHORIZED" });

                var order = await _context.Orders
                    .Include(o => o.Items)
                    .ThenInclude(i => i.Product)
                    .FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId.Value);

                if (order == null)
                    return NotFound(new { error = "Pedido no encontrado", code = "ORDER_NOT_FOUND" });

                // Obtener información de seguimiento si existe shippingId
                if (order.ShippingId.HasValue)
                {
                    try
                    {
                        var tracking = await _logisticaService.ObtenerSeguimientoAsync(order.ShippingId.Value);
                        order.TrackingInfo = System.Text.Json.JsonSerializer.Serialize(tracking);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, " No se pudo obtener información de seguimiento");
                    }
                }

                return Ok(order);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $" Error obteniendo detalles del pedido {id}");
                return StatusCode(500, new
                {
                    error = "Error interno del servidor",
                    code = "INTERNAL_ERROR"
                });
            }
        }

        private async Task<int?> GetCurrentUserId()
        {
            try
            {
                var email = User.FindFirst(ClaimTypes.Email)?.Value
                           ?? User.FindFirst("email")?.Value
                           ?? User.FindFirst("preferred_username")?.Value;

                if (string.IsNullOrEmpty(email))
                    return null;

                var user = await _context.Users
                    .FirstOrDefaultAsync(u => u.Email == email);

                if (user == null)
                {
                    user = new User
                    {
                        Email = email,
                        FirstName = User.FindFirst(ClaimTypes.GivenName)?.Value ?? "Usuario",
                        LastName = User.FindFirst(ClaimTypes.Surname)?.Value ?? "Keycloak",
                        PasswordHash = "keycloak_user",
                        CreatedAt = DateTime.UtcNow
                    };

                    _context.Users.Add(user);
                    await _context.SaveChangesAsync();
                }

                return user.Id;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, " Error al obtener userId");
                return 1; // Fallback para desarrollo
            }
        }
    }
}
