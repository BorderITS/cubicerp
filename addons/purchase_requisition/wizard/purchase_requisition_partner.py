# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import Warning

class PurchaseRequisitionPartner(models.TransientModel):
    _name = "purchase.requisition.partner"
    _description = "Purchase Requisition Partner"

    partner_id = fields.Many2one('res.partner', 'Supplier', required=True, domain=[('supplier', '=', True)])

    @api.model
    def view_init(self, fields_list):
        res = super(PurchaseRequisitionPartner, self).view_init(fields_list)

        if not self.env['purchase.requisition'].browse(self._context.get('active_id', False)).line_ids:
            raise Warning(_('Error!'), _(
                'Define product(s) you want to include in the call for bids.'
                ))

        return res

    @api.multi
    def create_order(self):
        self.env['purchase.requisition'].browse(
                self._context.get('active_id', False)
                ).make_purchase_order(self[0].partner_id.id)
        return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
