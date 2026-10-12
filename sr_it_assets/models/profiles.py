from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SrAssetProfile(models.Model):
    _name = 'sr.asset.profile'
    _description = 'Perfil técnico de activo'
    _order = 'sequence, name, id'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    attribute_ids = fields.One2many(
        'sr.asset.attribute',
        'profile_id',
        string='Atributos'
    )

    _sql_constraints = [
        (
            'code_unique',
            'unique(code)',
            'El código del perfil técnico debe ser único.'
        ),
    ]

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if rec.code and (
                not rec.code.isalnum()
                or rec.code != rec.code.upper()
            ):
                raise ValidationError(
                    'El código del perfil debe usar únicamente '
                    'letras/números en mayúsculas.'
                )


class SrAssetAttribute(models.Model):
    _name = 'sr.asset.attribute'
    _description = 'Atributo técnico configurable'
    _order = 'profile_id, sequence, name, id'

    name = fields.Char(required=True, translate=True)

    profile_id = fields.Many2one(
        'sr.asset.profile',
        required=True,
        ondelete='cascade',
        index=True
    )

    value_type = fields.Selection(
        [
            ('char', 'Texto corto'),
            ('text', 'Texto largo'),
            ('integer', 'Entero'),
            ('float', 'Decimal'),
            ('boolean', 'Sí/No'),
            ('date', 'Fecha'),
            ('selection', 'Lista'),
        ],
        required=True,
        default='char'
    )

    uom_id = fields.Many2one(
        'sr.asset.uom',
        string='Unidad'
    )

    required_for_verification = fields.Boolean(
        string='Obligatorio al verificar'
    )

    show_on_responsiva = fields.Boolean(
        string='Mostrar en responsiva'
    )

    highlighted = fields.Boolean(
        string='Mostrar destacado'
    )

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    option_ids = fields.One2many(
        'sr.asset.attribute.option',
        'attribute_id',
        string='Opciones'
    )


class SrAssetAttributeOption(models.Model):
    _name = 'sr.asset.attribute.option'
    _description = 'Opción de atributo técnico'
    _order = 'sequence, name, id'

    name = fields.Char(required=True, translate=True)

    attribute_id = fields.Many2one(
        'sr.asset.attribute',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class SrAssetAttributeValue(models.Model):
    _name = 'sr.asset.attribute.value'
    _description = 'Valor técnico de activo'
    _order = 'attribute_id, id'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        required=True,
        ondelete='cascade',
        index=True
    )

    attribute_id = fields.Many2one(
        'sr.asset.attribute',
        required=True,
        ondelete='restrict',
        index=True
    )

    # ---------------------------------------------------------
    # Tipo de valor
    # ---------------------------------------------------------
    # Campo relacionado utilizado por las vistas para determinar
    # qué campo de captura debe mostrarse al usuario.
    # ---------------------------------------------------------

    value_type = fields.Selection(
        related='attribute_id.value_type',
        string='Tipo de valor',
        readonly=True
    )

    # ---------------------------------------------------------
    # Campos donde se almacena el valor según su tipo
    # ---------------------------------------------------------

    value_char = fields.Char(
        string='Valor texto'
    )

    value_text = fields.Text(
        string='Valor texto largo'
    )

    value_integer = fields.Integer(
        string='Valor entero'
    )

    value_float = fields.Float(
        string='Valor decimal'
    )

    value_boolean = fields.Boolean(
        string='Valor Sí/No'
    )

    value_date = fields.Date(
        string='Valor fecha'
    )

    option_id = fields.Many2one(
        'sr.asset.attribute.option',
        string='Opción'
    )

    # ---------------------------------------------------------
    # Valor mostrado al usuario
    # ---------------------------------------------------------

    value_display = fields.Char(
        compute='_compute_value_display',
        string='Valor'
    )

    # ---------------------------------------------------------
    # Información relacionada con el atributo
    # ---------------------------------------------------------

    uom_id = fields.Many2one(
        related='attribute_id.uom_id',
        readonly=True
    )

    profile_id = fields.Many2one(
        related='attribute_id.profile_id',
        readonly=True,
        store=True
    )

    # ---------------------------------------------------------
    # Restricciones
    # ---------------------------------------------------------

    _sql_constraints = [
        (
            'equipment_attribute_unique',
            'unique(equipment_id, attribute_id)',
            'El atributo sólo puede existir una vez por activo.'
        ),
    ]

    # ---------------------------------------------------------
    # Cálculo del valor mostrado
    # ---------------------------------------------------------

    @api.depends(
        'attribute_id.value_type',
        'value_char',
        'value_text',
        'value_integer',
        'value_float',
        'value_boolean',
        'value_date',
        'option_id',
        'uom_id.symbol'
    )
    def _compute_value_display(self):
        for rec in self:
            typ = rec.attribute_id.value_type
            value = ''

            if typ == 'char':
                value = rec.value_char or ''

            elif typ == 'text':
                value = rec.value_text or ''

            elif typ == 'integer':
                value = (
                    str(rec.value_integer)
                    if rec.value_integer is not False
                    else ''
                )

            elif typ == 'float':
                value = (
                    str(rec.value_float)
                    if rec.value_float is not False
                    else ''
                )

            elif typ == 'boolean':
                value = 'Sí' if rec.value_boolean else 'No'

            elif typ == 'date':
                value = str(rec.value_date or '')

            elif typ == 'selection':
                value = rec.option_id.name or ''

            rec.value_display = (
                f"{value} {rec.uom_id.symbol or ''}".strip()
            )

    # ---------------------------------------------------------
    # Validación de existencia de valor
    # ---------------------------------------------------------

    def has_value(self):
        self.ensure_one()

        typ = self.attribute_id.value_type

        if typ == 'char':
            return bool(self.value_char)

        if typ == 'text':
            return bool(self.value_text)

        if typ == 'integer':
            return self.value_integer is not False

        if typ == 'float':
            return self.value_float is not False

        if typ == 'boolean':
            return True

        if typ == 'date':
            return bool(self.value_date)

        if typ == 'selection':
            return bool(self.option_id)

        return False