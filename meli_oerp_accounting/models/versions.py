
acc_pay_ref = "communication"
invoice_origin = "invoice_origin"
report_invoices = "account.account_invoices"
posted_statuses = ['posted']
def report_render( template, res_ids=None, data=None):
    return template.render_qweb_pdf( res_ids=res_ids,data=data)

def order_create_invoices( sale_order, grouped=False, final=False ):
	return sale_order._create_invoices(grouped=grouped, final=final)

def payment_post( self ):
    return self.post()
