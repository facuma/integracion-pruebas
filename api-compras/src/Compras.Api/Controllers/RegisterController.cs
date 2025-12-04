using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Compras.Infrastructure.Data;
using Compras.Domain.Entities;
using Compras.Application.DTOs;
using System.Security.Cryptography;
using System.Text;

namespace Compras.Api.Controllers
{
    [ApiController]
    [Route("api/auth/register")]
    public class RegisterController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public RegisterController(ApplicationDbContext context)
        {
            _context = context;
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
                // ⚠️ BYPASS KEYCLOAK: Guardar DIRECTAMENTE en base de datos local
                // Se eliminó la lógica de Keycloak por solicitud del usuario.
                
                var user = new User
                {
                    FirstName = request.FirstName,
                    LastName = request.LastName,
                    Email = request.Email,
                    PasswordHash = HashPassword(request.Password),
                    CreatedAt = DateTime.UtcNow
                };

                _context.Users.Add(user);
                await _context.SaveChangesAsync();

                return Ok(new { message = "Usuario registrado correctamente (Local DB Only)" });
            }
            catch (Exception ex)
            {
                // Log the exception
                return StatusCode(500, new { error = "Error interno del servidor", details = ex.Message });
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
