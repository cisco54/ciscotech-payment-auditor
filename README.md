# CiscoTech Payment Auditor — MVP

Auditoría autorizada de checkout y pasarelas de pago. Diseñado para ejecutarse en PC, VPS o Coolify mediante Docker.

## Alcance del MVP
- Dashboard web básico.
- API REST para crear/consultar auditorías.
- Worker Playwright para inspección de una URL autorizada.
- Detección heurística de proveedores de pago visibles.
- Comprobaciones no destructivas de checkout.
- Evidencias JSON.
- Sin generación de tarjetas financieras reales ni intentos de cobro en producción.

## Ejecutar
```bash
docker compose up --build
```

Dashboard: http://localhost:3000
API: http://localhost:8000/docs

## Variables
Copiar `.env.example` a `.env`.

Para producción, configurar un dominio y secretos en Coolify.