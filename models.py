from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customer(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False)
	pw_hash = db.Column(db.String(64), nullable=False)
	joinedEve = db.relationship('Event', backref='joiner')			#1 to many relationship for customers and events
	
	def __init__(self, username, pw_hash):
			self.username = username
			self.pw_hash = pw_hash

	def __repr__(self):
			return '<Customer {}'.format(self.username)

####many to many
class Event(db.Model):
	event_id = db.Column(db.Integer, primary_key=True)
	author_id = db.Column(db.Integer, db.ForeignKey('customer.user_id'), nullable=False)			
	text = db.Column(db.Text, nullable=False)
	event_year = db.Column(db.String(4))
	event_month = db.Column(db.String(2))
	event_date = db.Column(db.String(2))
	worked_on = db.relationship('Staff', secondary='worked_on',  backref=db.backref('worked_by', lazy='dynamic'), lazy='dynamic')	
	
	def has_staff(self):
		count = 0
		for worker in self.worked_on:
			count = count + 1
		if count > 0:
			return True
		return False	
	
	def not_has_3_staff(self):
		count = 0
		for worker in self.worked_on:
			count = count + 1
		if count >= 3:
			return False
		return True 
		
	def __init__(self, author_id, text, event_date, event_month, event_year):
		self.author_id = author_id
		self.text = text
		self.event_date = event_date
		self.event_month = event_month
		self.event_year = event_year
					
	def _repr_(self):
		return '<Event {}'.format(self.event_id)

worked_on  = db.Table('worked_on',
    db.Column('event_id', db.Integer, db.ForeignKey('event.event_id')),
	db.Column('staff_id', db.Integer, db.ForeignKey('staff.user_id'))
)		
		
class Owner(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False)
	pw_hash = db.Column(db.String(64), nullable=False)
	staff = db.relationship('Staff', backref='boss', lazy='dynamic')							#one to many relationship, corresponding to the customer part
	
	def __init__(self, username, pw_hash ):
			self.username = username
			self.pw_hash = pw_hash
			
	def __repr__(self):
			return '<Owner {}'.format(self.username)
		

class Staff(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False)
	owner_id = db.Column(db.Integer,db.ForeignKey('owner.user_id'))								
	pw_hash = db.Column(db.String(64), nullable=False)

	def __init__(self, username, pw_hash):
			self.username  = username
			self.pw_hash = pw_hash

	def __repr__(self):
			return '<Staff {}'.format(self.username)

