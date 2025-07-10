import frappe


def get_context(context):
	# Initialize fields to prevent undefined errors
	context.kebele = context.get('kebele', '')
	context.sub_city = context.get('sub_city', '')
	context.custom_school_id = context.get('custom_school_id', '')
	context.image = context.get('image', '')
	
	# Set default values for common fields
	if not context.get('nationality'):
		context.nationality = 'Ethiopian'
	if not context.get('city'):
		context.city = 'Adama'
	if not context.get('state'):
		context.state = 'Oromia'
	if not context.get('country'):
		context.country = 'Ethiopia'
