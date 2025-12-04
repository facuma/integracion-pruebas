# Dockerfile
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy csproj files and restore as distinct layers
COPY ["src/Compras.Api/Compras.Api.csproj", "src/Compras.Api/"]
COPY ["src/Compras.Application/Compras.Application.csproj", "src/Compras.Application/"]
COPY ["src/Compras.Domain/Compras.Domain.csproj", "src/Compras.Domain/"]
COPY ["src/Compras.Infrastructure/Compras.Infrastructure.csproj", "src/Compras.Infrastructure/"]

RUN dotnet restore "src/Compras.Api/Compras.Api.csproj"

# Copy everything else and build
COPY . .
WORKDIR "/src/src/Compras.Api"
RUN dotnet build "Compras.Api.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Compras.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .
EXPOSE 80
ENTRYPOINT ["dotnet", "Compras.Api.dll"]