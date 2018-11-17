import time
import os
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash
from models import db, Owner, Staff, Customer, Event 

# create our little application :)
app = Flask(__name__)

boss = {"owner":"pass"}

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'catering.db')

app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	db.create_all()
	print('Initialized the database.')		#setting up dummys to test
	"""
	db.session.add(Customer("alice", "1"))
	db.session.add(Customer("bob", "2"))
	db.session.add(Customer("charlie", "3"))
	
	db.session.add(Staff("thing1", "4"))
	db.session.add(Staff("thing2", "5"))
	
	db.session.commit()
	"""
	
####remember to delete this command later	
@app.cli.command('deletedb')
def initdb_command():
	"""delete the database tables."""
	print('deleting db')
	db.drop_all()

#might want to consider getting rid of the get_id methods, kind of useless here 	
def get_owner_id(username):
	"""Convenience method to look up the id for a username."""
	rv = Owner.query.filter_by(username=username).first()
	return rv.user_id if rv else None

def get_staff_id(username):
	"""Convenience method to look up the id for a username."""
	rv = Staff.query.filter_by(username=username).first()
	return rv.user_id if rv else None

def get_customer_id(username):
	"""Convenience method to look up the id for a username."""
	rv = Customer.query.filter_by(username=username).first()
	return rv.user_id if rv else None

def get_event_id(event_name):
	"""Convenience method to look up the id for a username."""
	rv = Event.query.filter_by(event_name=event_name).first()
	return rv.event_id if rv else None


def gravatar_url(email, size=80):
	"""Return the gravatar image for the given email address."""
	return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
		(md5(email.strip().lower().encode('utf-8')).hexdigest(), size)

def displayResult(num, res):
	print("\nQ{}:\n".format(num), res, "\n\n")
	
@app.cli.command('check')
def default():
	"""demonstrates model queries and relationships"""
	# queries
	tmp = Owner.query.get(1)
	displayResult(1, tmp)
	displayResult(9, Owner.query.filter(Owner.user_id < 3).all())
	displayResult(10, Owner.query)


		
@app.before_request
def before_request():
	g.customer = None
	g.owner = None
	g.staff = None
	if 'user_id' in session:			#to check if someone alrady signed in
		if 'CustomerIndicator' in session:
			g.customer = Customer.query.filter_by(user_id=session['user_id']).first()
		if 'ownerIndicator' in session:
			g.owner = Owner.query.filter_by(user_id=session['user_id']).first()
		if 'staffIndicator' in session:	
			g.staff = Staff.query.filter_by(user_id=session['user_id']).first()

@app.route("/login/", methods=["GET", "POST"])			#3 separate urls to determine whether staff, owner or customer
def login():
	if g.customer:
		return redirect(url_for('timeline'))
	if g.owner:
		return redirect(url_for('timeline'))
	if g.staff:
		return redirect(url_for('timeline'))	
	error = None
	
	if request.method == 'POST':						#fixed some table issues, and now works
		if request.form['loginType'] == "customer":
			user = Customer.query.filter_by(username=request.form['username']).first()			#get custmer
			if user is None:
				error = 'Invalid username'
			elif not check_password_hash(user.pw_hash, request.form['password']):
				error = 'Invalid password'
			else:
				session['user_id'] = user.user_id		#logged in
				session['CustomerIndicator'] = 1;
				return redirect(url_for('timeline'))
			
		if request.form['loginType'] == "owner":
			if request.form["username"] in boss and boss[request.form["username"]] == request.form["password"]:  
				if get_owner_id(request.form['username']) is None:
					db.session.add(Owner(request.form['username'], generate_password_hash(request.form['password'])))
					db.session.commit()
				user = Owner.query.filter_by(username=request.form['username']).first()
				session['user_id'] = user.user_id
				session['ownerIndicator'] = 1
				return redirect(url_for('timeline'))
			
		if request.form['loginType'] == "staff":
			user = Staff.query.filter_by(username=request.form['username']).first()		#the staff log in
			if user is None:
				error = 'Invalid username'
			elif not check_password_hash(user.pw_hash, request.form['password']):
				error = 'Invalid password'
			else:
				session['user_id'] = user.user_id		
				session['staffIndicator'] = 1;
				return redirect(url_for('timeline'))
				
	return render_template('login.html', error=error)
	
@app.route('/')
def timeline():
	"""Shows a users timeline or if no user is logged in it will
	redirect to the public timeline.  This timeline shows the user's
	messages as well as all the messages of followed users.
	"""
	if g.customer:
		u = Customer.query.filter_by(user_id=session['user_id']).first()		# go to customer's timeline
		timeline_ids = [u.user_id]				
		events = Event.query.filter(Event.author_id.in_(timeline_ids)).order_by(Event.event_month.desc()).limit(PER_PAGE).all()
		return render_template('timeline.html', events = events, username = g.customer.username )
	elif g.staff:
		u = Staff.query.filter_by(user_id=session['user_id']).first()			# staff timeline
		timeline_ids = [u.user_id]		
		sign_events = []
		available_events = []
		all_events = Event.query.all()
		for event in all_events:
			for worker in event.worked_on:					#get the singed up events for each workers
				if worker.user_id == g.staff.user_id:
					sign_events.append( event )				#append the event and send it to the timeline
					
		for event in all_events:
			if event not in sign_events and event.not_has_3_staff() :			#all the avavilble events for the workers has to be those that haven't been signed up, and have less than 3 staff
				available_events.append( event )
	
		return render_template('timeline.html', sign_events = sign_events, available_events = available_events, username = g.staff.username )
	elif g.owner:
		events = Event.query.all()
		return render_template('timeline.html', events = events )
	else:		
		return redirect(url_for('public_timeline'))

				
@app.route('/public')
def public_timeline():															#public timelnie
	"""Displays the latest messages of all users."""
	return render_template('timeline.html')
	
@app.route('/<username><eveID>/sign_event')
def sign_event(username,eveID):
	"""Adds the current user as follower of the given user."""
	if not g.staff:
		abort(401)
	staff_id = get_staff_id(username)						
	if staff_id is None:
		abort(404)
		
	staff = Staff.query.filter_by(user_id = staff_id).first()
	Event.query.filter_by(event_id=eveID).first().worked_on.append(staff)			
	db.session.commit()
	
	u = Staff.query.filter_by(user_id=session['user_id']).first()		# staff wants to see they has signed up for and a list of event they can sign up
	timeline_ids = [u.user_id]		
	available_events = []
	sign_events = []
	all_events = Event.query.all()
	for event in all_events:
		for worker in event.worked_on:					
			if worker.user_id == g.staff.user_id:
				sign_events.append( event )				
				
	for event in all_events:
		if event not in sign_events and event.not_has_3_staff() :			
			available_events.append( event )
			
		
	return render_template('timeline.html', sign_events = sign_events, available_events = available_events, username = g.staff.username )
	
	
@app.route('/register', methods=['GET', 'POST'])			
def register():
	"""Registers the user."""
	if g.customer:
		return redirect(url_for('timeline'))
	error = None
	if request.method == 'POST':
		if g.owner:
			if not request.form['theUsername']:
				error = 'You have to enter a username'
			elif not request.form['password']:
				error = 'You have to enter a password'
			elif request.form['password'] != request.form['password2']:
				error = 'The two passwords do not match'
			elif get_staff_id(request.form['theUsername']) is not None:
				error = 'The username is already taken'
			else:
				db.session.add(Staff(request.form['theUsername'], generate_password_hash(request.form['password'])))
				db.session.commit()
				flash('You were successfully registered and can login now')
				return redirect(url_for('login'))
		else:
			if not request.form['theUsername']:
				error = 'You have to enter a username'
			elif not request.form['password']:
				error = 'You have to enter a password'
			elif request.form['password'] != request.form['password2']:
				error = 'The two passwords do not match'
			elif get_customer_id(request.form['theUsername']) is not None:
				error = 'The username is already taken'
			else:
				db.session.add(Customer(request.form['theUsername'], generate_password_hash(request.form['password'])))
				db.session.commit()
				flash('You were successfully registered and can login now')
				return redirect(url_for('login'))
	return render_template('register.html', error=error)


@app.route('/<username>')		
def user_timeline(username):					#both customers and staff can access the user_timeline
	"""Display's a users tweets."""
	profile_user = Customer.query.filter_by(username=username).first()
	if profile_user is None:
		abort(404)
	sign_on = False
	if g.staff:				
		eve = Event.query.filter_by(author_id=profile_user.user_id).order_by(Event.event_month.desc()).limit(PER_PAGE).first()			
		for f in eve.worked_on:
			if (f is not None):
				sign_on = True	
	
	return render_template('timeline.html',sign_on = sign_on, eveID = eve.event_id, event=eve, profile_user=profile_user)
		
@app.route('/add_event', methods=['POST'])																
def add_event():																						#need to add a time checker here to make sure the events time don't duplicate	
	"""Registers a new message for the user."""																
	if 'user_id' not in session:
		abort(401)		
	if request.form['text']:
			dateDuplicate = False 
			all_events = Event.query.all()
			for event in all_events:
				if event.event_month == request.form['event_month'] and event.event_date == request.form['event_date'] and event.event_year == request.form['event_year']:
					dateDuplicate = True
			if	not dateDuplicate:
				db.session.add(Event(session['user_id'], request.form['text'], request.form['event_date'], request.form['event_month'], request.form['event_year']  ))	
				db.session.commit()
				session['eventSigned'] = 1
			else:																						#need to specify here the events are the events related to the customer
				costumer_events = Event.query.filter_by(author_id = session[ 'user_id' ] ).order_by(Event.event_month.desc()).limit(PER_PAGE).all()
				username = Customer.query.filter_by(user_id = session[ 'user_id' ] ).first().username
				return render_template('timeline.html',dateDuplicate = dateDuplicate, events = costumer_events)
				
	return redirect(url_for('timeline'))
	
@app.route('/<user_id>/cancel_event')															#cancel_event
def cancel_event(user_id):	
	"""Registers a new message for the user."""
	theEve = Event.query.filter_by(author_id = user_id).first()		
	db.session.delete(theEve)
	db.session.commit()
	flash('Your event was deleted')
	return redirect(url_for('timeline'))	
	
@app.route("/logout/")
def logout():
	flash('You were logged out')
	session.pop('user_id', None)
	session.pop('staffIndicator', None)
	session.pop('ownerIndicator', None)
	session.pop('CustomerIndicator', None)

	return redirect(url_for('public_timeline'))


app.jinja_env.filters['gravatar'] = gravatar_url
