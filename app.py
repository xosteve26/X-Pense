
from flask import Flask, render_template, request, redirect, url_for, session,flash, Response,json
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from math import pi
import csv
import bcrypt
import base64
import io
import pandas as pd
from numpy import int64
from dotenv import load_dotenv
load_dotenv()
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from sorted_months_weekdays import Month_Sorted_Month, Weekday_Sorted_Week



import datetime
from pandas.core.indexes.api import Int64Index
import shutil
app=Flask(__name__)
port=int(os.environ.get("PORT",5000))




app.secret_key = 'a'
  
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = '9CaX90ZO70'
app.config['MYSQL_PASSWORD'] = '3ZvAjIocQr'
app.config['MYSQL_DB'] = '9CaX90ZO70'
mysql = MySQL(app)



month=["January","February","March","April","May","June","July","August","September","October","November","December"]

@app.route('/home')
@app.route('/')
def home():
   
    try:
        #To check if the incomming user has already logged in or not using the session
        if session['id']:
            session['loggedin']=True
        else:
            session['loggedin']=False
    except:
        session['loggedin']=False
  
    return render_template('main.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg=''
    if request.method == 'POST':
        username=request.form['uname']
        password=request.form['pass']
        email=request.form['email']
        session['username'] = username
        session['password']=password
        session['email']=email
        hashed_pr=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        session['hash']=hashed_pr
 
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE username = % s', (username, ))
        account=cursor.fetchone()
 
        if account:
            msg="Account already exists"
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s)', (username, hashed_pr, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            session['loggedin']=False
         
            message = Mail(
            from_email='noreplyflaskblog1@gmail.com',
            to_emails=session['email'],
            subject='Successful Registeration',
            html_content='<h1>X-PENSE TRACKER</h1> <p> Congratulations'+' '+ session['username'] + ' , on successully creating an account with X-Pense . To manage your expenses please proceed to the dashboard upon logging in.</p><h2>Your account details are : </h2><h3> Username: </h3> <i>'+session['username']+'</i><h3>E-Mail: </h3> <i>'+ session['email'] +'</i><h3>Password: </h3> <i>'+ session['password'] + '</i>')
            try:
                sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                response = sg.send(message)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(e)
            session.pop('username',None)
            session.pop('email',None)
            session.pop('password',None)
            session.pop('hash',None)
      
            return render_template('main.html', msg=msg)


    return render_template('register.html',msg=msg)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #Obtianing username and password entered by the user 
        username=request.form['username']
        password=request.form['password']
        
        
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT password FROM user WHERE username=%s ',(username,))
        h_p = cursor.fetchone()
        #Below if is executed for when hashed password was obtained for the entered username
        if h_p:
            a=bcrypt.checkpw(password.encode('utf-8'),h_p['password'].encode('utf-8'))
            #The following if condition is executed for when hash password doesnt match the password entered
            if a == False:
                msg="Password is incorrect"
       
                return render_template('main.html', msg=msg)
            #else condition is executed for when password entered matches the hashed password then else block is executed
            else:
                cursor.execute('SELECT * FROM user WHERE username = % s AND password = % s', (username, h_p['password'] ))
                account = cursor.fetchone()
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['email']=account['email']
                msg = 'Logged in successfully !'
        
                return render_template('main.html', msg=msg)
        #The below else block is executed for when the query wasnt able to obtain the password for the username entered           
        else:
            msg="Account doesn't exist"
    
            return render_template('main.html', msg=msg)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    wa=''
   

    if session['loggedin']:
        session['s_m']=None
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            #To obtain the month for a set budget
            cursor.execute("SELECT b_month FROM budget WHERE id=%s", (session['id'],))
            b_m=cursor.fetchone()
        
            session['y_r']=b_m['b_month'].split('-')[0]
            b_m['b_month']=b_m['b_month'].split('-')[1]
            
            session['b_m']=b_m['b_month']
            session['s_m']=session['y_r']+'-'+session['b_m']
           
        
        except:
            pass
        data=[]
        try:
            #To obtain the expense details for a particualar month of the user
            cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = % s AND monthname(date)=%s AND YEAR(date)=%s ORDER BY date DESC', (session['id'], session['b_m'],session['y_r'] ))
            data=cursor.fetchall()
          

        except KeyError:
            pass
       
        try:
            #To obtain the budget amount from our database
            cursor.execute('SELECT bamount FROM budget WHERE id = % s', (session['id'], ))
            b=cursor.fetchone()

        except TypeError:
            b={'bamount': 0}
        
        try:
            #To obtain the sum of all the expenses for a particular month
            cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = % s AND monthname(date)=%s AND YEAR(date)=%s', (session['id'], session['b_m'],session['y_r']))
            total=cursor.fetchone()
            session['total']=str(total['tsum'])
   
        except KeyError:
            total={'tsum':0}

       
        #To obtain the budget month
        cursor.execute("SELECT b_month FROM budget WHERE id=%s ", (session['id'],))
        d_m=cursor.fetchall()
        
        l_month=[]
        m_year=[]
        year=[]
        for i in d_m:
            l_month.append(i['b_month'][5:])
            m_year.append(i['b_month'])
            year.append(i['b_month'][0:4])
        session['d_m']=l_month
        session['y_m']=m_year
        session['years']=year
        
     
    
        if b:
            session['budget']=b['bamount']
            bud=session['budget']

        else:
            flash(u"Please Set Budget First","primary")
      
            return render_template('dashboard.html',month=month)
        if data:
            flash(u"Wecome back {}".format(session['username']) , "primary")
          
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

 


@app.route('/switchmonth/<string:mon>', methods=['GET'])   
def switch_month(mon):
  
    month=["January","February","March","April","May","June","July","August","September","October","November","December"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    session['s_m']=mon
  
    #Retrieve expense details for a particualr month
    cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a  WHERE id = % s AND monthname(date)=%s AND YEAR(date)=%s ORDER BY date DESC  ', (session['id'], mon.split('-')[1],mon.split('-')[0] ))
    data=cursor.fetchall()
    
  
    #Obtain the budget amount for a particular month
    cursor.execute('SELECT bamount FROM budget WHERE id=%s AND b_month LIKE %s', (session['id'], mon,))
    b=cursor.fetchone()
  
    if b == None:
        flash(u"Budget does not exist for the inputted budget month/year","danger")
        return redirect(url_for('dashboard'))

    #Obtain the total for the expenses corresponding to the month
    cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = % s AND monthname(date)=%s AND YEAR(date)=%s', (session['id'], mon.split('-')[1],mon.split('-')[0]))
    total=cursor.fetchone()
 
    session['total']=str(total['tsum'])
   
    #To obtian the name of the budget month
    cursor.execute("SELECT b_month FROM budget WHERE id=%s ", (session['id'],))
    d_m=cursor.fetchall()
    
    l=[]
    for i in d_m:
        l.append(i['b_month'][5:])
        session['d_m']=l
  
    session['budget']=b['bamount']
    bud=session['budget']
  
  
    try:

        return render_template('dashboard.html',data=data,budget=bud, total=int(total['tsum']),month=month,d_m=session['d_m'])
        #return redirect(url_for('dashboard',data=data,budget=bud, total=int(total['tsum']),month=month,d_m=session['d_m']))   
    except:
        #return redirect(url_for('dashboard',data=data,budget=bud, total=0,month=month,d_m=session['d_m']))
        return render_template('dashboard.html',data=data,budget=bud, total=0,month=month,d_m=session['d_m'])

@app.route('/setbudget', methods=['POST'])
def budget():
    
    budget=request.form['budget']
    b_id=session['id']
    b_y = request.form['b_y']
    b_m = request.form['b_m']
    session['b_m']=b_m
    m=b_y+"-"+b_m
    session['s_m']=m
    
 
    cursor = mysql.connection.cursor()
    #To check if the budget month entered by the user already exists
    cursor.execute('SELECT * FROM budget WHERE id=%s AND b_month=%s',(session['id'],m))
    exist=cursor.fetchall()
    if exist:
        flash(u'Budget already exists for the inputted month','danger')
        return redirect(url_for('dashboard'))
    cursor.execute('INSERT INTO budget VALUES (NULL,%s, %s, %s)', (b_id,budget,m, ))
    mysql.connection.commit()
    #Obtain the budget amount from databse
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM budget WHERE id = % s AND bamount = % s', (b_id, budget ))
    account = cursor.fetchone()
    session['budget']=account['bamount']  
    session['years'].append(b_y)
    flash(u"Budget has been set, Now you can proceed to adding expenses","primary")

  
    return redirect(url_for('switch_month', mon=session['s_m']))
    
    


@app.route('/updatebudget', methods=['POST'])
def updatebudget():
    new_budget=request.form['updatebudget']
    n_y=request.form['b_y']
    n_m=request.form['b_m']
    
    cursor = mysql.connection.cursor()
    #To update the required inputs given into the database
    cursor.execute('UPDATE budget SET bamount=%s WHERE id=%s AND b_month=%s',(new_budget,session['id'],n_y+"-"+n_m))
    mysql.connection.commit()
    session['years'].append(n_y)
    
    flash(u"Budget Updated","success")
    return redirect(url_for('dashboard'))


@app.route('/aexpense', methods=['POST'])
def expense():
  
    e_id=session['id']
    amount=request.form['am']
    category=request.form['categ']
    date=request.form['date']

    description=request.form['desc']
    cursor = mysql.connection.cursor()
    session['y_r']=date[0:4]
  
 
    cursor.execute('SELECT bamount FROM budget WHERE id=%s AND b_month LIKE %s',(session['id'],date[0:4]+'-'+month[int(date[5:7])-1]))
    check=cursor.fetchone()
    if check:

        cursor.execute('INSERT INTO expense_a VALUES(NULL,%s,%s,%s,%s,%s)', (e_id,amount,category,date,description, ))
        mysql.connection.commit()
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT bamount FROM budget WHERE id = % s ', (e_id, ))
    bud=cursor.fetchone()
 
 
    cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = %s AND monthname(date)=%s AND YEAR(date)=%s', (session['id'], session['b_m'],session['y_r'] ))
    data=cursor.fetchall()
   
  
    cursor.execute('SELECT SUM(amount) AS tsum FROM expense_a WHERE id = %s AND monthname(date)=%s AND YEAR(date)=%s ', (session['id'],session['b_m'],session['y_r'], ))
    total=cursor.fetchone()
   
    session['total']=str(total['tsum'])
   
    
    if total['tsum'] == None:
        total['tsum']=0
 
    bud=session['budget']
   
    if check:

        if data:
            if session['s_m']:
                flash(u"Expense has been added","success")
          
                if (total['tsum']>bud):
                    message = Mail(
                        from_email='noreplyflaskblog1@gmail.com',
                        to_emails=session['email'],
                        subject='WARNING: Exceeded Budget',
                        html_content='<h1>X-PENSE TRACKER</h1> <h3> Dear'+' '+ session['username'] + '</h3> <p style="color:red"> You have exceeded your monthly budget of amount'+' '+str(session['budget'])+ ', For the month of'+' '+session['s_m']+'.</p><br>You current expenses are worth:'+session['total']+'<p>Yours Truely,<br>ABC</p>')
                try:
                    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                    response = sg.send(message)
                    print(response.status_code)
                    print(response.body)
                    print(response.headers)
                except Exception as e:
                    print(e)
                
                return redirect(url_for('switch_month',mon=session['s_m'],data=data,budget=int(bud), total=int(total['tsum'])))
            else:
                flash(u"Expense has been added","success")
               
                return redirect(url_for('switch_month',mon=session['b_m'],data=data,budget=int(bud), total=int(total['tsum'])))
        
    else:

        flash(u"Budget not set for the month inputted for the expense","danger")
        return redirect(url_for('dashboard', data=data,budget=int(bud), total=int(total['tsum'])))

@app.route('/uexpense/<string:id>', methods=['POST'])
def uexpense(id):

 
    nam=request.form['nam']
    ncateg=request.form['ncateg']
    ndate=request.form['ndate']
    ndesc=request.form['ndesc']
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT bamount FROM budget WHERE id=%s AND b_month LIKE %s',(session['id'],ndate[0:4]+'-'+month[int(ndate[5:7])-1]))
    check=cursor.fetchone()
    if check:

        cursor.execute('UPDATE expense_a SET amount=%s, category=%s, date=%s, description=%s WHERE ex_id=%s and id=%s ', (nam,ncateg,ndate,ndesc,id,session['id'], ))
        mysql.connection.commit()
    
 
        try:
            flash(u"Expense Has Been Updated","succcess")
            return redirect(url_for('switch_month',mon=session['s_m']))
        except:

            return redirect(url_for('dashboard'))
    else:
        flash(u"Budget not set for the inputted month/year","danger")
        return redirect(url_for('switch_month',mon=session['s_m']))



@app.route('/delete', methods=['POST'])
def delete():

    da=request.form['del']
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM expense_a WHERE ex_id = % s ', (da, ))
    mysql.connection.commit()
    cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = % s', (session['id'], ))
    data=cursor.fetchall()
    
    try:
      
        #if request.endpoint!=url_for('switch_month',mon=session['s_m']):

         #   return redirect(f"/switchmonth/{session['s_m']}")
        return redirect(url_for('switch_month',mon=session['s_m']),code=301)
    
    except:
        return redirect(url_for('dashboard'))

@app.route('/dtransactions', methods=['GET'])
def download_transactions():

    conn=None
    cursor=None
    try:
   
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT ex_id,amount,category,date,description FROM expense_a WHERE id = % s AND monthname(date)=%s AND YEAR(date)=%s', (session['id'], session['s_m'][5:],session['s_m'][0:4] ))
        result=cursor.fetchall()
       
        output=io.StringIO()
        writer=csv.writer(output)
        head=["Username :",session['username'],"Budget :","$"+str(session['budget']),"Total Expenses :","$"+str(session['total'])]
        writer.writerow(head)
        line=['amount','category','date','description']
        writer.writerow(line)
        for row in result: 
            line=[str(row['amount']) , row['category'], str(row['date']),row['description']]
            writer.writerow(line)
        output.seek(0)
        return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=transaction_report.csv"})

    except Exception as e:
        print(e)
    finally:
        cursor.close()


@app.route('/etransactions',methods=['GET'])
def email_transaction():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #To obtain the email of the user
    cursor.execute('SELECT email FROM user WHERE id=%s',(session['id'],))
    em=cursor.fetchone()
    #To obtain a detailed list of all the expenses as per the chosen time frame.
    cursor.execute('SELECT amount,category,date,description FROM expense_a WHERE id =%s AND monthname(date)=%s AND YEAR(date)=%s ',(session['id'],session['s_m'][5:],session['s_m'][0:4]))
    result=cursor.fetchall()
   
    df=pd.DataFrame(result)
    df_update=df.rename(columns={'amount':'Amount(in $)','category':'Category','date':'Date','description':'Description'})
    
    df_update.to_csv(r'transaction.csv',index=False)

    with open('transaction.csv', 'rb') as f:
        data = f.read()
        f.close()
    message = Mail(
    from_email='noreplyflaskblog1@gmail.com',
    to_emails=em['email'],
    subject='Transaction Report For The Month Of'+'-'+ session['s_m'],
    html_content='Below you will find attached a detailed copy of your transactions for the month of'+' '+session['s_m']
    )

    encoded_file = base64.b64encode(data).decode()
  

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName('transaction'+'_'+session['s_m']+'.csv'),
        FileType('transaction/csv'),
        Disposition('attachment')
    )
    message.attachment = attachedFile

    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code, response.body, response.headers)
    flash(u"E-mail has been sent","success")
    return redirect(url_for('dashboard'))


@app.route('/statistics', methods=['GET'])
def statistics():

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #To obtain category & amount from our database
    cursor.execute('SELECT category,amount FROM expense_a WHERE id = % s AND monthname(date)=%s AND YEAR(date)=%s', (session['id'], session['s_m'][5:],session['s_m'][0:4] ))
    catam = (cursor.fetchall())

   
    #For creating a dictionary 'x' which contains the  Category(key) & Amount(value) of expenses
    x={}
    for i in catam:
   
        if(i["category"] in x):
            x[i["category"]]+=i["amount"]
        else:
            x[i["category"]] = i["amount"]
  

    row = list(x.keys())
    col = list(x.values())
    
    session['statnotavail']=False
    if(catam):
        return render_template('stats.html',row=row,col=col)
  
    else:
 
        session['statnotavail']=True
        no="No expenses available to generate graphical preview"
        return render_template('stats.html',no=no)

@app.route('/statistics/months',methods=['GET'])
def statm():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #To obtain monthname and sum of expenses for each month
    cursor.execute('SELECT monthname(date) as m,sum(amount) as a from expense_a WHERE id=%s AND YEAR(date)=%s  group by monthname(date) order by monthname(date)DESC  ', (session['id'],session['s_m'][0:4]))
    a_month=cursor.fetchall()
    fc=[]
    s_r=[]
    l={}
    #For Obtaining Months
    for i in a_month:
        s_r.append(i['m'])
    #Sorting the months in ascending order
    c=Month_Sorted_Month(s_r)

    for i in range(0,len(a_month)):
        d=list(a_month[i].values())
        l[d[0]]=d[1]
    for j in c:
        fc.append(int(l[j]))
    if a_month:
        
        return render_template('statsm.html',s_r=c,s_c=fc)
    else:
        session['statnotavail']=True
        no="No expenses available to generate graphical preview"
        return render_template('stats.html',no=no)



    
@app.route('/statistics/years',methods=['GET'])
def staty():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #To obtain all years present along with the sum of amounts for each of those years
    cursor.execute('SELECT   YEAR(date) as ym ,SUM(amount) as a from expense_a WHERE id=%s  group by ym',(session['id'],))
    allyear=cursor.fetchall()
    ay=[]
    sy=[]

    for j in allyear:
        ay.append(j['ym'])
        sy.append(int(j['a']))
    if allyear:
        return render_template('staty.html',ay=ay,sy=sy)
    else:
        session['statnotavail']=True
        no="No expenses available to generate graphical preview"
        return render_template('stats.html',no=no)



@app.route('/logout')
def logout():
   #Removal of all sessions 
   session.pop('id', None)
   session.pop('username', None)
   session.pop('budget', None)
   session.pop('total', None)
   session.pop('mnd', None)
   session.pop('mxd', None)
   session.pop('new_user', None)
   session.pop('b_m', None)
   session.pop('d_m', None)
   session.pop("s_m", None)
   session.pop("statnotavail",None)
   session.pop("row",None)
   session.pop("column",None)
   session.pop("email",None)
   session.pop("y_r",None)
   session.pop("y_m",None)
   session.pop("years",None)
   session['loggedin']=False
   

   msg='You have been logged out successfully'

   return render_template('main.html', msg=msg)



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=port,debug=True)