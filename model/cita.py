# -*- coding: utf-8 -*-
import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.tools.yaml_import import is_comment
import pytz
import time
from mx import DateTime
import datetime
class cita(osv.osv):
	_name='dental.appointment'
	def copy(self, cr, uid, id, default=None, context={}):
		default.update({'validity_status':'tobe'})
		return super(appointment,self).copy(cr, uid, id, default, context)

	def onchange_appointment_date(self, cr, uid, ids, apt_date):
		if apt_date:
			validity_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(apt_date,"%Y-%m-%d %H:%M:%S")))
			validity_date = validity_date+datetime.timedelta(days=7)
			v = {'appointment_validity_date':str(validity_date)}
			return {'value': v}
		return {}

	_columns={
		'doctor' : fields.many2one ('dental.physician','Physician', help="Physician's Name"),
		'name' : fields.char ('Appointment ID',size=64, readonly=True, required=True),
		'patient' : fields.many2one ('dental.patient','Patient', help="Patient Name"),
		'speciality' : fields.many2one ('dental.speciality','Speciality', help="Medical Speciality / Sector"),
		'appointment_date' : fields.datetime('Appointment Date'),
		'comments' : fields.text ('Comments'),
		'photo':fields.binary('Photo'),
		'user_id':fields.related('doctor','user_id',type='many2one',relation='res.partner',string='Physician'),
		'no_invoice' : fields.boolean ('Invoice exempt'),
		'appointment_validity_date' : fields.datetime ('Validity Date'),
		'validity_status' : fields.selection([('invoiced','Invoiced'),('tobe','To be Invoiced')],'Status'),
		'consultations' : fields.many2one ('product.product', 'Consultation Service', domain=[('type', '=', "service")], help="Consultation Services", required=False),
			}
	_defaults = {
		'validity_status': lambda *a: 'tobe',
		'no_invoice': lambda *a: False
	}	

cita()

class dent(osv.osv):
	_name= "dental.dent"
	def _get_image(self, cr, uid, ids, name, args, context=None):
		result = dict.fromkeys(ids, False)
		for obj in self.browse(cr, uid, ids, context=context):
			result[obj.id] = tools.image_get_resized_images(obj.image, avoid_resize_small=True)
		return result
	def _set_image(self, cr, uid, id, name, value, args, context=None):
		return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
	_columns={
		'name': fields.char("Name"),
		'image': fields.binary('pics'),
		}
dent()

class physician (osv.osv):
	_name = "dental.physician"
	_description = "Information about the doctor"
	_columns = {
		'name' : fields.many2one ('res.partner','Physician', domain=[('is_doctor', '=', "1")], help="Physician's Name, from the partner list"),
		'institution' : fields.many2one ('res.partner','Institution',domain=[('is_institution', '=', "1")],help="Instituion where she/he works"),
		'code' : fields.char ('ID', size=128, help="MD License ID"),
		'speciality' : fields.many2one ('dental.speciality','Speciality', help="Speciality Code"),
		'available_lines': fields.one2many('dental.physician.line', 'physician_id', 'Physician Availability'),
		'info' : fields.text ('Extra info'),
		}

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		rec_name = 'name'
		res = [(r['id'], r[rec_name][1]) for r in self.read(cr, uid, ids, [rec_name], context)]
		return res
physician ()

class patient_data (osv.osv):
	_name = "dental.patient"
	_description = "Patient related information"
	
	def name_get(self, cr, user, ids, context={}):
		if not len(ids):
			return []
		def _name_get(d):
			name = d.get('name','')
			id = d.get('patient_id',False)
			if id:
				name = '[%s] %s' % (id,name[1])
			return (d['id'], name)
		result = map(_name_get, self.read(cr, user, ids, ['name','patient_id'], context))
		return result

	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
		if not args:
			args=[]
		if not context:
			context={}
		if name:
			ids = self.search(cr, user, [('patient_id','=',name)]+ args, limit=limit, context=context)
			if not len(ids):
				ids += self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context)
		return result    


# Automatically assign the family code

	def onchange_partnerid (self, cr, uid, ids, partner):
		partner_img_id = ""
		if not partner:
			return {}
		if partner:
 			cr.execute ('select image from res_partner where id=%s',(partner,))
 			values = cr.fetchone()
 			if values:
 				#raise osv.except_osv(_('Image'), _(str(values[0]))) 			 	
 				partner_img_id = str(values[0])				
		 		v = {'photo':partner_img_id}		
				return {'value': v}
			else:
				#raise osv.except_osv(_('Image'), _("Inside"))
				return {}
							
# Get the patient age in the following format : "YEARS MONTHS DAYS"
# It will calculate the age of the patient while the patient is alive. When the patient dies, it will show the age at time of death.


		
	def _patient_age(self, cr, uid, ids, name, arg, context={}):
		def compute_age_from_dates (patient_dob):
			now=DateTime.now()
			if (patient_dob):
				dob=DateTime.strptime(patient_dob,'%Y-%m-%d')
				delta=DateTime.Age (now, dob)
				years_months_days = str(delta.years) +"y "+ str(delta.months) +"m "+ str(delta.days)+"d" 
			else:
				years_months_days = "No DoB !"
			
 
			return years_months_days
		result={}
	    	for patient_data in self.browse(cr, uid, ids, context=context):
	        	result[patient_data.id] = compute_age_from_dates (patient_data.dob)
	    	return result

	def _get_image_of18(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			print image.d18.image
			result[image.id]= image.d18.image
		return result
	def _get_image_of17(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d17.image
		return result
	def _get_image_of16(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d16.image
		return result
	def _get_image_of15(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d15.image
		return result
	def _get_image_of14(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d14.image
		return result
	def _get_image_of13(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d13.image
		return result
	def _get_image_of12(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d12.image
		return result
	def _get_image_of11(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d11.image
		return result
	def _get_image_of28(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d28.image
		return result
	def _get_image_of27(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d27.image
		return result
	def _get_image_of26(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d26.image
		return result
	def _get_image_of25(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d25.image
		return result
	def _get_image_of24(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d24.image
		return result
	def _get_image_of23(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d23.image
		return result
	def _get_image_of22(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d22.image
		return result
	def _get_image_of21(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d21.image
		return result
	def _get_image_of38(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d38.image
		return result
	def _get_image_of37(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d37.image
		return result
	def _get_image_of36(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d36.image
		return result
	def _get_image_of35(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d35.image
		return result
	def _get_image_of34(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d34.image
		return result
	def _get_image_of33(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d33.image
		return result
	def _get_image_of32(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d32.image
		return result
	def _get_image_of31(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d31.image
		return result
	def _get_image_of48(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d48.image
		return result
	def _get_image_of47(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d47.image
		return result
	def _get_image_of46(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d46.image
		return result
	def _get_image_of45(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d45.image
		return result
	def _get_image_of44(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d44.image
		return result
	def _get_image_of43(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d43.image
		return result
	def _get_image_of42(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d42.image
		return result
	def _get_image_of41(self, cr, uid, id, field, arg, context=None):
		result = {}
		image = ""
		for image in self.browse(cr, uid, id, context=context):
			print "="*50
			result[image.id]= image.d41.image
		return result

	
	_columns = {
                'name' : fields.many2one('res.partner','Patient', required="1", domain=[('is_patient', '=', True),('is_person', '=', True) ], help="Patient Name"),
                'patient_id': fields.char('ID', size=64, required=True, select=True, help="Patient Identifier provided by the Health Center. Is not the patient id from the partner form"),	
				'lastname' : fields.related ('name','lastname',type='char',string='Lastname', required="1"), 
				'identifier' : fields.related ('name','ref',type='char',string='SSN', help="Social Security Number or National ID"),
				'current_insurance': fields.many2one ('dental.insurance',"Insurance", domain="[('name','=',name)]",help="Insurance information. You may choose from the different insurances belonging to the patient"),
				'current_address': fields.many2one ('res.partner', "Address", domain="[('id','=',name)]", help="Contact information. You may choose from the different contacts and addresses this patient has"),
				'primary_care_doctor': fields.many2one('dental.physician','Primary Care Doctor', help="Current primary care / family doctor"),
				'photo' : fields.binary ('Picture'),
				'dob' : fields.date ('Date of Birth'),
				'd18':fields.many2one('dental.dent','18',editable=False),
				'id18':fields.function(_get_image_of18,type='binary', string='Image'),
				'd17':fields.many2one('dental.dent','17'),
				'id17':fields.function(_get_image_of17,type='binary', string='Image'),
				'd16':fields.many2one('dental.dent','16'),
				'id16':fields.function(_get_image_of16,type='binary', string='Image'),
				'd15':fields.many2one('dental.dent','15'),
				'id15':fields.function(_get_image_of15,type='binary', string='Image'),
				'd14':fields.many2one('dental.dent','14'),
				'id14':fields.function(_get_image_of14,type='binary', string='Image'),
				'd13':fields.many2one('dental.dent','13'),
				'id13':fields.function(_get_image_of13,type='binary', string='Image'),
				'd12':fields.many2one('dental.dent','12'),
				'id12':fields.function(_get_image_of12,type='binary', string='Image'),
				'd11':fields.many2one('dental.dent','11'),
				'id11':fields.function(_get_image_of11,type='binary', string='Image'),
				'd28':fields.many2one('dental.dent','28'),
				'id28':fields.function(_get_image_of28,type='binary', string='Image'),
				'd27':fields.many2one('dental.dent','27'),
				'id27':fields.function(_get_image_of27,type='binary', string='Image'),
				'd26':fields.many2one('dental.dent','26'),
				'id26':fields.function(_get_image_of26,type='binary', string='Image'),
				'd25':fields.many2one('dental.dent','25'),
				'id25':fields.function(_get_image_of25,type='binary', string='Image'),
				'd24':fields.many2one('dental.dent','24'),
				'id24':fields.function(_get_image_of24,type='binary', string='Image'),
				'd23':fields.many2one('dental.dent','23'),
				'id23':fields.function(_get_image_of23,type='binary', string='Image'),
				'd22':fields.many2one('dental.dent','22'),
				'id22':fields.function(_get_image_of22,type='binary', string='Image'),
				'd21':fields.many2one('dental.dent','21'),
				'id21':fields.function(_get_image_of21,type='binary', string='Image'),
				'd48':fields.many2one('dental.dent','48'),
				'id48':fields.function(_get_image_of48,type='binary', string='Image'),
				'd47':fields.many2one('dental.dent','47'),
				'id47':fields.function(_get_image_of47,type='binary', string='Image'),
				'd46':fields.many2one('dental.dent','46'),
				'id46':fields.function(_get_image_of46,type='binary', string='Image'),
				'd45':fields.many2one('dental.dent','45'),
				'id45':fields.function(_get_image_of45,type='binary', string='Image'),
				'd44':fields.many2one('dental.dent','44'),
				'id44':fields.function(_get_image_of44,type='binary', string='Image'),
				'd43':fields.many2one('dental.dent','43'),
				'id43':fields.function(_get_image_of43,type='binary', string='Image'),
				'd42':fields.many2one('dental.dent','42'),
				'id42':fields.function(_get_image_of42,type='binary', string='Image'),
				'd41':fields.many2one('dental.dent','41'),
				'id41':fields.function(_get_image_of41,type='binary', string='Image'),
				'd38':fields.many2one('dental.dent','38'),
				'id38':fields.function(_get_image_of38,type='binary', string='Image'),
				'd37':fields.many2one('dental.dent','37'),
				'id37':fields.function(_get_image_of37,type='binary', string='Image'),
				'd36':fields.many2one('dental.dent','36'),
				'id36':fields.function(_get_image_of36,type='binary', string='Image'),
				'd35':fields.many2one('dental.dent','35'),
				'id35':fields.function(_get_image_of35,type='binary', string='Image'),
				'd34':fields.many2one('dental.dent','34'),
				'id34':fields.function(_get_image_of34,type='binary', string='Image'),
				'd33':fields.many2one('dental.dent','33'),
				'id33':fields.function(_get_image_of33,type='binary', string='Image'),
				'd32':fields.many2one('dental.dent','32'),
				'id32':fields.function(_get_image_of32,type='binary', string='Image'),
				'd31':fields.many2one('dental.dent','31'),
				'id31':fields.function(_get_image_of31,type='binary', string='Image'),
				'age' : fields.function(_patient_age, method=True, type='char', size=32, string='Patient Age',help="It shows the age of the patient in years(y), months(m) and days(d).\nIf the patient has died, the age shown is the age at time of death, the age corresponding to the date on the death certificate. It will show also \"deceased\" on the field"),
				'sex' : fields.selection([
                                ('m','Male'),
                                ('f','Female'),
                                ], 'Sex', select=True),
				'marital_status' : fields.selection([
                                ('s','Single'),
                                ('m','Married'),
				('w','Widowed'),
				('d','Divorced'),
				('x','Separated'),
                                ], 'Marital Status'),
				'blood_type' : fields.selection([
				('A','A'),
				('B','B'),
				('AB','AB'),
				('O','O'),
				], 'Blood Type'),
				'rh' : fields.selection([
				('+','+'),
				('-','-'),
				], 'Rh'),


				'user_id':fields.related('name','user_id',type='many2one',relation='res.partner',string='Doctor',help="Physician that logs in the local Medical system (HIS), on the health center. It doesn't necesarily has do be the same as the Primary Care doctor"),
				'ethnic_group' : fields.many2one ('dental.ethnicity','Ethnic group'),
				'medications' : fields.one2many('dental.patient.medication','name','Medications'),
				'prescriptions': fields.one2many ('dental.prescription.order','name',"Prescriptions"),
				'diseases' : fields.one2many ('dental.patient.disease', 'name', 'Diseases'),
				'critical_info' : fields.text ('Important disease, allergy or procedures information',help="Write any important information on the patient's disease, surgeries, allergies, ..."),
				'evaluation_ids' : fields.one2many ('dental.patient.evaluation','name','Evaluation'),
				'general_info' : fields.text ('General Information',help="General information about the patient"),

	}

	_defaults={
		'patient_id': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'dental.patient'),
		'd18': 1,
		'd17': 1,
		'd16': 1,
		'd15': 1,
		'd14': 1,
		'd13': 1,
		'd12': 1,
		'd11': 1,
		'd28': 1,
		'd27': 1,
		'd26': 1,
		'd25': 1,
		'd24': 1,
		'd23': 1,
		'd22': 1,
		'd21': 1,
		'd38': 1,
		'd37': 1,
		'd36': 1,
		'd35': 1,
		'd34': 1,
		'd33': 1,
		'd32': 1,
		'd31': 1,
		'd48': 1,
		'd47': 1,
		'd46': 1,
		'd45': 1,
		'd44': 1,
		'd43': 1,
		'd42': 1,
		'd41': 1,
		}
		
	_sql_constraints = [
    	('name_uniq', 'unique (name)', 'The Patient already exists')]

patient_data ()
class speciality (osv.osv):
	_name = "dental.speciality"
	_columns = {
		'name' :fields.char ('Description', size=128, help="ie, Addiction Psychiatry"),
		'code' : fields.char ('Code', size=128, help="ie, ADP"),
	}
	_sql_constraints = [
    	('code_uniq', 'unique (name)', 'The Medical Speciality code must be unique')]

speciality ()

class physician_line (osv.osv):
	
	# Array containing different days name
	PHY_DAY = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),        
		]
	
	_name = "dental.physician.line"
	_description = "Information about doctor availability"
	def create(self, cr, uid, vals, context=None):
		print vals
	_columns = {
		'name': fields.selection(PHY_DAY, 'Available Day(s)'),
		'start_time' : fields.float ('Start Time'),
		'end_time' : fields.float ('End Time'),
		'physician_id': fields.many2one('dental.physician', 'Physician',select=True,ondelete='cascade'),		
		}
physician_line ()
class insurance (osv.osv):

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['number','company'], context)
		res = []
		for record in reads:
			name = record['number']
			if record['company']:
				name = record['company'][1] + ': ' +name
			res.append((record['id'], name))
		return res


	_name = "dental.insurance"
	_columns = {
		'name' : fields.many2one ('res.partner','Owner'), 
		'number' : fields.char ('Number', size=64),
		'company' : fields.many2one ('res.partner','Insurance Company'),
		'member_since' : fields.date ('Member since'),
		'member_exp' : fields.date ('Expiration date'),
		'category' : fields.char ('Category', size=64, help="Insurance company plan / category"),
		'type' : fields.selection([
                                ('state','State'),
                                ('labour_union','Labour Union / Syndical'),
                                ('private','Private'),

                                ], 'Insurance Type', select=True),

		'notes' : fields.text ('Extra Info'),

		}
insurance ()
class ethnic_group (osv.osv):
	_name ="dental.ethnicity"
	_columns = {
		'name' : fields.char ('Ethnic group',size=128,required=True),
		'code' : fields.char ('Code',size=64),
		}

ethnic_group ()
# PATIENT VACCINATION INFORMATION

class vaccination (osv.osv):
	def _check_vaccine_expiration_date(self,cr,uid,ids):
		vaccine=self.browse(cr,uid,ids[0])
		if vaccine:
			if vaccine.vaccine_expiration_date < vaccine.date:
				return False
		return True

	def onchange_vaccination_expiration_date(self, cr, uid, ids, vaccine_date, vaccination_expiration_date):
		if not vaccination_expiration_date and vaccine_date:
			return {}
		else:
			v={}
			if vaccination_expiration_date and vaccine_date:
				if vaccination_expiration_date < vaccine_date:
					v = {'vaccine_expiration_date':''}
					exp_message = "EXPIRED VACCINE !! "+ vaccination_expiration_date + "\nPlease Dispose it !!"
					return {'value': v,'warning':{'title':'warning','message': exp_message}}
				else:
					v = {'vaccine_expiration_date':vaccination_expiration_date}
					return {'value': v}
	_name = "dental.vaccination"
	_columns = {
		'name' : fields.many2one ('dental.patient','Patient ID', readonly=True),
		'vaccine' : fields.many2one ('product.product','Name', domain=[('is_vaccine', '=', "1")], help="Vaccine Name. Make sure that the vaccine (product) has all the proper information at product level. Information such as provider, supplier code, tracking number, etc.. This information must always be present. If available, please copy / scan the vaccine leaflet and attach it to this record"),
		'vaccine_expiration_date' : fields.date ('Expiration date'),
		'vaccine_lot' : fields.char ('Lot Number',size=128,help="Please check on the vaccine (product) production lot number and tracking number when available !"),
		'institution' : fields.many2one ('res.partner','Institution', domain=[('is_institution', '=', "1")],help="Medical Center where the patient is being or was vaccinated"),
		'date' : fields.datetime ('Date'),
		'dose' : fields.integer ('Dose Number'),
		'observations' : fields.char ('Observations', size=128),
		}
	_defaults = {
                'dose': lambda *a: 1,
			 	'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
		}

	_constraints = [
        (_check_vaccine_expiration_date, 'WARNING !! EXPIRED VACCINE. PLEASE INFORM THE LOCAL HEALTH AUTHORITIES AND DO NOT USE IT !!', ['vaccine_expiration_date'])
	] 
	_sql_constraints = [
                ('dose_unique', 'unique (name,dose,vaccine)', 'This vaccine dose has been given already to the patient ')
     ]
vaccination ()

class patient_prescription_order (osv.osv):

	_name = "dental.prescription.order"
	_description = "prescription order"

		
	_columns = {
		'name' : fields.many2one ('dental.patient','Patient ID'),
		'prescription_id' : fields.char ('Prescription ID', size=128,required=True, help='Type in the ID of this prescription'),
		'prescription_date' : fields.datetime ('Prescription Date'),
		'user_id' : fields.many2one ('res.users','Prescribing Doctor', readonly=True),
		'pharmacy' : fields.many2one ('res.partner', 'Pharmacy'),
		'notes' : fields.text ('Prescription Notes'),
		}

	_defaults = {
                'prescription_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda obj, cr, uid, context: uid,		
		'prescription_id': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'medical.prescription'),
                }


patient_prescription_order ()

class patient_disease_info (osv.osv):

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		rec_name = 'pathology'
		res = [(r['id'], r[rec_name][1]) for r in self.read(cr, uid, ids, [rec_name], context)]
		return res

	_name = "dental.patient.disease"
	_description = "Disease info"
	_columns = {
		'name' : fields.many2one ('dental.patient','Patient ID',readonly=True),
	
		'disease_severity' : fields.selection ([
			('1_mi','Mild'),
			('2_mo','Moderate'),
			('3_sv','Severe'),
			], 'Severity', select=True),		
		'is_on_treatment' : fields.boolean ('Currently on Treatment'),
		'is_infectious' : fields.boolean ('Infectious Disease',help="Check if the patient has an infectious / transmissible disease"),		
		'short_comment' : fields.char ('Remarks', size=128,help="Brief, one-line remark of the disease. Longer description will go on the Extra info field"),
		'doctor' : fields.many2one('dental.physician','Physician', help="Physician who treated or diagnosed the patient"),
		'diagnosed_date': fields.date ('Date of Diagnosis'),
		'healed_date' : fields.date ('Healed'),
		'is_active' : fields.boolean ('Active disease'),
		'age': fields.integer ('Age when diagnosed',help='Patient age at the moment of the diagnosis. Can be estimative'),
		'pregnancy_warning': fields.boolean ('Pregnancy warning'),
		'weeks_of_pregnancy' : fields.integer ('Contracted in pregnancy week #'),
		'is_allergy' : fields.boolean ('Allergic Disease'),
		'allergy_type' : fields.selection ([
			('da','Drug Allergy'),
			('fa','Food Allergy'),
			('ma','Misc Allergy'),
			('mc','Misc Contraindication'),
			], 'Allergy type', select=True),		
		'treatment_description' : fields.char ('Treatment Description',size=128),
		'date_start_treatment' : fields.date ('Start of treatment'),
		'date_stop_treatment' : fields.date ('End of treatment'),
		'status' : fields.selection ([
			('c','chronic'),
			('s','status quo'),
			('h','healed'),
			('i','improving'),
			('w','worsening'),
			], 'Status of the disease', select=True),
		'extra_info' : fields.text ('Extra Info'),
		}

	_order = 'is_active desc, disease_severity desc, is_infectious desc, is_allergy desc, diagnosed_date desc'

	_defaults = {
		'is_active': lambda *a : True,
                }

patient_disease_info ()
class patient_evaluation (osv.osv):
	def _get_image(self, cr, uid, ids, name, args, context=None):
		result = dict.fromkeys(ids, False)
		for obj in self.browse(cr, uid, ids, context=context):
			result[obj.id] = tools.image_get_resized_images(obj.image, avoid_resize_medium=True)
		return result

	def _set_image(self, cr, uid, id, name, value, args, context=None):
		return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
# Kludge to get patient ID when using one2many fields.
	def onchange_evaluation_date (self, cr, uid, ids,name, patient):
		if not name:
#			pdb.set_trace()
			return {'value': {'name': patient}}


	_name = "dental.patient.evaluation"
	_description = "evaluation"
	_columns = {
		'name' : fields.many2one ('dental.patient','Patient ID'),
                'evaluation_date' : fields.datetime ('Evaluation Date', help="Enter or select the date / ID of the appointment related to this evaluation"),
		'index_plaque' : fields.char('Dental Plaque Index'),
		'evaluation_endtime' : fields.datetime ('End of Evaluation'),
		'next_evaluation' : fields.many2one ('dental.appointment','Next Appointment'),
		'user_id' : fields.many2one ('res.users','Doctor', readonly=True),
		'derived_from' : fields.many2one('dental.physician','Derived from Doctor', help="Physician who escalated / derived the case"), 
		'derived_to' : fields.many2one('dental.physician','Derived to Doctor', help="Physician to whom escalate / derive the case"), 
		'evaluation_type' : fields.selection([
                                ('a','normal'),
                                ('e','Emergencia'),
                                ('i','Rutina'),
                                ], 'Evaluation Type', select=True),
		'chief_complaint' : fields.char ('Chief Complaint', size=128,help='Chief Complaint'),
		'notes_complaint' : fields.text ('Complaint details'),
		'glycemia' : fields.float('Glycemia', help="Last blood glucose level. Can be approximative."),
		'notes' : fields.text ('Notes'),
		'image': fields.binary('Image'),
		'image_medium': fields.function(_get_image, fnct_inv=_set_image,
		string="Image", type="binary", multi="_get_image",
		store={
				'dental.patient.evaluation': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
			help="Medium-sized image of the product. It is automatically "\
					"resized as a 128x128px image, with aspect ratio preserved, "\
					"only when the image exceeds one of those sizes. Use this field in form views or some kanban views."),
		'image_small': fields.function(_get_image, fnct_inv=_set_image, string="Small-sized image", type="binary", multi="_get_image",
            store={'dental.patient.evaluation': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10)}), 
		'partner_id':fields.many2one('res.partner',ondelete='set null', string='patient'),
		'weight' : fields.float('Weight (kg)'),
		'height' : fields.float('Height (cm)'),
		'bmi' : fields.float('Body Mass Index'),

	}

	_defaults = {
		'evaluation_type': lambda *a: 'a',
		'user_id': lambda obj, cr, uid, context: uid,
		'name': lambda self, cr, uid, c: c.get('name', False),
		
        }
patient_evaluation ()




class medicament (osv.osv):

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		rec_name = 'name'
		res = [(r['id'], r[rec_name][1]) for r in self.read(cr, uid, ids, [rec_name], context)]
		return res

	_name = "dental.medicament"
	_columns = {
		'name' : fields.many2one ('product.product','Name', domain=[('is_medicament', '=', "1")],help="Commercial Name"),
		'active_component' : fields.char ('Active component', size=128, help="Active Component"),
		'therapeutic_action' : fields.char ('Therapeutic effect', size=128, help="Therapeutic action"),
		'composition' : fields.text ('Composition',help="Components"),
		'indications' : fields.text ('Indication',help="Indications"),
		'dosage' : fields.text ('Dosage Instructions',help="Dosage / Indications"),
		'overdosage' : fields.text ('Overdosage',help="Overdosage"),
		'pregnancy_warning' : fields.boolean ('Pregnancy Warning', help="Check when the drug can not be taken during pregnancy or lactancy"),
		'pregnancy' : fields.text ('Pregnancy and Lactancy',help="Warnings for Pregnant Women"),
		'presentation' : fields.text ('Presentation',help="Packaging"),
		'adverse_reaction' : fields.text ('Adverse Reactions'),
		'storage' : fields.text ('Storage Conditions'),
		'price' : fields.related ('name','lst_price',type='float',string='Price'),
		'qty_available' : fields.related ('name','qty_available',type='float',string='Quantity Available'),
		'notes' : fields.text ('Extra Info'),
		}

medicament ()

class product_medical (osv.osv):
	_name = "product.product"
	_inherit = "product.product"
	_columns = {
                'is_medicament' : fields.boolean('Medicament', help="Check if the product is a medicament"),
                'is_vaccine' : fields.boolean('Vaccine', help="Check if the product is a vaccine"),
                'is_bed' : fields.boolean('Bed', help="Check if the product is a bed on the medical center"),

	}
product_medical ()
class medication_template (osv.osv):

	_name = "dental.medication.template"
	_description = "Template for medication"
	_columns = {
		'medicament' : fields.many2one ('dental.medicament','Medicament',help="Prescribed Medicament"),
		
		'dose' : fields.integer ('Dose',help="Amount of medication (eg, 250 mg ) each time the patient takes it"),
		'qty' : fields.integer ('x',help="Quantity of units (eg, 2 capsules) of the medicament"),
		'common_dosage' : fields.many2one ('dental.medication.dosage','Frequency',help="Common / standard dosage frequency for this medicament"),
		'frequency' : fields.integer ('Frequency', help="Time in between doses the patient must wait (ie, for 1 pill each 8 hours, put here 8 and select 'hours' in the unit field"),
		'frequency_unit' : fields.selection ([
			('seconds','seconds'),
			('minutes','minutes'),
			('hours','hours'),
			('days','days'),
			('weeks','weeks'),
			('wr','when required'),
			], 'unit', select=True),
		'admin_times' : fields.char  ('Admin hours', size=128, help='Suggested administration hours. For example, at 08:00, 13:00 and 18:00 can be encoded like 08 13 18'),
		'duration' : fields.integer ('Treatment duration',help="Period that the patient must take the medication. in minutes, hours, days, months, years or indefinately"),
		'duration_period' : fields.selection([
                                ('minutes','minutes'),
                                ('hours','hours'),
				('days','days'),
				('months','months'),
				('years','years'),
				('indefinite','indefinite'),
                               ], 'Treatment period',help="Period that the patient must take the medication. in minutes, hours, days, months, years or indefinately", select=True),
		'start_treatment' : fields.datetime ('Start of treatment'),
		'end_treatment' : fields.datetime ('End of treatment'),
		}


medication_template ()	
class medication_dosage (osv.osv):
	_name = "dental.medication.dosage"
	_description = "Medicament Common Dosage combinations"
	_columns = {
		'name': fields.char ('Frequency', size=256, help='Common frequency name'),
		'code': fields.char ('Code', size=64, help='Dosage Code, such as SNOMED, 229798009 = 3 times per day'),
		'abbreviation' : fields.char  ('Abbreviation', size=64, help='Dosage abbreviation, such as tid in the US or tds in the UK'),
		}

medication_dosage ()
class patient_medication (osv.osv):

	_name = "dental.patient.medication"
	_inherit = "dental.medication.template"
	_description = "Patient Medication"
	_columns = {
		'name' : fields.many2one ('dental.patient','Patient ID',readonly=True),
		'doctor' : fields.many2one('dental.physician','Physician', help="Physician who prescribed the medicament"),
		'is_active' : fields.boolean('Active',help="Check this option if the patient is currently taking the medication"),
		'discontinued' :  fields.boolean('Discontinued'),
		'course_completed' : fields.boolean('Course Completed'),
		'discontinued_reason' : fields.char ('Reason for discontinuation', size=128, help="Short description for discontinuing the treatment"),
		'adverse_reaction' : fields.text ('Adverse Reactions',help="Specific side effects or adverse reactions that the patient experienced"),
		'notes' : fields.text ('Extra Info'),
		'patient_id' : fields.many2one('dental.patient','Patient'),		
		}

	_defaults = {
		'is_active': lambda *a : True,
		'start_treatment': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
                'frequency_unit': lambda *a: 'hours',
                'duration_period': lambda *a: 'days',
                'qty': lambda *a: 1,                                                              
                }
	
patient_medication ()

class partner_patient (osv.osv):
	_name = "res.partner"
	_inherit = "res.partner"
	_columns = {
		'date' : fields.date('Partner since',help="Date of activation of the partner or patient"),
		'alias' : fields.char('Alias', size=64),
		'ref': fields.char('ID Number', size=64),
        'is_person' : fields.boolean('Person', help="Check if the partner is a person."),
        'is_patient' : fields.boolean('Patient', help="Check if the partner is a patient"),
        'is_doctor' : fields.boolean('Doctor', help="Check if the partner is a doctor"),
		'is_institution' : fields.boolean ('Institution', help="Check if the partner is a Medical Center"),
		'lastname' : fields.char('Last Name', size=128, help="Last Name"),
		'user_id': fields.many2one('res.users', 'Internal User', help='In Medical is the user (doctor, nurse) that logins into OpenERP that will relate to the patient or family. When the partner is a doctor or a health proffesional, it will be the user that maps the doctor\'s partner name. It must be present.'),
		'relationship' : fields.char('Relationship', size=64, help="Include the relationship with the patient - friend, co-worker, brother, ...- "),		

	}
	_sql_constraints = [
                ('ref_uniq', 'unique (ref)', 'The partner or patient code must be unique')
 		]

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['name', 'lastname'], context)
		res = []
		for record in reads:
			name = record['name']
			if record['lastname']:
				name = record['lastname'] + ', '+name
			res.append((record['id'], name))
		return res


partner_patient ()


class patient_data (osv.osv):
	_name = "dental.patient"
	_inherit = "dental.patient"

	_columns = {
		'receivable' : fields.related('name','credit',type='float',string='Receivable',help='Total amount this patient owes you',readonly=True),
	}
patient_data()

# Add Invoicing information to the Appointment

class appointment (osv.osv):
	_name = "dental.appointment"
	_inherit = "dental.appointment"



	_columns = {

	}


appointment ()


