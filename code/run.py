''' Saem Jeon, sj846@drexel.edu
CS530: GUI, Project '''

from flask import Flask, render_template, send_file, jsonify, request, g, redirect, session, make_response
from passlib.hash import pbkdf2_sha256
import json, csv, requests
import os
from db import Database
from uszipcode import Zipcode

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = Database()
	return db


@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

# Handle the index (home) page
@app.route('/')
def index():
	return render_template('index.html')

# Handle Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
	msg = None
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		if email and password:
			user = get_db().get_user(email)
			if user:
				if pbkdf2_sha256.verify(password, user['encrypted_password']):
					session['user'] = user
					return redirect('/my_collection')
				else:
					msg = "Email or password you entered is incorrect."
		else:
			msg = "Email or password you entered is incorrect."
	return render_template('login.html', message=msg)

# Log out functionality
@app.route('/logout')
def logout():
	session.pop('user', None)
	return redirect('/')

# Handle Create an Account page
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
	msg = None
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		password = request.form['password']
		dob = request.form['dob']
		artist = request.form['artist']
		member = request.form['member']
		if name and email and password and dob and artist and member:
			if get_db().get_user(email):
				msg = "Account with the provided email already exists"
			else:
				encrypted_password = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)
				get_db().create_account(name, email, encrypted_password, dob, artist, member)
				return redirect('/login')
		else:
			msg = "Please enter all the information"
	return render_template('create_account.html', message=msg)


# Handle Edit My Pop page
@app.route('/edit_my_pop', methods=['GET', 'POST'])
def edit_my_pop():
	if request.method == 'POST':
		artist = request.form['artist']
		member = request.form['member']
		city = request.form['city']
		state = request.form['state']
		zipcode = request.form['zipcode']
		distance = request.form['distance']
		language = request.form['language']
		user = session['user']
		if artist and member and city and state and zipcode and language:
			get_db().update_profile(artist, member, city, state, zipcode, distance, language, user['user_id'])
			return redirect('my_collection')
	return render_template('edit_my_pop.html')

# Handle My Collection page
@app.route('/my_collection')
def my_collection():
	return render_template('my_collection.html')

# Handle Buy page
@app.route('/buy', methods=['GET', 'POST'])
def buy():
	if request.method == "POST":
		artist = request.form['artist']
		sell_type = request.form['type']
		album = request.form['albums']
		member = request.form['members']
		delivery = request.form['delivery']
		price = request.form['price']
		products = get_db().applyFilter(artist, sell_type, album, member, price, delivery)
	else:
		products = get_db().getProducts()
	if products:
		for i in products:
			for j in range(len(products[i])):
				if products[i][j] is None:
					products[i][j] = 99999
	else:
		products = {}
	return render_template('buy.html', data = products)

# Handle Sell page
@app.route('/sell', methods=['GET', 'POST'])
def sell():
	if request.method == 'POST':
		artist = request.form['artist']
		sell_type = request.form['type']
		album = request.form['albums']
		member = request.form['members']
		delivery = request.form['delivery']
		zipcode = request.form['zipcode']
		distance = request.form['distance']
		fee = request.form['fee']
		price = request.form['price']
		user = session['user']
		if sell_type == "1":
			if delivery == "1":
				if artist and album and zipcode and distance and price:
					get_db().addProduct(user['user_id'], artist, sell_type, album, None, delivery, zipcode, distance, None, price, 0, 0)
			elif delivery == "2":
				if artist and album and price:
					get_db().addProduct(user['user_id'], artist, sell_type, album, None, delivery, None, None, None, price, 0, 0)
			else:
				if artist and album and fee and price:
					get_db().addProduct(user['user_id'], artist, sell_type, album, None, delivery, None, None, fee, price, 0, 0)
		else:
			if delivery == "1":
				if artist and member and zipcode and distance and price:
					get_db().addProduct(user['user_id'], artist, sell_type, album, member, delivery, zipcode, distance, None, price, 0, 0)
			elif delivery == "2":
				if artist and member and price:
					get_db().addProduct(user['user_id'], artist, sell_type, album, member, delivery, None, None, None, price, 0, 0)
			else:
				if artist and member and fee and price:
					get_db().addProduct(user['user_id'], artist, sell_type, album, member, delivery, None, None, fee, price, 0, 0)
		return redirect('my_collection')
	return render_template('sell.html')

# Handle Shopping Cart page
@app.route('/cart', methods=['GET', 'POST'])
def cart():
	return render_template('cart.html')

# Handle any files that begin "/course" by loading from the course directory
@app.route('/course/<path:path>')
def base_static(path):
	return send_file(os.path.join(app.root_path, '..', 'course', path))

# # Handle any unhandled filename by loading its template
@app.route('/<name>')
def generic(name):
	return render_template(name + '.html')

# Any additional handlers that go beyond simply loading a template
# (e.g., a handler that needs to pass data to a template) can be added here
# Function to return content from data.txt
@app.route('/api/data')
def api_data():
	with open('data.txt', 'r') as f:
		content = f.read()
		# Add braceks to make it a list
		content = "[" + content + "]"
		# Convert string to list
		data = {"content": eval(content)}
	return data

@app.route('/api/get_user_profile')
def api_profile():
	user = session['user']
	profile = get_db().get_profile(user['user_id'])
	return profile

@app.route('/api/get_groups')
def api_groups():
	groups = get_db().get_groups()
	return groups

@app.route('/api/get_members/<int:group_id>')
def api_members(group_id):
	members = get_db().get_members(group_id)
	return members

@app.route('/api/get_my_pop')
def api_my_pop():
	user = session['user']
	pop = get_db().get_my_pop(user['user_id'])
	return pop

@app.route('/api/get_albums/<int:group_id>')
def api_albums(group_id):
	user = session['user']
	albums = get_db().getAlbums(user['user_id'], group_id)
	return albums

@app.route('/api/get_all_albums')
def api_all_albums():
	albums = {}
	with open('../code/db/albums.csv') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		for row in csv_reader:
			if row[0] in albums:
				albums[row[0]].append(row)
			else:
				albums[row[0]] = [row]
	return albums

@app.route('/api/get_all_members')
def api_all_members():
	members = {}
	with open('../code/db/members.csv') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		for row in csv_reader:
			members[row[0]] = [row]
	return members

@app.route('/api/update_album/<int:group_id>/<int:album_id>')
def api_update_album(group_id, album_id):
	user = session['user']
	get_db().updateAlbum(user['user_id'], group_id, album_id)
	return "Success"

@app.route('/api/get_photos/<int:group_id>/<int:member_id>')
def api_photos(group_id, member_id):
	user = session['user']
	photos = get_db().getPhotos(user['user_id'], group_id, member_id)
	return photos

@app.route('/api/update_photo/<int:group_id>/<int:member_id>/<int:photo_id>')
def api_update_photo(group_id, member_id, photo_id):
	user = session['user']
	get_db().updatePhoto(user['user_id'], group_id, member_id, photo_id)
	return "Success"

@app.route('/api/get_products')
def api_get_products():
	products = get_db().getProducts()
	return products

@app.route('/api/add_to_cart/<int:product_id>')
def api_add_to_cart(product_id):
	user = session['user']
	get_db().addToCart(user['user_id'], product_id)
	return "Sucess"

@app.route('/api/get_shopping_cart')
def api_shopping_cart():
	user = session['user']
	products = get_db().getShoppingCart(user['user_id'])
	return products

@app.route('/api/get_selling')
def api_get_selling():
	user = session['user']
	products = get_db().getMySelling(user['user_id'])
	return products

@app.route('/api/remove_cart/<int:product_id>')
def api_remove_cart(product_id):
	user = session['user']
	get_db().removeFromCart(user['user_id'], product_id)
	return "Success"

@app.route('/api/buy_product/<int:product_id>')
def api_buy_product(product_id):
	user = session['user']
	get_db().buyProduct(user['user_id'], product_id)
	return "Success"

@app.route('/api/get_order_history')
def api_order_history():
	user = session['user']
	products = get_db().getOrderHistory(user['user_id'])
	return products

@app.route('/api/confirm_order/<int:product_id>')
def api_confirm_order(product_id):
	user = session['user']
	get_db().confirmOrder(user['user_id'], product_id)
	return "Success"

if __name__ == "__main__":
	app.run(host='127.0.0.1', port=8080, debug=True)
