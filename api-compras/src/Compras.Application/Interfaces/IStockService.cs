using Compras.Application.DTOs;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Compras.Application.Interfaces
{
    public interface IStockService
    {
        Task<ReservaOutput> CrearReservaAsync(ReservaInput reserva);
        Task<bool> CancelarReservaAsync(int idReserva, string motivo);
        Task<ProductoStock> GetProductoAsync(int productoId);
        Task<List<ProductoStock>> GetAllProductsAsync();
        Task<ProductoStock> GetProductByIdAsync(int id);
    }
}
