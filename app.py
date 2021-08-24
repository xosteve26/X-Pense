from flask import Flask, render_template, request, redirect, sessions, url_for, session,flash, Response,json
import psycopg2,psycopg2.extras
import csv
import bcrypt
import base64
import io
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from sorted_months_weekdays import Month_Sorted_Month
app=Flask(__name__)
port=int(os.environ.get("PORT",5000))
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}

def start_db():

    conn = psycopg2.connect(
    database=os.environ.get('db_name'), user=os.environ.get('db_username'), password=os.environ.get('db_password'), host=os.environ.get('db_host'), port= os.environ.get('db_port')
    )
    return conn
start_db()

app.secret_key = 'a'
app.config['DATABASE_URL']=os.environ.get('DATABASE_URL')


def get_expense(a,b):
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cursor.execute('SELECT ex_id,amount,category,date,description FROM public.expense_a WHERE id=%s AND ym=%s ORDER BY date DESC', (a,b,  ))
    data=cursor.fetchall()
    return data
def get_sum(c,d):
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cursor.execute('SELECT SUM(amount) AS tsum FROM public.expense_a WHERE id=%s AND ym=%s', (c,d, ))
    total=cursor.fetchone()
    return total



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
        hashed_pr=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        session['hash']=hashed_pr
   
        conn=start_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM public.user WHERE username=%s', (username, ))
        account=cursor.fetchone()
 
 
        if account:
            msg="Account already exists"
        else:
            cursor.execute('INSERT INTO public.user(id,username,password,email) VALUES (DEFAULT,%s,%s,%s)', (username, hashed_pr, email, ))
            conn.commit()
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
        
        conn=start_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        cursor.execute('SELECT password FROM public.user WHERE username=%s ',(username,))
        h_p = cursor.fetchone()
        #To check if an account with the entered details exist in the database
        if h_p:
            #Below if is executed for when hashed password was obtained for the entered username
            if h_p.password:
        
                a=bcrypt.checkpw(password.encode('utf-8'),h_p.password.encode('utf-8'))
                #The following if condition is executed for when hash password doesnt match the password entered
                if a == False:
                    msg="Password is incorrect"
                    return render_template('main.html', wa=msg)
                #else condition is executed for when password entered matches the hashed password then else block is executed
                else:
            
                    cursor.execute('SELECT * FROM public.user WHERE username=%s AND password=%s', (username, h_p.password ))
                    account = cursor.fetchone()
            
                    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    session['loggedin'] = True
                    session['id'] = account.id
                    session['username'] = account.username
                    session['email']=account.email
                    msg = 'Logged in successfully !'
            
                    return render_template('main.html', msg=msg)
        #The below else block is executed for when the query wasn't able to obtain the password for the username entered             
        else:
            msg="Account doesn't exist"
            return render_template('main.html', wa=msg)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    wa=''
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    if session['loggedin']:
        session['s_m']=None
 
        
        try:
         
            #To obtain the month for a set budget
            cursor.execute("SELECT b_month FROM public.budget WHERE id=%s", (session['id'],))
            b_m=cursor.fetchone()
         
        
            session['y_r']=b_m.b_month.split('-')[0]
            
            session['b_m']=b_m.b_month
            session['s_m']=b_m.b_month
           
           
        
        except:
          
            cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
            pass
        data=[]
        try:
            #To obtain the expense details for a particualar month of the user
            data=get_expense(str(session['id']),session['b_m'])

        except KeyError:
            pass
    
        try:
            #To obtain the budget amount from our database
            cursor.execute('SELECT bamount FROM public.budget WHERE id=%s', (session['id'], ))
            b=cursor.fetchone()
         

        except TypeError:
            b={'bamount': 0}
        
        try:
            #To obtain the sum of all the expenses for a particular month
            total=get_sum(str(session['id']), session['b_m'])
            session['total']=total.tsum
   
        except KeyError:
            total={'tsum':0}

       
        #To obtain the budget month
        cursor.execute("SELECT b_month FROM public.budget WHERE id=%s ", (str(session['id']),))
        d_m=cursor.fetchall()

        
        l_month=[]
        m_year=[]
        year=[]
        full_ym=[]
        for i in d_m:
            l_month.append(i.b_month[5:])
            m_year.append(i.b_month)
            year.append(i.b_month[0:4])
            full_ym.append(i.b_month)
        session['d_m']=l_month
        session['y_m']=m_year
        session['years']=year
        session['full_ym']=full_ym
        
     
    
        if b:
            session['budget']=b.bamount
            bud=session['budget']
         

        else:
            flash(u"Please Set Budget First","primary")
      
            return render_template('dashboard.html',month=month)
        if data:
            flash(u"Wecome back {}".format(session['username']) , "primary")
          
            return render_template('dashboard.html', data=data,budget=bud, total=int(total.tsum),month=month,d_m=session['d_m'])
        else:
            flash(u"Please Add Expenses","primary")
        if (total.tsum == None):
            return render_template('dashboard.html',total=0,budget=bud,month=month,d_m=session['d_m'])
        else:
            session['total'] = int(total.tsum)
        
        return render_template('dashboard.html')
    
    else:
        wa='Please login first'       
        return render_template('main.html', wa=wa)

 


@app.route('/switchmonth/<string:mon>', methods=['GET'])   
def switch_month(mon):
    conn=start_db()
    month=["January","February","March","April","May","June","July","August","September","October","November","December"]
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    session['s_m']=mon
    
  
    #Retrieve expense details for a particualr month
    data=get_expense(str(session['id']), mon)

    #Obtain the budget amount for a particular month
    cursor.execute('SELECT bamount FROM public.budget WHERE id=%s AND b_month LIKE %s', (session['id'], mon,))
    b=cursor.fetchone()
    
  
    if b == None:
        flash(u"Budget does not exist for the inputted budget month/year","danger")
        return redirect(url_for('dashboard'))

    #Obtain the total for the expenses corresponding to the month
    total=get_sum(str(session['id']), mon)
    session['total']=str(total.tsum)
   
    #To obtian the name of the budget month
    cursor.execute("SELECT b_month FROM public.budget WHERE id=%s ", (session['id'],))
    d_m=cursor.fetchall()
    
    l=[]
    for i in d_m:
        l.append(i.b_month[5:])
        session['d_m']=l
  
    session['budget']=b.bamount
    bud=session['budget']
  
  
    try:

        return render_template('dashboard.html',data=data,budget=bud, total=int(total.tsum),month=month,d_m=session['d_m'])
         
    except:
  
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
    
    
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    #To check if the budget month entered by the user already exists
    cursor.execute('SELECT * FROM public.budget WHERE id=%s AND b_month=%s',(session['id'],m))
    exist=cursor.fetchall()
    if exist:
        flash(u'Budget already exists for the inputted month','danger')
        return redirect(url_for('dashboard'))
    cursor.execute('INSERT INTO public.budget(sl_no,id,bamount,b_month) VALUES (DEFAULT,%s, %s, %s)', (b_id,budget,m, ))
    session['full_ym'].append(m)
    conn.commit()
    #Obtain the budget amount from databse
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cursor.execute('SELECT * FROM public.budget WHERE id=%s AND bamount=%s', (b_id, budget ))
    account = cursor.fetchone()
    session['budget']=account.bamount 
    session['years'].append(b_y)
    flash(u"Budget has been set, Now you can proceed to adding expenses","primary")

  
    return redirect(url_for('switch_month', mon=session['s_m']))
    
    


@app.route('/updatebudget', methods=['POST'])
def updatebudget():
    new_budget=request.form['updatebudget']
    n_y=request.form['b_y']
    n_m=request.form['b_m']
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    #To update the required inputs given into the database
    cursor.execute('UPDATE budget SET bamount=%s WHERE id=%s AND b_month=%s',(new_budget,session['id'],n_y+"-"+n_m))
    conn.commit()
    session['years'].append(n_y)
    
    flash(u"Budget Updated","success")
    return redirect(url_for('dashboard'))


@app.route('/aexpense', methods=['POST'])
def expense():
  
    e_id=session['id']
    amount=request.form['am']
    category=request.form['categ']
    date=request.form['date']
   
    conn=start_db()
    description=request.form['desc']
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    session['y_r']=date[0:4]
  
    
    cursor.execute('SELECT bamount FROM public.budget WHERE id=%s AND b_month LIKE %s',(str(session['id']),date[0:4]+'-'+month[int(date[5:7])-1]))
    check=cursor.fetchone()
    
    if check:

        cursor.execute('INSERT INTO public.expense_a(ex_id,id,amount,category,date,description,ym)  VALUES(DEFAULT,%s,%s,%s,%s,%s,%s)', (e_id,amount,category,date,description,session['s_m'], ))
        conn.commit()
        
  
    cursor.execute('SELECT bamount FROM public.budget WHERE id=%s ', (e_id, ))
    bud=cursor.fetchone()
 
    
    data=get_expense(str(session['id']), session['s_m'])
 
    
   
    total=get_sum(str(session['id']),session['s_m'])   
    session['total']=str(total.tsum)
   
    
    if total.tsum == None:
        total=0
    else:
        total=total.tsum
 
    bud=session['budget']
   
    if check:
        if data:
            if session['s_m']:
                flash(u"Expense has been added","success")
          
                if (total>bud):
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
                
                return redirect(url_for('switch_month',mon=session['s_m'],data=data,budget=int(bud), total=int(total)))
            else:
                flash(u"Expense has been added","success")
                return redirect(url_for('switch_month',mon=session['b_m'],data=data,budget=int(bud), total=int(total)))
        
    else:
        flash(u"Budget not set for the month inputted for the expense","danger")
        return redirect(url_for('dashboard', data=data,budget=int(bud), total=int(total)))

@app.route('/uexpense/<string:id>', methods=['POST'])
def uexpense(id):

 
    nam=request.form['nam']
    ncateg=request.form['ncateg']
    ndate=request.form['ndate']
    
    ndesc=request.form['ndesc']
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

    cursor.execute('SELECT bamount FROM budget WHERE id=%s AND b_month LIKE %s',(str(session['id']),ndate[0:4]+'-'+month[int(ndate[5:7])-1]))
    check=cursor.fetchone()

    if check:
        if ndate[0:7] == session['s_m'][0:5]+'%02d'%(int(month.index(session['s_m'][5:])+1)):

            cursor.execute('UPDATE expense_a SET amount=%s, category=%s, date=%s, description=%s WHERE ex_id=%s and id=%s ', (nam,ncateg,ndate,ndesc,id,str(session['id']), ))
            conn.commit()
        
            try:
                flash(u"Expense Has Been Updated",category="success")
                return redirect(url_for('switch_month',mon=session['s_m']))
            except:
          
                return redirect(url_for('dashboard'))
        else:
            flash(u"Date inputted for another budget period","danger")
            return redirect(url_for('switch_month',mon=session['s_m']))

    else:
        flash(u"Budget not set for the inputted month/year","danger")
        return redirect(url_for('switch_month',mon=session['s_m']))



@app.route('/delete', methods=['POST'])
def delete():

    da=request.form['del']
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cursor.execute('DELETE FROM expense_a WHERE ex_id = %s ', (da, ))
    conn.commit()    
    try:
        return redirect(url_for('switch_month',mon=session['s_m']),code=301)
    except:
        return redirect(url_for('dashboard'))

@app.route('/dtransactions', methods=['GET'])
def download_transactions():
    conn=start_db()
    
    try:
   
        cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        result=get_expense(str(session['id']), session['s_m'])
        
        output=io.StringIO()
        writer=csv.writer(output)
        head=["Username :",session['username'],"Budget :","$"+str(session['budget']),"Total Expenses :","$"+str(session['total'])]
        writer.writerow(head)
        line=['amount','category','date','description']
        writer.writerow(line)
        for row in result: 
            line=[str(row.amount) , row.category, str(row.date),row.description]
            writer.writerow(line)
        output.seek(0)
        return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=transaction_report.csv"})

    except Exception as e:
        print(e)
    finally:
        cursor.close()


@app.route('/etransactions',methods=['GET'])
def email_transaction():
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    #To obtain the email of the user
    cursor.execute('SELECT email FROM public.user WHERE id=%s',(str(session['id']),))
    em=cursor.fetchone()
    #To obtain a detailed list of all the expenses as per the chosen time frame.
    cursor.execute('SELECT amount,category,date,description FROM public.expense_a WHERE id=%s AND ym=%s ',(str(session['id']),session['s_m']))
    result=cursor.fetchall()
   
    df=pd.DataFrame(result)
    df_update=df.rename(columns={'amount':'Amount(in $)','category':'Category','date':'Date','description':'Description'})
    
    df_update.to_csv(r'transaction.csv',index=False)

    with open('transaction.csv', 'rb') as f:
        data = f.read()
        f.close()
    message = Mail(
    from_email='noreplyflaskblog1@gmail.com',
    to_emails=em.email,
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
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    #To obtain category & amount from our database
    cursor.execute('SELECT category,amount FROM expense_a WHERE id=%s AND ym=%s', (str(session['id']), session['s_m']))
    catam = (cursor.fetchall())
    
    #For creating a dictionary 'x' which contains the  Category(key) & Amount(value) of expenses
    x={}
    for i in catam:
   
        if(i.category in x):
            x[i.category]+=i.amount
        else:
            x[i.category] = i.amount
  

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
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    
    #To obtain monthname and sum of expenses for each month
    cursor.execute("SELECT TO_CHAR(date,'Month') as m,sum(amount) as a from expense_a WHERE id=%s AND date>='%s-01-01' AND date< '%s-01-01' group by m order by m DESC", (str(session['id']),int(session['s_m'][0:4]),int(session['s_m'][0:4])+1))   
    a_month=cursor.fetchall()
    
    fc=[]
    s_r=[]
    l={}
    #For Obtaining Months
    for i in a_month:
        f=i.m.strip()
        s_r.append(f)
    
    #Sorting the months in ascending order
    c=Month_Sorted_Month(s_r)
    
    
    for i in a_month:
        ww=i.m.strip()
        l[ww]=i.a
      
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
    conn=start_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    #To obtain all years present along with the sum of amounts for each of those years
    cursor.execute("SELECT TO_CHAR(date,'YYYY') as y ,SUM(amount) as a from public.expense_a WHERE id=%s  group by y",(str(session['id']),))
    allyear=cursor.fetchall()
    
    ay=[]
    sy=[]

    for j in allyear:
        ay.append(int(j.y))
        sy.append(int(j.a))
    
    if allyear:
        return render_template('staty.html',ay=ay,sy=sy)
    else:
        session['statnotavail']=True
        no="No expenses available to generate graphical preview"
        return render_template('stats.html',no=no)



@app.route('/feedback',methods=['GET','POST'])
def feedback():
    if request.method == 'POST':
        name=request.form['name']
        feedback=request.form['feedback']
   
        message = Mail(
        from_email='noreplyflaskblog1@gmail.com',
        to_emails='lavobix315@dmsdmg.com',
        subject='Feedback From:'+' '+name,
        html_content='<h1>X-PENSE TRACKER</h1> <p> <br><i>'+feedback+'</i></p>')
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e)
        return render_template('main.html',msg='Feedback Has Been Sent')

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
   session.pop("full_ym",None)
   session['loggedin']=False
   print(session)
  
   

   msg='You have been logged out successfully'

   return render_template('main.html', msg=msg)



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=port,debug=True)