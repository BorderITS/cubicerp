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
from openerp.addons import decimal_precision as dp



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
        ], 'Bid Selection Type',
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
    line_ids = fields.One2many('purchase.requisition.merge.line', 'requisition_merge_id', string='Products to Purchase')
    # procurement_id = fields.Many2one('procurement.order', string="Procurement", ondelete='set null', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    multiple_rfq_per_supplier = fields.Boolean('Multiple RFQ per supplier')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True,
                                      default=lambda self: self._default_picking_type_id())

    @api.model
    def _default_picking_type_id(self):
        return self.env.ref('stock.picking_type_in')

    @api.multi
    def action_requisition_merge(self):
        if self._context.get('active_model') == 'purchase.requisition' and self.env['purchase.requisition'].browse(
                        self._context.get('active_ids')
                        ).filtered(lambda r: r.state != 'in_progress' or
                                             r.parent_id or
                                             r.child_ids):
            raise Warning(_('Error!'), _(
                'The selected requisitions are already processed or merged.'
                ))

        action = self.env.ref('purchase_requisition.purchase_requisition_merge').read()[0]
        action['context'] = self._context.copy()

        return action

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

        lines2merge = []
        for requisition in self.env['purchase.requisition'].browse(self._context.get('active_ids')):
            for field_name in FIELDS_LIST:
                if field_name in fields_list:
                    field_value = defaults.setdefault(field_name, requisition[field_name])
                    # if detect more than one value for the given field mark for remove
                    if field_value != requisition[field_name]:
                        fields2remove.add(field_name)

            # TODO: add requisition lines as line for this wizard
            for line in requisition.line_ids:
                lines2merge.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_id': line.product_uom_id.id,
                    'product_qty': line.product_qty,
                    'company_id': line.company_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'schedule_date': line.schedule_date,
                    'requisition_id': line.requisition_id.id,
                    }))

        if lines2merge:
            defaults['line_ids'] = lines2merge

        # remove fields with more than one value for the given requisitions
        for field_name in fields2remove:
            defaults.pop(field_name)

        if 'account_analytic_id' in defaults and isinstance(defaults['account_analytic_id'], models.BaseModel):
            defaults['account_analytic_id'] = defaults['account_analytic_id'].id

        return defaults

    @api.model
    def _get_hash_key(self, merge, tender):
        assert isinstance(tender, models.BaseModel) and tender._name == 'purchase.requisition', "A requisition is expected"

        return (
            merge.exclusive or tender.exclusive,
            merge.schedule_date or tender.schedule_date,
            )

    @api.model
    def _prepare_tender(self, merge, tender):
        assert (isinstance(tender, models.BaseModel) and
                tender._name == 'purchase.requisition'), "A requisition is expected"

        return {
            'name': merge.name,
            # 'parent_id': ,
            'child_ids': [],
            'origin': '',
            'ordering_date': merge.ordering_date,
            'date_end': merge.date_end,
            'schedule_date': merge.schedule_date or tender.schedule_date,
            'exclusive': merge.exclusive or tender.exclusive,
            'description': merge.description,
            # 'company_id': self.company_id.id;
            # 'purchase_ids':;
            # 'po_line_ids':;
            'line_ids': [],
            # 'procurement_id':,
            'warehouse_id': merge.warehouse_id.id,
            'state': 'draft',
            'multiple_rfq_per_supplier': merge.multiple_rfq_per_supplier,
            'account_analytic_id': merge.account_analytic_id.id,
            'picking_type_id': merge.picking_type_id.id,
            # 'compliance':;
            }

    @api.model
    def _prepare_tender_line(self, merge, line):
        assert (isinstance(line, models.TransientModel) and
                line._name == 'purchase.requisition.merge.line'), "A requisition merge line was expected"

        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'product_uom_id': line.product_uom_id.id,
            'product_qty': line.product_qty,
            # 'requisition_id': ;
            # 'company_id': ,
            'account_analytic_id': line.account_analytic_id.id,
            'schedule_date': line.schedule_date,
            }

    @api.multi
    def merge_requisition(self):
        PurchaseRequisition = self.env['purchase.requisition']

        tenders_def = {}
        for record in self:
            for line in record.line_ids:
                # group lines acccording to exclude policy & schedule date & prepare a proposition requisition
                tender_def = tenders_def.setdefault(
                                    self._get_hash_key(record, line.requisition_id),
                                    self._prepare_tender(record, line.requisition_id)
                                    )

                # add requisition lines to the merge proposition
                tender_def['line_ids'].append((0, 0, self._prepare_tender_line(record, line)))

                # mark source requisition as oring of the created one
                src_origin = list(set(tender_def['origin'].split(' | ')).union([line.requisition_id.name or '']))
                src_origin = filter(None, src_origin)
                tender_def['origin'] = ' | '.join(src_origin)

                # get merge requisition reference to marge parent/child relationship
                tender_def['child_ids'] = list(set(tender_def['child_ids']).union([line.requisition_id.id]))

        for tender_def in tenders_def.values():
            tender_lines = tender_def.pop('child_ids', [])

            # create a requisition merge
            tender = PurchaseRequisition.create(tender_def)

            # update requisitions to set that are merged in the create one
            PurchaseRequisition.browse(tender_lines).write({'parent_id': tender.id})

        return {'type': 'ir.actions.act_window_close'}


class PurchaseRequisitionMergeLine(models.TransientModel):
    _name = "purchase.requisition.merge.line"
    _description = "Purchase Requisition Merge Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)])
    name = fields.Text('Description')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     default=lambda self: self.env['purchase.order.line']._get_uom_id())
    product_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    requisition_merge_id = fields.Many2one('purchase.requisition.merge', 'Merge Call for Bids', ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', related='requisition_merge_id.company_id', store=True,
                                 readonly=True, default=lambda self: self.env['res.company']._company_default_get(
                                                'purchase.requisition.merge.line'))
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    schedule_date = fields.Date('Scheduled Date', required=True)
    requisition_id = fields.Many2one('purchase.requisition', 'Call for Bids')
