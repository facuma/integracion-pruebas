using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ComprasAPI.Data;
using ComprasAPI.Models;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Net.Http.Headers;

namespace ComprasAPI.Controllers
{
    [ApiController]
    [Route("api/auth/register")]
    public class RegisterController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;

        public RegisterController(ApplicationDbContext context, IHttpClientFactory httpClientFactory, IConfiguration configuration)
        {
            _context = context;
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
        }

        [HttpPost]
        public async Task<IActionResult> Register(RegisterRequest request)
        {
            if (request.Password != request.RepeatPassword)
                return BadRequest(new { error = "Las contraseñas no coinciden" });

            if (await _context.Users.AnyAsync(u => u.Email == request.Email))
                return Conflict(new { error = "El correo ya está registrado" });

            try
            {
                // 1️⃣ Crear usuario en Keycloak
                var token = await GetAdminToken();
                if (token == null)
                    return StatusCode(500, new { error = "No se pudo obtener el token de administrador de Keycloak" });

                var client = _httpClientFactory.CreateClient();

                var userPayload = new
                {
                    username = request.Email,
                    email = request.Email,
                    enabled = true,
                    firstName = request.FirstName,
                    lastName = request.LastName,
                    credentials = new[]
                    {
                        new { type = "password", value = request.Password, temporary = false }
                    }
                    Email = request.Email,
                    PasswordHash = HashPassword(request.Password),
                    CreatedAt = DateTime.UtcNow
                };

                _context.Users.Add(user);
                await _context.SaveChangesAsync();

                return Ok(new { message = "Usuario registrado correctamente" });
            }
            catch (Exception ex)
            {
                // Log the exception
                return StatusCode(500, new { error = "Error interno del servidor", details = ex.Message });
            }
        }

        // 🔐 Obtener token admin de Keycloak
                    var errorContent = await response.Content.ReadAsStringAsync();
                    Console.WriteLine($"Keycloak token error: {response.StatusCode} - {errorContent}");
                    return null;
                }

                var json = await response.Content.ReadAsStringAsync();
                using var doc = JsonDocument.Parse(json);
                return doc.RootElement.GetProperty("access_token").GetString();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception in GetAdminToken: {ex.Message}");
                return null;
            }
        }

        private string HashPassword(string password)
        {
            using var sha256 = SHA256.Create();
            var bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
            return Convert.ToBase64String(bytes);
        }
    }
}