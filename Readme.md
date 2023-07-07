note this project needs to install werkzeug, flask_sqlalchemy, and flask in order to make it work. and the command should be run in flask environment.

users need to initialize their flask db first, such as flask --app catering.py initdb
and then the users need to run the main program, such as flask --app catering.py run

this program uses model view controller architecture, users can create customer, owner and staff to sign in. customers can create events based on time, the owner can assign
staffs to complete the events, and the staff need to complete events in time.
