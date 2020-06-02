import feedparser
from flask import Flask, render_template
from flask import request
import pandas as pd
import numpy as np
import pickle
from flask_bootstrap import Bootstrap
import json
import requests
from flask_googlemaps import GoogleMaps, Map
from flask_moment import Moment
from flask_wtf import Form
from wtforms import StringField, SubmitField, BooleanField
from wtforms import IntegerField, SelectField, FloatField, PasswordField
from wtforms.validators import Required
from flask_script import Manager
import os
import psycopg2
import urlparse
from sqlalchemy import create_engine



app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

bed_nums = [(str(i),str(i)) for i in [1,2,3]]
bath_nums = [(str(i),str(i)) for i in [1,2,3,4]]


# Getting the Town Name
with open ('townlist.list', 'rb') as fp:
    town_names = pickle.load(fp)

town_types_dict  = {town:i for (i, town) in enumerate(town_names)}


town_names = [(i,i) for i in town_names]



class NameForm(Form):
	address = StringField('Address', validators=[Required()])
	town = SelectField('Town:', choices = town_names)
	sqft = FloatField('SQFT:', validators=[Required()])
	bathrooms = SelectField('# of Bathrooms', choices = bath_nums)
	bedrooms = SelectField('# of Bedrooms', choices = bed_nums)
	

	# Booleans
	if_deck = BooleanField('Deck')
	if_studio = BooleanField('studio')
	ac = BooleanField('ac')
	cable = BooleanField('cable')
	deck = BooleanField('deck')
	dishw = BooleanField('dishw')
	wifi = BooleanField('wifi')
	laundry_f = BooleanField('laundry_f')
	microw = BooleanField('microw')
	if_pets = BooleanField('if_pets')
	fridge = BooleanField('fridge')
	wash_dry_unit = BooleanField('wash_dry_unit')

	#Submit Clause
	submit = SubmitField('Submit')

class TestNameForm(Form):
	address = StringField('Address', validators=[Required()], default='153 S Washington Ave')
	town = SelectField('Town:', choices = town_names[:2])
	sqft = FloatField('SQFT:', validators=[Required()], default=1000)
	bathrooms = SelectField('# of Bathrooms', choices = bath_nums)
	bedrooms = SelectField('# of Bedrooms', choices = bed_nums)
	

	# Booleans
	if_deck = BooleanField('Deck')
	if_studio = BooleanField('studio')
	ac = BooleanField('ac')
	cable = BooleanField('cable')
	deck = BooleanField('deck')
	dishw = BooleanField('dishw')
	wifi = BooleanField('wifi')
	laundry_f = BooleanField('laundry_f')
	microw = BooleanField('microw')
	if_pets = BooleanField('if_pets')
	fridge = BooleanField('fridge')
	wash_dry_unit = BooleanField('wash_dry_unit')

	#Submit Clause
	submit = SubmitField('Submit')

class SigninForm(Form):
	username = StringField('User Name', validators=[Required()])
	password = PasswordField('Password', validators=[Required()])
	submit = SubmitField('Submit')



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500



GoogleMaps(app, key="AIzaSyCoSG2qHLz1r9Lqe2UydmKnhNQKkprfy1I")
#GoogleMaps(app)







#House map Stuff
urlparse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

engine = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

to_erase = pd.read_sql_query('select * from map_info;', engine)
to_erase = to_erase[to_erase.columns.difference(['index'])]
house_map_data = to_erase.values

house_locations = []

for crime in house_map_data:
    named_crime = {
    'lat': crime[1],
    'lng': crime[0],
    #crime3 is name and crime4 is url
    'infobox': '%s<br>%s'%(crime[2],crime[3])
    }
    house_locations.append(named_crime)





### Passwords
user_password_dict = {'fernando': '1fghfghfgh', 'richman': 'kentshire'}
password_user_dict = {'1fghfghfgh': 'fernando' , 'kentshire': 'richman'}






#Start of Templates                                     

@app.route('/', methods = ['GET', 'POST'])
def home():

	name = None
	signinform = SigninForm()
	form = NameForm()
	try:
		if signinform.validate_on_submit() \
		and (user_password_dict[signinform.username.data.lower()] in ('1fghfghfgh', 'kentshire'))\
		and (password_user_dict[signinform.password.data] in ('fernando', 'richman')):


			if form.validate_on_submit():

				reg_model = pd.read_pickle('amenities_model.pkl')

				sqft = form.sqft.data
				bathrooms = form.bathrooms.data
				bedrooms = form.bedrooms.data
				address = form.address.data
				town = form.town.data
				if_studio = form.if_studio.data
				ac = form.ac.data
				cable = form.cable.data
				deck = form.deck.data
				dishw = form.dishw.data
				wifi = form.wifi.data
				laundry_f = form.laundry_f.data
				microw = form.microw.data
				if_pets = form.if_pets.data
				fridge = form.fridge.data
				wash_dry_unit = form.wash_dry_unit.data


				lat, lng = call_api(address, town)

				x = pd.Series(np.zeros(56))
				x.iloc[52] = int(bathrooms)
				x.iloc[53] = int(bedrooms)
				x.iloc[54] = if_studio
				x.iloc[55] = sqft
				x.iloc[town_types_dict[town]] = 1

				x.iloc[42] = ac
				x.iloc[43] = cable
				x.iloc[44] = deck
				x.iloc[45] = dishw
				x.iloc[46] = wifi
				x.iloc[47] = laundry_f
				x.iloc[48] = microw
				x.iloc[49] = if_pets
				x.iloc[50] = fridge
				x.iloc[51] = wash_dry_unit

				amenities_list = ['Air Conditioning','Cable Ready','Deck','Dishwasher',
								'High Speed Internet Access','Laundry Facility','Microwave','Pets OK',
								'Refrigerator','Washer/Dryer in Unit']



				prediction = round(np.exp(reg_model.predict(x.values.reshape(1, -1))[0]),2)



				test_map = Map(identifier="test_map",lat=lat,lng=lng,markers= house_locations,
							style = "height:500px;width:100%;margin:0;", )



				# return render_template('hello2.html', form = form,sqft = sqft, if_deck = if_deck,
				# 						bathrooms = bathrooms, address = address, town = town)



				# return render_template('hello2.html', prediction = prediction,
				# 						 form = form, test_map = test_map)

				return render_template('results.html', prediction = prediction,
					form = form, test_map = test_map,ac = ac,cable = cable,deck = deck,
					dishw = dishw,wifi = wifi,laundry_f = laundry_f,microw = microw,
					if_pets = if_pets,fridge = fridge,wash_dry_unit = wash_dry_unit,
					bathrooms = bathrooms, bedrooms = bedrooms, sqft = sqft, town = town, 
					if_studio = if_studio)
			else:
				return render_template('index.html', form=form)



		else:
			return render_template('jumbotron.html', signinform=signinform, response = '')

	except:
		return render_template('jumbotron.html', signinform=signinform, response = 'Wrong Username or Password')



@app.route('/test', methods = ['GET', 'POST'])
def test():
	name = None
	form = TestNameForm()

	if form.validate_on_submit():
		reg_model = pd.read_pickle('amenities_model.pkl')

		sqft = form.sqft.data
		bathrooms = form.bathrooms.data
		bedrooms = form.bedrooms.data
		address = form.address.data
		town = form.town.data
		if_studio = form.if_studio.data
		ac = form.ac.data
		cable = form.cable.data
		deck = form.deck.data
		dishw = form.dishw.data
		wifi = form.wifi.data
		laundry_f = form.laundry_f.data
		microw = form.microw.data
		if_pets = form.if_pets.data
		fridge = form.fridge.data
		wash_dry_unit = form.wash_dry_unit.data


		lat, lng = call_api(address, town)

		x = pd.Series(np.zeros(56))
		x.iloc[52] = int(bathrooms)
		x.iloc[53] = int(bedrooms)
		x.iloc[54] = if_studio
		x.iloc[55] = sqft
		x.iloc[town_types_dict[town]] = 1

		x.iloc[42] = ac
		x.iloc[43] = cable
		x.iloc[44] = deck
		x.iloc[45] = dishw
		x.iloc[46] = wifi
		x.iloc[47] = laundry_f
		x.iloc[48] = microw
		x.iloc[49] = if_pets
		x.iloc[50] = fridge
		x.iloc[51] = wash_dry_unit

		amenities_list = ['Air Conditioning','Cable Ready','Deck','Dishwasher',
						'High Speed Internet Access','Laundry Facility','Microwave','Pets OK',
						'Refrigerator','Washer/Dryer in Unit']



		prediction = round(np.exp(reg_model.predict(x.values.reshape(1, -1))[0]),2)



		test_map = Map(identifier="test_map",lat=lat,lng=lng,markers= house_locations,
					style = "height:500px;width:100%;margin:0;", )



		# return render_template('hello2.html', form = form,sqft = sqft, if_deck = if_deck,
		# 						bathrooms = bathrooms, address = address, town = town)



		# return render_template('hello2.html', prediction = prediction,
		# 						 form = form, test_map = test_map)

		return render_template('results.html', prediction = prediction,
			form = form, test_map = test_map,ac = ac,cable = cable,deck = deck,
			dishw = dishw,wifi = wifi,laundry_f = laundry_f,microw = microw,
			if_pets = if_pets,fridge = fridge,wash_dry_unit = wash_dry_unit,
			bathrooms = bathrooms, bedrooms = bedrooms, sqft = sqft, town = town, 
			if_studio = if_studio)
	else:
		return render_template('index.html', form=form)



def get_values(query):
	output = request.args.get(query)
	if not output:
		output = defaults[query]
	return output

def call_api(address, town):
	api_address = address.replace(' ', '+')
	api_town = '+' + town.replace(' ', '+')
	key = 'AIzaSyD_-p5_2cUMt_wfpetjt0-OoVI42da6ASk'

	api_url = 'https://maps.googleapis.com/maps/api/geocode/json?address=%s,%s,+NJ&key=%s'%(api_address,api_town, key)

	response = requests.get(api_url, verify = False).json()['results'][0]['geometry']['location']

	return response['lat'], response['lng']




if __name__ =='__main__':
	app.debug = True
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)