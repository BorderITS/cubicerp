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

import openerp.addons.decimal_precision as dp
from openerp import api, fields, models

class bid_line_qty(models.TransientModel):
    _name = "bid.line.qty"
    _description = "Change Bid line quantity"

    qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)

    @api.multi
    def change_qty(self):
        active_ids = self._context and self._context.get('active_ids', [])
        data = self.browse()[0]
        self.env['purchase.order.line'].write(active_ids, {'quantity_bid': data.qty})
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
