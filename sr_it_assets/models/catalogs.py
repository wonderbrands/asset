from odoo import fields, models


class SrAssetCatalogMixin(models.AbstractModel):
    _name = 'sr.asset.catalog.mixin'
    _description = 'Mixin para catálogos de activos TI'
    _order = 'sequence, name, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class SrAssetPhysicalState(models.Model):
    _name = 'sr.asset.physical.state'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Estado físico del activo'


class SrAssetOperationalState(models.Model):
    _name = 'sr.asset.operational.state'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Estado operativo del activo'


class SrAssetCondition(models.Model):
    _name = 'sr.asset.condition'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Condición del activo'


class SrAssetOwnershipType(models.Model):
    _name = 'sr.asset.ownership.type'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Tipo de propiedad del activo'


class SrAssetBrand(models.Model):
    _name = 'sr.asset.brand'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Marca de activo'


class SrAssetComponentType(models.Model):
    _name = 'sr.asset.component.type'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Tipo de componente de activo'


class SrAssetInterfaceType(models.Model):
    _name = 'sr.asset.interface.type'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Tipo de interfaz de red'


class SrAssetStorageType(models.Model):
    _name = 'sr.asset.storage.type'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Tipo de almacenamiento'


class SrAssetUom(models.Model):
    _name = 'sr.asset.uom'
    _inherit = 'sr.asset.catalog.mixin'
    _description = 'Unidad técnica de activo'

    symbol = fields.Char(required=True)
