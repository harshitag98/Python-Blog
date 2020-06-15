from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import math
import json

with open('config.json', 'r') as con:
    params = json.load(con)['params']

app = Flask(__name__)
app.secret_key = 'secret_key'

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['mail_user'],
    MAIL_PASSWORD=params['mail_pass']
)
mail = Mail(app)

if(params['local_server']==True):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    sub_heading = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/params['no_of_posts'])
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*params['no_of_posts'] : (page-1)*params['no_of_posts']+params['no_of_posts']]
    if(page==1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page==last):
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if('user' in session and session['user']==params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if(request.method=="POST"):
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username==params['admin_user'] and userpass==params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    return render_template('login.html', params=params)

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if('user' in session and session['user']==params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/logout")
def logout():
    if('user' in session and session['user']==params['admin_user']):
        session.pop('user')
        return redirect('/dashboard')

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if('user' in session and session['user']==params['admin_user']):
        if(request.method=="POST"):
            new_title = request.form.get('title')
            new_sub_heading = request.form.get('sub_heading')
            new_slug = request.form.get('slug')
            new_content = request.form.get('content')
            date = datetime.now()
            if(sno=='0'):
                add_post = Posts(title=new_title, sub_heading=new_sub_heading, slug=new_slug, content=new_content, date=date)
                db.session.add(add_post)
                db.session.commit()
                return redirect('/edit/'+sno)
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = new_title
                post.sub_heading = new_sub_heading
                post.slug = new_slug
                post.content = new_content
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)



@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method=="POST"):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('message')
        entry = Contacts(name=name, email=email, phone_num=phone, message=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        # mail.send_message("New message from "+name ,
        #                   sender = email,
        #                   recipients = [params['mail_user']],
        #                   body = msg + "\n" + phone
        #                   )
        flash("Thanks for contacting us. We will get back to you soon !!", "success")
    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

app.run(debug=True)
