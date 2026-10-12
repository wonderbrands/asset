import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    sr_prefix = fields.Char(
        string='Prefijo SR',
        copy=False
    )
    sr_profile_ids = fields.Many2many(
        'sr.asset.profile',
        string='Perfiles técnicos'
    )
    sr_serial_required = fields.Boolean(
        string='Serie requerida'
    )
    sr_allow_assignment = fields.Boolean(
        string='Permitir asignación',
        default=True
    )
    sr_allow_components = fields.Boolean(
        string='Permitir componentes',
        default=True
    )
    sr_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia SR',
        copy=False,
        readonly=True
    )

    _sql_constraints = [
        (
            'sr_prefix_unique',
            'unique(sr_prefix)',
            'El prefijo SR debe ser único.'
        ),
    ]

    @api.constrains('sr_prefix')
    def _check_sr_prefix(self):
        for rec in self:
            if (
                rec.sr_prefix
                and not re.fullmatch(r'[A-Z0-9]{2,5}', rec.sr_prefix)
            ):
                raise ValidationError(
                    _(
                        'El prefijo debe tener de 2 a 5 caracteres, '
                        'sólo mayúsculas y números.'
                    )
                )

    def write(self, vals):
        if 'sr_prefix' in vals:
            for rec in self:
                new = (vals.get('sr_prefix') or '').strip().upper()

                if rec.sr_prefix and new != rec.sr_prefix:
                    used = self.env[
                        'maintenance.equipment'
                    ].search_count([
                        ('category_id', '=', rec.id),
                        ('sr_asset_code', '!=', False),
                    ])

                    if used:
                        raise UserError(
                            _(
                                'No puede cambiar el prefijo porque '
                                'la categoría ya emitió folios.'
                            )
                        )

            vals['sr_prefix'] = (
                vals.get('sr_prefix') or ''
            ).strip().upper()

        return super().write(vals)

    def _sr_get_or_create_sequence(self):
        self.ensure_one()

        if not self.sr_prefix:
            raise UserError(
                _('La categoría no tiene un prefijo SR configurado.')
            )

        if not self.sr_sequence_id:
            seq = self.env['ir.sequence'].sudo().create({
                'name': f'Activos SR - {self.name}',
                'code': f'sr.it.asset.{self.id}',
                'prefix': f'SR-{self.sr_prefix}-',
                'padding': 5,
                'company_id': (
                    self.company_id.id
                    if self.company_id
                    else False
                ),
            })

            self.sudo().sr_sequence_id = seq

        return self.sr_sequence_id


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    sr_asset_code = fields.Char(
        string='ID Activo',
        copy=False,
        readonly=True,
        index=True,
        tracking=True
    )
    sr_brand_id = fields.Many2one(
        'sr.asset.brand',
        string='Marca',
        tracking=True
    )
    sr_physical_state_id = fields.Many2one(
        'sr.asset.physical.state',
        string='Estado físico',
        tracking=True
    )
    sr_operational_state_id = fields.Many2one(
        'sr.asset.operational.state',
        string='Estado operativo',
        tracking=True
    )
    sr_condition_id = fields.Many2one(
        'sr.asset.condition',
        string='Condición',
        tracking=True
    )
    sr_ownership_type_id = fields.Many2one(
        'sr.asset.ownership.type',
        string='Propiedad',
        tracking=True
    )
    sr_hostname = fields.Char(
        string='Hostname',
        index=True
    )
    sr_vault_ref = fields.Char(
        string='Referencia Vaultwarden'
    )
    sr_document_state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('complete', 'Completo'),
            ('verified', 'Verificado'),
        ],
        string='Estado documental',
        default='pending',
        required=True,
        tracking=True
    )
    sr_last_verified = fields.Datetime(
        string='Última verificación',
        readonly=True,
        tracking=True
    )
    sr_verified_by = fields.Many2one(
        'res.users',
        string='Verificado por',
        readonly=True
    )
    sr_it_notes = fields.Text(
        string='Observaciones TI'
    )
    sr_attribute_value_ids = fields.One2many(
        'sr.asset.attribute.value',
        'equipment_id',
        string='Información técnica',
        copy=True
    )
    sr_component_ids = fields.One2many(
        'sr.asset.component',
        'equipment_id',
        string='Componentes',
        copy=True
    )
    sr_network_interface_ids = fields.One2many(
        'sr.asset.network.interface',
        'equipment_id',
        string='Interfaces de red',
        copy=True
    )
    sr_is_assigned = fields.Boolean(
        compute='_compute_sr_is_assigned',
        string='Asignado'
    )

    _sql_constraints = [
        (
            'sr_asset_code_unique',
            'unique(sr_asset_code)',
            'El ID de activo debe ser único.'
        ),
    ]

    @api.depends(
        'employee_id',
        'department_id',
        'owner_user_id'
    )
    def _compute_sr_is_assigned(self):
        for rec in self:
            rec.sr_is_assigned = bool(
                rec.employee_id
                or rec.department_id
                or rec.owner_user_id
            )

    def _sr_sync_attribute_lines(self):
        for rec in self:
            if not rec.category_id:
                continue

            wanted = (
                rec.category_id
                .sr_profile_ids
                .mapped('attribute_ids')
                .filtered('active')
            )

            existing = (
                rec.sr_attribute_value_ids
                .mapped('attribute_id')
            )

            for attr in wanted - existing:
                self.env['sr.asset.attribute.value'].create({
                    'equipment_id': rec.id,
                    'attribute_id': attr.id,
                })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            rec._sr_assign_code_if_needed()
            rec._sr_sync_attribute_lines()

        return records

    def write(self, vals):
        result = super().write(vals)

        if 'category_id' in vals:
            for rec in self:
                rec._sr_assign_code_if_needed()
                rec._sr_sync_attribute_lines()

        return result

    def _sr_assign_code_if_needed(self):
        records = self.filtered(
            lambda r: not r.sr_asset_code and r.category_id
        )

        for rec in records:
            seq = rec.category_id._sr_get_or_create_sequence()
            code = seq.next_by_id()

            rec.with_context(
                sr_setting_code=True
            ).write({
                'sr_asset_code': code
            })

            rec.message_post(
                body=_(
                    'ID de activo generado automáticamente: %s',
                    code
                )
            )

    def action_sr_verify(self):
        for rec in self:
            missing = []

            if not rec.sr_asset_code:
                missing.append(_('ID Activo'))

            if not rec.category_id:
                missing.append(_('Categoría'))

            if (
                rec.category_id.sr_serial_required
                and not rec.serial_no
            ):
                missing.append(_('Número de serie'))

            required_attrs = (
                rec.category_id
                .sr_profile_ids
                .mapped('attribute_ids')
                .filtered(
                    lambda a:
                    a.active
                    and a.required_for_verification
                )
            )

            values = {
                v.attribute_id.id: v
                for v in rec.sr_attribute_value_ids
            }

            for attr in required_attrs:
                line = values.get(attr.id)

                if not line or not line.has_value():
                    missing.append(attr.name)

            if missing:
                raise UserError(
                    _(
                        'No se puede verificar el activo. '
                        'Faltan: %s'
                    ) % ', '.join(missing)
                )

            rec.write({
                'sr_document_state': 'verified',
                'sr_last_verified': fields.Datetime.now(),
                'sr_verified_by': self.env.user.id,
            })

        return True

    def unlink(self):
        if any(self.mapped('sr_asset_code')):
            raise UserError(
                _(
                    'Los activos con ID emitido no se eliminan. '
                    'Archívelos para conservar la trazabilidad.'
                )
            )

        return super().unlink()


class SrAssetComponent(models.Model):
    _name = 'sr.asset.component'
    _description = 'Componente serializado de activo'
    _order = 'equipment_id, component_type_id, id'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        required=True,
        ondelete='cascade',
        index=True
    )
    component_type_id = fields.Many2one(
        'sr.asset.component.type',
        required=True,
        string='Tipo'
    )
    brand_id = fields.Many2one(
        'sr.asset.brand',
        string='Marca'
    )
    model = fields.Char(
        string='Modelo'
    )
    serial_no = fields.Char(
        string='Número de serie',
        index=True
    )
    physical_state_id = fields.Many2one(
        'sr.asset.physical.state',
        string='Estado físico'
    )
    operational_state_id = fields.Many2one(
        'sr.asset.operational.state',
        string='Estado operativo'
    )
    include_on_responsiva = fields.Boolean(
        string='Incluir en responsiva',
        default=True
    )
    notes = fields.Text(
        string='Observaciones'
    )
    active = fields.Boolean(
        default=True
    )


class SrAssetNetworkInterface(models.Model):
    _name = 'sr.asset.network.interface'
    _description = 'Interfaz de red de activo'
    _order = 'equipment_id, id'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        required=True,
        ondelete='cascade',
        index=True
    )
    interface_type_id = fields.Many2one(
        'sr.asset.interface.type',
        required=True,
        string='Tipo'
    )
    name = fields.Char(
        string='Nombre'
    )
    mac_address = fields.Char(
        string='MAC',
        index=True
    )
    ip_address = fields.Char(
        string='IP'
    )
    dhcp = fields.Boolean(
        string='DHCP',
        default=True
    )
    notes = fields.Text(
        string='Observaciones'
    )

    @api.constrains('mac_address')
    def _check_mac(self):
        pattern = re.compile(
            r'^([0-9A-Fa-f]{2}[:-]){5}'
            r'([0-9A-Fa-f]{2})$'
        )

        for rec in self:
            if (
                rec.mac_address
                and not pattern.fullmatch(
                    rec.mac_address.strip()
                )
            ):
                raise ValidationError(
                    _(
                        'La dirección MAC no tiene '
                        'un formato válido.'
                    )
                )