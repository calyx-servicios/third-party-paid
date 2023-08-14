# -*- coding: utf-8 -*-

{
    "name" : "Purchase Tender Based On Supplier",
    "author": "Edge Technologies",
    "version" : "13.0.1.0",
    "live_test_url":'https://youtu.be/f98b49uiTaI',
    "images":["static/description/main_screenshot.png"],
    'summary': 'Purchase tender bidding for supplier bidding procurement tender bidding procurement best supplier tender management bid for best supplier bidding process procurement bidding process procurement of vendor choose best supplier on tender purchase requisition',
    "description": """Purchase tender helps customers to select the best quotation among all the purchase orders. change quantities of selected quotation.
Odoo previous versions had tender bidding procurement to choose best vendor/supplier, so this app helps to choose best request for proposal rfq, this module helps to avoid problems of the customers during creating purchase order with multiple vendors. user can create purchase order with the chosen products and most suitable supplier from bid in tendering process by this odoo erp module
Tender bidding for supplier
Bidding procurement
Supplier bidding

Tender bidding procurement for best supplier
Bidding process
Tender management  bid supplier price comparision
Request for proposal RFP
RFP
Bids for best supplier 
Bidding process 
  Supplier bidding process supplier tender bidding process

Procurement bidding process
Tender procurement process 
Procurement for supplier 
Supplier procurement
Vendor procurement
Procurement of vendors

   Choose best supplier on tender
Tender procurement for best supplier
Procurement for best supplier
Procurement supplier
Supplier procurement
 Best supplier purchase tender
 Tender best supplier
Tender requisition by supplier best supplier from tender process
Purchase requisition with supplier purchase procurement process material purchase requisition supplier material requisition


 """,
    "license" : "OPL-1",
    "depends" : ['base','purchase','purchase_requisition','purchase_requisition_stock'],
    "data": [   
        'views/purchase_agreement_views.xml',
        'wizard/quantity_wizard_views.xml',
        'wizard/generate_views.xml',
        'data/data.xml'
    ],
    "auto_install": False,
    "installable": True,
    "price": 48,
    "currency": 'EUR',
    "category" : "Purchase",
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
