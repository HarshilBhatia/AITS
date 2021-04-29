from flask import Flask, flash, render_template, request, redirect, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_table import Table, Col, LinkCol
from s3_demo import list_files, download_file, upload_file
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
BUCKET = "harshilbhatia"

ENV = 'dev'
if(ENV == 'dev'):
	app.debug = True
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost/userlists'
else:
	app.debug = False
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vglukmsdgeioml:30d4438d7342b57d30b758fd2ff967e7e920c10f55d1f075a2ff40995802383c@ec2-34-200-94-86.compute-1.amazonaws.com:5432/d7c44hvch8srl8'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PMSusers(db.Model):
	__tablename__ = 'pmsusers'
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.String(200), unique=True)
	password = db.Column(db.String(200))
	email = db.Column(db.String(200), unique=True)
	mobile = db.Column(db.BigInteger, unique=True)
	approval = db.Column(db.Integer)
	
	def __init__(self, user, password, email, mobile, approval):
		self.user = user
		self.password = password
		self.email = email
		self.mobile = mobile
		self.approval = approval

class UserAnalytics(db.Model):
	__tablename__ = 'useranalytics'
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.String(200), unique=True)
	holding = db.Column(db.Float(200))
	bookedpnl = db.Column(db.Float(200), unique=True)
	positionalpnl = db.Column(db.Float, unique=True)
	charges = db.Column(db.Float, unique=True)
	
	def __init__(self, user, holding, bookedpnl, positionalpnl, charges):
		self.user = user
		self.holding = holding
		self.bookedpnl = bookedpnl
		self.positionalpnl = positionalpnl
		self.charges = charges

class Results(Table):
    id = Col('id', show=False)
    user = Col('user')
    email = Col('email')
    mobile = Col('mobile')
    approval = Col('approval')	
    edit = LinkCol('Edit', 'edit', url_kwargs=dict(id='id'))
    
@app.route('/')
def home():
	return render_template('login.html')
	
@app.route('/readmin')
def readmin():
	results = []
	qry = db.session.query(PMSusers)
	results = qry.all()
	table = Results(results)
	table.border = True
	table.html_attrs = {"style":"width:90%; border-color:gray; border-collapse: collapse; text-align: center;"}
	print(table.html_attrs)
	return render_template('admin.html', table = table)

@app.route('/login', methods=['POST'])
def login():
	return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
	return render_template('signup.html')
	
'''
@app.route('/login_success')
def login_success():
	return render_template('login_success.html')	
'''
	
@app.route('/item/<int:id>', methods=['get', 'post'])
def edit(id):
	qry = db.session.query(PMSusers).filter(PMSusers.id==id)
	client = qry.first()
	print(client.approval)
	if client and client.user != "admin":
		if(client.approval == 0):
			client.approval = 1
		else:
			client.approval = 0
		db.session.commit()
		print(client)
		return redirect('/readmin')
	return 'error loading #{id}'.format(id=id)		

@app.route('/submitlogin', methods=['POST'])
def submitlogin():
	if request.method == 'POST':
		user = request.form['username']
		pwd = request.form['password']
		if(user == "" or pwd == ""):
			return render_template('login.html', message='Please enter required fields')
		if db.session.query(PMSusers).filter(PMSusers.user == user).count() == 0:
			return render_template('login.html', message='Please enter correct username')
		else:
			temp = db.session.query(PMSusers).filter(PMSusers.user==user).first()
			#print(temp)
			if temp.user == "admin" and temp.password == pwd:
				results = []
				qry = db.session.query(PMSusers)
				results = qry.all()
				table = Results(results)
				table.border = True
				table.html_attrs = {"style":"width:90%; border-color:gray; border-collapse: collapse; text-align: center;"}
				print(table.html_attrs)
				return render_template('admin.html', table = table)
			if temp.password == pwd:
				if(temp.approval == 1):
					return redirect('/storage')
				else:
					return render_template('login.html', message='User is not approved')
			else:
				return render_template('login.html', message='Incorrect password')
		

@app.route('/submitsignup', methods=['POST'])
def submitsignup():
	if request.method == 'POST':
		user = request.form['username']
		email = request.form['emailid']
		mobile = request.form['mobile']
		pwd = request.form['password']
		repwd = request.form['repassword']
		#print(user, pwd)
		if(user == "" or pwd == "" or repwd == ""):
			return render_template('signup.html', message='Please enter required fields')
		if(pwd != repwd):
			return render_template('signup.html', message='The passwords do not match')
		
		if(db.session.query(PMSusers).filter(PMSusers.user == user).count() == 0 and db.session.query(PMSusers).filter(PMSusers.email == email).count() == 0 and db.session.query(PMSusers).filter(PMSusers.mobile == mobile).count() == 0):
			approval = 0
			data = PMSusers(user,pwd,email,mobile,approval)
			db.session.add(data)
			db.session.commit()
			return render_template('success.html')
		elif db.session.query(PMSusers).filter(PMSusers.user == user).count() > 0:
			return render_template('signup.html', message='Username already exists')
		elif db.session.query(PMSusers).filter(PMSusers.email == email).count() > 0:
			return render_template('signup.html', message='Email-Id already exists')
		else:
			return render_template('signup.html', message='Mobile number already exists')
		
@app.route("/storage")
def storage():
    contents = list_files(BUCKET)
    return render_template('storage.html', contents=contents)

@app.route("/upload", methods=['POST'])
# POST method.
def upload():
    if request.method == "POST":
        f = request.files['file']
        f.save(f.filename)
        print(f)
        #change as per the user ? we can
        upload_file(f"{f.filename}", BUCKET)
        return redirect("/storage")

@app.route("/download/<filename>", methods=['GET'])
def download(filename):
    if request.method == 'GET':
        output = download_file(filename, BUCKET)
        return send_file(output, as_attachment=True)
        
if __name__ == '__main__':
	app.run()
