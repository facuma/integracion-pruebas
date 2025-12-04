using ComprasAPI.Controllers;
using ComprasAPI.Data;
using ComprasAPI.Models;
using ComprasAPI.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using Microsoft.OpenApi.Models;


var builder = WebApplication.CreateBuilder(args);

// Configuración JWT en appsettings.json
// Asegurarse de que estas claves existan en appsettings.json
var jwtSettings = builder.Configuration.GetSection("Jwt");
var jwtKey = jwtSettings["Key"] ?? "ClaveSuperSecreta123456789";
var jwtIssuer = jwtSettings["Issuer"] ?? "https://localhost:7248";
var jwtAudience = jwtSettings["Audience"] ?? "https://localhost:7248";

// ✅ 1. CONFIGURAR STOCK SERVICE
builder.Services.AddHttpClient<IStockService, StockService>(client =>
{
    client.BaseAddress = new Uri("http://localhost:3000/");
    client.Timeout = TimeSpan.FromSeconds(30);
});

// ✅ 2. CONFIGURAR LOGÍSTICA SERVICE
builder.Services.AddHttpClient<ILogisticaService, LogisticaService>((provider, client) =>
{
    var config = provider.GetRequiredService<IConfiguration>();
    var logisticaApiUrl = config["ExternalApis:Logistica:BaseUrl"] ?? "http://localhost:5002";

    client.BaseAddress = new Uri(logisticaApiUrl);
    client.Timeout = TimeSpan.FromSeconds(30);
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

// ✅ 3. REGISTRAR SERVICIOS
builder.Services.AddScoped<IStockService, StockService>();
builder.Services.AddScoped<ILogisticaService, LogisticaService>();

// AÑADIR JWT LOCAL (Bypass Keycloak para Auth entrante)
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = jwtIssuer,
            ValidAudience = jwtAudience,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ClockSkew = TimeSpan.Zero
        };
    });

builder.Services.AddControllers();

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseMySql(builder.Configuration.GetConnectionString("DefaultConnection"),
    new MySqlServerVersion(new Version(8, 0, 36))));

// Agregar CORS al inicio, después de builder.Services
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAngular",
        policy =>
        {
            policy.WithOrigins("https://localhost:4200", "http://localhost:4200")
                  .AllowAnyHeader()
                  .AllowAnyMethod()
                  .AllowCredentials();
        });
});

// ----------------------
// [Swagger] Servicios
// ----------------------
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// ✅ EJECUTAR MIGRACIONES AUTOMÁTICAMENTE AL INICIAR
try
{
    Console.WriteLine("🔧 Iniciando verificación de migraciones...");

    using (var scope = app.Services.CreateScope())
    {
        var services = scope.ServiceProvider;
        var context = services.GetRequiredService<ApplicationDbContext>();

        // Verificar si podemos conectar a la base de datos
        if (await context.Database.CanConnectAsync())
        {
            Console.WriteLine("✅ Base de datos conectada exitosamente");

            // Verificar si hay migraciones pendientes
            var pendingMigrations = await context.Database.GetPendingMigrationsAsync();
            if (pendingMigrations.Any())
            {
                Console.WriteLine($"🔧 Aplicando {pendingMigrations.Count()} migraciones pendientes...");
                foreach (var migration in pendingMigrations)
                {
                    Console.WriteLine($"   - {migration}");
                }

                await context.Database.MigrateAsync();
                Console.WriteLine("✅ Todas las migraciones aplicadas correctamente");
            }
            else
            {
                Console.WriteLine("✅ No hay migraciones pendientes");
            }

            // Verificar si la tabla Users existe y tiene datos
            try
            {
                var userCount = await context.Users.CountAsync();
                Console.WriteLine($"✅ Tabla Users existe y tiene {userCount} registros");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error al acceder a la tabla Users: {ex.Message}");
                Console.WriteLine("💡 Esto puede ser normal si la tabla está vacía o recién creada");
            }
        }
        else
        {
            Console.WriteLine("❌ No se pudo conectar a la base de datos");
        }
    }
}
catch (Exception ex)
{
    Console.WriteLine($"⚠️ Error durante la verificación de migraciones: {ex.Message}");
    Console.WriteLine("💡 La aplicación continuará iniciando...");
}

app.UseCors("AllowAngular");

// ----------------------
// [Swagger] Middleware
// ----------------------
app.UseSwagger(c =>
    {
    c.PreSerializeFilters.Add((swaggerDoc, httpReq) =>
    {
        swaggerDoc.Servers = new List<OpenApiServer> 
        { 
            new OpenApiServer { Url = "/compras" } 
        };
    });
    });
app.UseSwaggerUI();

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

Console.WriteLine("🚀 Aplicación ComprasAPI iniciada correctamente");
app.Run();