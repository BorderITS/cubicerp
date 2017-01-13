# coding=utf-8

from openerp import models, fields, api, _


class ResGroups(models.Model):
    _inherit = 'res.groups'

    login_calendar_id = fields.Many2one('resource.calendar', 'Allowed Login Calendar')


class ResUser(models.Model):
    _inherit = 'res.users'

    login_calendar_id = fields.Many2one('resource.calendar', 'Allowed Login Calendar')
