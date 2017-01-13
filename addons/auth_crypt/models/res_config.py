# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.tools.safe_eval import safe_eval


class AuthConfigSettings(models.TransientModel):
    _name = 'auth.config.settings'
    _inherit = 'res.config.settings'

    pwd_min_character = fields.Integer(string='Minimum Password Length')
    pwd_has_capital_letter = fields.Boolean(string='Use Capital Letters')
    pwd_has_digit = fields.Boolean(string='Use Digits')
    pwd_has_special_letter = fields.Boolean(string='Use Special Characters')

    def get_default_pwd_min_character(self, cr, uid, fields, ctx=None):
        icp = self.pool['ir.config_parameter']
        return {
            'pwd_min_character':
                safe_eval(icp.get_param(cr, uid, 'l10n_cu_auth_crypt.pwd_min_character', '5')),
            'pwd_has_capital_letter':
                safe_eval(icp.get_param(cr, uid, 'l10n_cu_auth_crypt.pwd_has_capital_letter', 'False')),
            'pwd_has_digit':
                safe_eval(icp.get_param(cr, uid, 'l10n_cu_auth_crypt.pwd_has_digit', 'False')),
            'pwd_has_special_letter':
                safe_eval(icp.get_param(cr, uid, 'l10n_cu_auth_crypt.pwd_has_special_letter', 'False')),
        }

    def set_pwd_min_character(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context=context)
        # ---------------------------------------
        if config.pwd_min_character < 1:
            raise ValidationError(_('Password length should be 1 at less.'))
        # ---------------------------------------
        icp = self.pool['ir.config_parameter']
        icp.set_param(cr, uid, 'l10n_cu_auth_crypt.pwd_min_character', repr(config.pwd_min_character))
        icp.set_param(cr, uid, 'l10n_cu_auth_crypt.pwd_has_capital_letter', repr(config.pwd_has_capital_letter))
        icp.set_param(cr, uid, 'l10n_cu_auth_crypt.pwd_has_digit', repr(config.pwd_has_digit))
        icp.set_param(cr, uid, 'l10n_cu_auth_crypt.pwd_has_special_letter', repr(config.pwd_has_special_letter))
