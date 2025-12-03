// jwt-auth.guard.ts (modificado)
import { Injectable, ExecutionContext, UnauthorizedException, Logger } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { Observable } from 'rxjs';
import * as dns from 'dns';
import { promisify } from 'util';

const lookup = promisify(dns.lookup);

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  private readonly logger = new Logger(JwtAuthGuard.name);

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const clientIp = request.ip || request.connection.remoteAddress;

    // Lista de IPs permitidas (localhost por defecto)
    // Nota: ::ffff:127.0.0.1 es la versión IPv6 mapeada de localhost
    const allowedIps = ['127.0.0.1', '::1', '::ffff:127.0.0.1'];

    // Agregar IPs/Hostnames desde variable de entorno
    if (process.env.INTERNAL_API_IPS) {
      const items = process.env.INTERNAL_API_IPS.split(',').map(i => i.trim());

      for (const item of items) {
        // Si parece una IP, la agregamos directamente
        if (this.isIp(item)) {
          allowedIps.push(item);
        } else {
          // Si no, intentamos resolver el hostname (para Docker containers)
          try {
            const { address } = await lookup(item);
            if (address) {
              allowedIps.push(address);
              // También agregar versión IPv6 mapeada si es IPv4
              if (address.includes('.')) {
                allowedIps.push(`::ffff:${address}`);
              }
            }
          } catch (e) {
            this.logger.warn(`Could not resolve hostname: ${item}`);
          }
        }
      }
    }

    this.logger.log(`Incoming request from IP: ${clientIp}`);
    // this.logger.debug(`Allowed IPs: ${JSON.stringify(allowedIps)}`);

    // Verificar si la IP está en la lista blanca
    if (allowedIps.includes(clientIp)) {
      this.logger.log(`Bypassing auth for internal IP: ${clientIp}`);

      // Inyectar usuario de sistema para pasar ScopesGuard
      request.user = {
        sub: 'system-internal',
        username: 'system',
        scope: 'reservas:read reservas:write products:read products:write'
      };

      return true;
    }

    // Si no es IP interna, proceder con validación JWT normal
    return super.canActivate(context) as Promise<boolean>;
  }

  handleRequest(err: any, user: any, info: any) {
    if (err || !user) {
      throw new UnauthorizedException('Token inválido o no proporcionado');
    }
    return user;
  }

  private isIp(value: string): boolean {
    // Check simple IPv4 or IPv6 format
    return /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(value) || value.includes(':');
  }
}