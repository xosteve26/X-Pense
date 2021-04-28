
from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from math import pi

import pandas as pd



from bokeh.plotting import figure, show
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.io import save, output_file
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.palettes import Spectral6


app=Flask(__name__)




app.secret_key = 'a'
  
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = '9CaX90ZO70'
app.config['MYSQL_PASSWORD'] = '3ZvAjIocQr'
app.config['MYSQL_DB'] = '9CaX90ZO70'
mysql = MySQL(app)




@app.route('/home')
@app.route('/')
def home():
    if session['id']:
        session['loggedin']=True
    else:
        session['loggedin']=False
    print("session at home", session)
    return render_template('main.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg=''
    if request.method == 'POST':
        username=request.form['uname']
        password=request.form['pass']
        email=request.form['email']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE username = % s', (username, ))
        account=cursor.fetchone()
        print(account)
        if account:
            msg="Account already exists"
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            session['loggedin']=False
            
            print("session at register else" ,session)
            return render_template('main.html', msg=msg)

    print("session at register final" ,session)
    return render_template('register.html',msg=msg)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = % s AND password = % s', (username, password ))
        account = cursor.fetchone()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        print ("account at login is:",account)
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
    
            print("session at login ",session)
            return render_template('main.html', msg=msg)
            

        else:
            msg="Account doesn't exist"
            print("session at login else" ,session)
            return render_template('main.html', msg=msg)
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    wa=''
    print("initial dash session",session)
    month=["January","February","March","April","May","June","July","August","September","October","November","December"]
    
    
    if session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
        
            cursor.execute("SELECT b_month FROM budget WHERE id=%s", (session['id'],))
            b_m=cursor.fetchone()
            b_m['b_month']=b_m['b_month'].split('-')[1]
            session['b_m']=b_m['b_month']
            print(b_m)
        except:
            pass
        data=[]
        try:
            cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = % s AND monthname(date)=%s', (session['id'], session['b_m'] ))
            data=cursor.fetchall()
            print("data",data)
        except KeyError:
            pass
       
        try:

            cursor.execute('SELECT bamount FROM budget WHERE id = % s', (session['id'], ))
            b=cursor.fetchone()
            print("b is ",b)
        except TypeError:
            b={'bamount': 0}
        
        try:

            cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = % s AND monthname(date)=%s', (session['id'], session['b_m']))
            total=cursor.fetchone()
            print("total",total)
        except KeyError:
            total={'tsum':0}

       
        #cursor.execute("SELECT  DATE_FORMAT(date,'%M') AS dt  FROM expense_a ")
        #dt=cursor.fetchall()
        #print(dt)

        cursor.execute("SELECT DISTINCT MONTHNAME(date) AS 'dt' FROM expense_a WHERE id=%s ", (session['id'],))
        d_m=cursor.fetchall()
        l=[]
        for i in d_m:
            l.append(i['dt'])
        session['d_m']=l
        print("dm is ",l)

        #cursor.execute('SELECT MAX(date) AS mxd, MIN(date) AS mnd FROM expense_a WHERE id=% s', (session['id'],))
        #date=cursor.fetchone()
        #session['mxd']=date['mxd']
        #session['mnd']=date['mnd']
        #print(date['mnd'])
        #print("session after date",session)    
        if b:

            session['budget']=b['bamount']
            bud=session['budget']
            print(session['budget'])
        else:
            flash(u"Please Set Budget First","primary")
            print("session at dashboard else" ,session)
            return render_template('dashboard.html',month=month)
        if data:
            flash(u"Wecome back {}".format(session['username']) , "primary")
            print("session at dashboard if data" ,session)
            return render_template('dashboard.html', data=data,budget=bud, total=int(total['tsum']),month=month,d_m=session['d_m'])
        else:
            flash(u"Please Add Expenses","primary")
        if (total['tsum'] == None):
            return render_template('dashboard.html',total=0,budget=bud,month=month,d_m=session['d_m'])
        else:
            session['total'] = int(total['tsum'])
        
        return render_template('dashboard.html')
    
    else:
        wa='Please login first'       
        return render_template('main.html', wa=wa)
@app.route('/switchmonth/<string:mon>', methods=['GET','POST'])   
def switch_month(mon):
    print(session)
    month=["January","February","March","April","May","June","July","August","September","October","November","December"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    session['b_m']=mon
    print(" mon is ",mon)
    cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = % s AND monthname(date)=%s', (session['id'], mon ))
    data=cursor.fetchall()
    print(data)
    cursor.execute('SELECT bamount FROM budget WHERE id=%s AND b_month LIKE %s', (session['id'], '2021-'+mon,))
    b=cursor.fetchone()
    print("b is ",b)
    cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = % s AND monthname(date)=%s', (session['id'], mon))
    total=cursor.fetchone()
    print("total",total)
    cursor.execute("SELECT DISTINCT MONTHNAME(date) AS 'dt' FROM expense_a WHERE id=%s ", (session['id'],))
    d_m=cursor.fetchall()
    l=[]
    for i in d_m:
        l.append(i['dt'])
    session['d_m']=l
    print("dm is ",l)
    session['budget']=b['bamount']
    bud=session['budget']
    print(session['budget'])
    return render_template('dashboard.html',data=data,budget=bud, total=int(total['tsum']),month=month,d_m=session['d_m'])


@app.route('/setbudget', methods=['GET','POST'])
def budget():
    print("budget",session)
    budget=request.form['budget']
    b_id=session['id']
    b_y = request.form['b_y']
    b_m = request.form['b_m']
    session['b_m']=b_m
    m=b_y+"-"+b_m
    print("month and year is ",b_y,b_m)
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO budget VALUES (NULL,%s, %s, %s)', (b_id,budget,m, ))
    mysql.connection.commit()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM budget WHERE id = % s AND bamount = % s', (b_id, budget ))
    account = cursor.fetchone()
    session['budget']=account['bamount']  
    flash(u"Budget has been set, Now you can proceed to adding expenses","primary")
    print("session at budget " ,session)
    return render_template('dashboard.html', budget=session['budget'], total=0, b_m=session['b_m'],)


@app.route('/updatebudget', methods=['POST'])
def updatebudget():
    new_budget=request.form['updatebudget']
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE budget SET bamount=%s WHERE id=%s',(new_budget,session['id'],))
    mysql.connection.commit()
    flash(u"Budget Updated","success")
    return redirect(url_for('dashboard'))


@app.route('/aexpense', methods=['GET','POST'])
def expense():
    print("expense session",session)
    e_id=session['id']
    amount=request.form['am']
    category=request.form['categ']
    date=request.form['date']
    description=request.form['desc']
    cursor = mysql.connection.cursor()
    print("before commit")
    cursor.execute('INSERT INTO expense_a VALUES(NULL,%s,%s,%s,%s,%s)', (e_id,amount,category,date,description, ))
    mysql.connection.commit()
    print("commit done")
    cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = % s ', (e_id, ))
    ac=cursor.fetchone()
    print("ac is ",ac)
    print("sum done")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT bamount FROM budget WHERE id = % s ', (e_id, ))
    bud=cursor.fetchone()
    if int(ac[0]) > int(bud['bamount']) :
        wa="Warning : You've exceeded your budget"
    print(session)    
    print("before data")   
    cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = %s AND monthname(date)=%s', (session['id'], session['b_m'] ))
    data=cursor.fetchall()
    print("after data",data)
    print("before totoal")
    cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = %s AND monthname(date)=%s ', (session['id'],session['b_m'], ))
    total=cursor.fetchone()
    if total['tsum'] == None:
        total['tsum']=0
    print("total aex",total)
    bud=session['budget']
    print("bud at expense ", bud)
    if data:
            flash("Expense has been added","success")
        
            print("session at aexpense if data" ,session)
            return render_template('dashboard.html', data=data,budget=int(bud), total=int(total['tsum']))
    msg='Expense has been added'
    print("session at dashbaord final" ,session)
    return render_template('dashboard.html',msg=msg ,data=data,budget=int(bud), total=int(total['tsum']))

@app.route('/uexpense/<string:id>', methods=['GET','POST'])
def uexpense(id):

    print(id)
    nam=request.form['nam']
    ncateg=request.form['ncateg']
    ndate=request.form['ndate']
    ndesc=request.form['ndesc']
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE expense_a SET amount=%s, category=%s, date=%s, description=%s WHERE ex_id=%s and id=%s ', (nam,ncateg,ndate,ndesc,id,session['id'], ))
    mysql.connection.commit()
    flash(u"Expense Has Been Updated","succcess")
    print(dict(request.form))
    return redirect(url_for('dashboard'))


@app.route('/delete', methods=['GET','POST'])
def delete():
    print("restes form is ",request.form)
    da=request.form['del']
    print(da)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM expense_a WHERE ex_id = % s ', (da, ))
    mysql.connection.commit()
    cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = % s', (session['id'], ))
    data=cursor.fetchall()
    

    return redirect(url_for('dashboard'))
@app.route('/statistics', methods=['GET','POST'])
def statistics():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT category,amount FROM expense_a WHERE id = % s', (session['id'],  ))
    catam = (cursor.fetchall())
    print(catam)
    x={}
    for i in catam:
        print("I is ",i)
        if(i['category'] in x):
            x[i['category']]+=i['amount']
        else:
            x[i['category']] = i['amount']
        print(i['category'],i['amount'])
    print(x)
    curdoc().theme = 'dark_minimal'

    chart_colors = ['#44e5e2', '#e29e44', '#e244db',
                '#d8e244', '#eeeeee', '#56e244', '#007bff', 'black']
    data = pd.Series(x).reset_index(name='value').rename(columns={'index':'country'})
    print(data)
    data['angle'] = data['value']/data['value'].sum() * 2*pi
    data['color'] = chart_colors[:len(x)]

    p = figure(plot_height=350, title="Pie Chart", toolbar_location=None,
                tools="hover", tooltips="@country: @value", x_range=(-0.5, 1.0))

    p.wedge(x=0, y=1, radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color', legend_field='country', source=data)

    p.axis.axis_label=None
    p.axis.visible=False
    p.grid.grid_line_color = None



    html = file_html(p, CDN, "my plot")
    #file=open('./static/pie.html',"w")
    #file.write(html)
    #file.close()

    
    

    fruits = list(x.keys())
    counts = list(x.values())
    
    print(fruits,counts)
    source = ColumnDataSource(data=dict(fruits=fruits, counts=counts, color=Spectral6))

    p_h = figure(x_range=fruits, y_range=(0,max(counts)*2), plot_height=250, title="Fruit counts",
           toolbar_location=None, tools="")

    p_h.vbar(x='fruits', top='counts', width=0.9, color='color', legend_field="fruits", source=source)

    p_h.xgrid.grid_line_color = None
    p_h.legend.orientation = "horizontal"
    p_h.legend.location = "top_center"

    
    html1 = file_html(p_h, CDN, "my plot1")

    
    
    return render_template('stats.html',html=html,html1=html1)



@app.route('/logout')
def logout():
   
   session.pop('id', None)
   session.pop('username', None)
   session.pop('budget', None)
   session.pop('total', None)
   session.pop('mnd', None)
   session.pop('mxd', None)
   session.pop('new_user', None)
   session.pop('b_m', None)
   session.pop('d_m', None)
   session['loggedin']=False
   print(session)
   msg='You have been logged out successfully'

   return render_template('main.html', msg=msg)



if __name__ == '__main__':
    app.run(debug=True)