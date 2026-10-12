from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestSrItAssets(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cat = self.env['maintenance.equipment.category'].create({'name': 'Monitor SR', 'sr_prefix': 'MON'})

    def test_sequence_and_immutability(self):
        a = self.env['maintenance.equipment'].create({'name': 'Monitor A', 'category_id': self.cat.id})
        b = self.env['maintenance.equipment'].create({'name': 'Monitor B', 'category_id': self.cat.id})
        self.assertEqual(a.sr_asset_code, 'SR-MON-00001')
        self.assertEqual(b.sr_asset_code, 'SR-MON-00002')
        with self.assertRaises(UserError):
            self.cat.write({'sr_prefix': 'MNT'})
        with self.assertRaises(UserError):
            a.unlink()

    def test_required_attribute_verification(self):
        profile = self.env['sr.asset.profile'].create({'name': 'Pantalla Test', 'code': 'PANTEST'})
        attr = self.env['sr.asset.attribute'].create({
            'name': 'Resolución', 'profile_id': profile.id, 'value_type': 'char',
            'required_for_verification': True,
        })
        self.cat.sr_profile_ids = profile
        a = self.env['maintenance.equipment'].create({'name': 'Monitor C', 'category_id': self.cat.id})
        with self.assertRaises(UserError):
            a.action_sr_verify()
        line = a.sr_attribute_value_ids.filtered(lambda x: x.attribute_id == attr)
        line.value_char = '1920x1080'
        a.action_sr_verify()
        self.assertEqual(a.sr_document_state, 'verified')
