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

class PurchaseRequisitionMerge(models.TransientModel):
    _name = "purchase.requisition.merge"
    _description = "Purchase Requisition Merge"

    name = fields.Char(string='Requisition',required=True ,copy=False, default='/')
    ordering_date = fields.Date('Scheduled Ordering Date')
    date_end = fields.Datetime('Bid Submission Deadline')
    schedule_date = fields.Date('Scheduled Date', select=True,
                                help="The expected and scheduled date where all the products are received")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    exclusive = fields.Selection([
        ('exclusive', 'Select only one RFQ (exclusive)'),
        ('multiple', 'Select multiple RFQ')
        ], 'Bid Selection Type', required=True, default='multiple',
        help="Select only one RFQ (exclusive):  On the confirmation of a purchase order, it cancels the remaining "
             "purchase order.\nSelect multiple RFQ:  It allows to have multiple purchase orders.On confirmation of a "
             "purchase order it does not cancel the remaining orders""")
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', string="Company", required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'purchase.requisition'))
    # purchase_ids = fields.One2many('purchase.order', 'requisition_id', string='Purchase Orders',
    #                                states={'done': [('readonly', True)]})
    # po_line_ids = fields.One2many('purchase.order.line', compute="_compute_po_line_ids",  string='Products by supplier')
    line_ids = fields.One2many('purchase.requisition.line', 'requisition_id', string='Products to Purchase',
                               states={'done': [('readonly', True)]}, copy=True)
    # procurement_id = fields.Many2one('procurement.order', string="Procurement", ondelete='set null', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    multiple_rfq_per_supplier = fields.Boolean('Multiple RFQ per supplier')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True ,
                                      default=lambda self: self._default_picking_type_id())
