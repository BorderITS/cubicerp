# coding=utf-8

import logging
import string
from passlib.context import CryptContext

from openerp import models, fields, api, _
from openerp.exceptions import AccessDenied, ValidationError
from openerp.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

crypt_context = CryptContext(
    ['pbkdf2_sha512', 'md5_crypt'],
    deprecated=['md5_crypt'],
)


class ResUser(models.Model):
    _inherit = 'res.users'

    password = fields.Char('Password', size=256)

    @api.one
    def write(self, values):
        """
        Only encrypt password when user intent update it.
        """
        if 'password' in values:
            problems = self._validate_password(values['password'])  # verifying if the password fulfills all rules
            if problems:
                raise ValidationError(
                    _("Password must match with following rules\n %s ") % ("\n-- ".join(problems)))
            values['password'] = crypt_context.encrypt(values['password'])
        return super(ResUser, self).write(values)

    def _validate_password(self, password):
        """
        Verifying if the password fulfills all rules
        :param password: str : string with password value
        :return: [] : list of problems found in strings format
        """
        ConfigParameter = self.env['ir.config_parameter']
        # ---------------------------------------
        config_data = {
            'pwd_min_character':
                safe_eval(ConfigParameter.get_param('l10n_cu_auth_crypt.pwd_min_character', '5')),
            'pwd_has_capital_letter':
                safe_eval(ConfigParameter.get_param('l10n_cu_auth_crypt.pwd_has_capital_letter', 'False')),
            'pwd_has_digit':
                safe_eval(ConfigParameter.get_param('l10n_cu_auth_crypt.pwd_has_digit', 'False')),
            'pwd_has_special_letter':
                safe_eval(ConfigParameter.get_param('l10n_cu_auth_crypt.pwd_has_special_letter', 'False'))
        }
        # ---------------------------------------
        password_rules = []
        password_rules.append(
            lambda s: len(s) >= config_data.get('pwd_min_character', 5) or
                      _('Has %s or more characters') % (config_data.get(
                          'pwd_min_character', 5)
                      )
        )
        # ---------------------------------------
        if config_data.get('pwd_has_capital_letter', False):
            password_rules.append(
                lambda s: any(x.isupper() for x in s) or
                          _('Has one capital letter at least')
            )
        # ---------------------------------------
        if config_data.get('pwd_has_digit', False):
            password_rules.append(
                lambda s: any(x.isdigit() for x in s) or
                          _('Has one digit at least')
            )
        # ---------------------------------------
        if config_data.get('pwd_has_special_letter', False):
            password_rules.append(
                lambda s: any(x in string.punctuation for x in s) or
                          _('Has one special letter at least')
            )
        # ---------------------------------------
        problems = [
            p for p in [
                r(password) for r in password_rules
                ] if p and p is not True]
        # ---------------------------------------
        return problems

    # -------------------------------------------------------------------------
    # Override auth_crypt implementations
    # -------------------------------------------------------------------------
    def check_credentials(self, cr, uid, password):
        try:
            return super(ResUser, self).check_credentials(cr, uid, password)
        except AccessDenied:
            cr.execute('SELECT password FROM res_users WHERE id=%s AND active' % uid)
            if cr.rowcount:
                encrypted_password = cr.fetchone()
                try:
                    if crypt_context.verify(password, encrypted_password[0]):
                        return
                    else:
                        raise AccessDenied()
                except ValueError:
                    raise AccessDenied()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
