using Compras.Application.DTOs;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Compras.Application.Interfaces
{
    public interface ILogisticaService
    {
        Task<ShippingCostResponse> CalcularCostoEnvioAsync(ShippingCostRequest request);
        Task<CreateShippingResponse> CrearEnvioAsync(CreateShippingRequest request);
        Task<ShippingDetail> ObtenerSeguimientoAsync(int shippingId);
        Task<List<TransportMethod>> ObtenerMetodosTransporteAsync();
    }
}
