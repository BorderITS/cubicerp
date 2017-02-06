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

    name = fields.Char(string='Requisition',required=True, default='/')
    ordering_date = fields.Date('Scheduled Ordering Date')
    date_end = fields.Datetime('Bid Submission Deadline')
    schedule_date = fields.Date('Scheduled Date', help="The expected and scheduled date where all the products are received")
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
                                     'purchase.requisition.merge'))
    # purchase_ids = fields.One2many('purchase.order', 'requisition_id', string='Purchase Orders',
    #                                states={'done': [('readonly', True)]})
    # po_line_ids = fields.One2many('purchase.order.line', compute="_compute_po_line_ids",  string='Products by supplier')
    line_ids = fields.One2many('purchase.requisition.merge_line', 'requisition_merge_id', string='Products to Purchase')
    # procurement_id = fields.Many2one('procurement.order', string="Procurement", ondelete='set null', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    multiple_rfq_per_supplier = fields.Boolean('Multiple RFQ per supplier')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True)

    @api.model
    def view_init(self, fields_list):
        res = super(PurchaseRequisitionMerge, self).view_init(fields_list)

        if self.env['purchase.requisition'].browse(
                        self._context.get('active_ids')
                        ).filtered(lambda r: r.state != 'in_progress'):
            raise Warning(_('Error!'), _(
                'Define product(s) you want to include in the call for bids.'
                ))

        return res

    @api.model
    def default_get(self, fields_list):
        defaults = super(PurchaseRequisitionMerge, self).default_get(fields_list)

        fields2remove = set()
        FIELDS_LIST = [
            'ordering_date',
            'date_end',
            'schedule_date',
            'exclusive',
            'multiple_rfq_per_supplier',
            'account_analytic_id',
            ]

        for requisition in self.env['purchase.requisition'].browse(self._context.get('active_ids')):
            for field_name in FIELDS_LIST:
                if field_name in fields_list:
                    field_value = defaults.setdefault(field_name, requisition[field_name])
                    if field_value != requisition[field_name]:
                        fields2remove.add(field_name)




class PurchaseRequisitionMergeLine(models.TransientModel):
    _name = "purchase.requisition.merge.line"
    _description = "Purchase Requisition Merge Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)])
    name = fields.Text('Description')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     default=lambda self: self.env['purchase.order.line']._get_uom_id())
    product_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    requisition_merge_id = fields.Many2one('purchase.requisition.merge', 'Call for Bids', ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', related='requisition_merge_id.company_id', store=True,
                                 readonly=True, default=lambda self: self.env['res.company']._company_default_get(
                                                'purchase.requisition.merge.line'))
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    schedule_date = fields.Date('Scheduled Date', required=True)
