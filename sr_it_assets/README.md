# sr_it_assets — Somos Reyes Activos TI

Versión inicial para Odoo 18 Enterprise / Odoo.sh.

## Dependencias
- maintenance
- hr_maintenance
- stock

`stock` se declara explícitamente porque Odoo 18 ha tenido incidencias conocidas donde la ficha de equipo consulta `stock.lot` al trabajar con Mantenimiento/RRHH.

## Alcance v1
- Extensión de `maintenance.equipment`
- Folio `SR-[PREFIJO]-00000` por categoría
- Catálogos administrables
- Perfiles y atributos técnicos configurables
- Componentes serializados
- Interfaces de red
- Referencia Vaultwarden sin secretos
- Verificación documental
- Vistas Form/List/Kanban
- Grupos de seguridad

## Instalación / prueba
1. Copiar `sr_it_assets` al repositorio de addons personalizados.
2. Commit/push a la rama conectada al ambiente TEST de Odoo.sh.
3. Actualizar lista de Apps.
4. Instalar **Somos Reyes - Activos TI**.
5. Asignar el grupo **Administrador Activos TI** al usuario de pruebas.
6. Configurar las categorías existentes de Mantenimiento con prefijo y perfiles.
7. Crear activos piloto y ejecutar los casos de prueba de RF-ACT-001.

## Importante
Este paquete es una primera implementación para TEST. Antes de producción el desarrollador debe revisar los XML IDs heredados contra la compilación exacta de Odoo 18 de Somos Reyes y cualquier módulo personalizado ya instalado.
