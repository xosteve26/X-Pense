# X-Pense : A Personalised Expense Tracker #

Application Demo : <https://youtu.be/rjsxO4KjXak>

The objective of this project was to provide a user- friendly application, that could make the process of managing one’s expenses in an easier and effective manner by providing insightful charts that will help the user to derive useful data from it and understand where his finances are being consumed, which could in turn help him to manage his expenditures in a more coherent manner.This app has been successfully deployed on the TANZU APPLICATION SERVICE.
This project showcases the implementation of an expense tracker which was made using Python FLASK, MySQL and the fundamental web development technologies like HTML, CSS & JS.
This app provides the end users the following features:



- Would allow users to set a budget for a particular month & year following which 
- The user would then would be able to add any expenditures to that particular month & year that was set.
- Supports additions of multiple budget limits for various months along with the functionality of navigating between all the budgets created and the expenses created for theat specified budget month/year.
- E-Mail alerts for when the user’s expenditures were to cross the budget limit set for that month.
- Functionality to download/e-mail a report of the expenditures for the budget month that was set.
- Provides the user the ability to visualize his expenditures in a graphical form.

![image](https://user-images.githubusercontent.com/73709251/117812845-efe0a600-b27f-11eb-919f-a041cd519a90.png)


Click on the link to access the product : <https://expense-tracker.apps.pcfdev.in>


> ### Replication & Usage

- Close the repository first:
``` https://github.com/xosteve26/X-Pense.git ```

- Create a `.env` file and craete a varaible named `SENDGRID_API_KEY` EX: ```SENDGRID_API_KEY="You Sendgrid API Key" ``` and store the sendgrid api key in order to make use of the email funcitonality.

- Modify the variables app.config[MySQL_HOST,USER,PASSWORD,DB] in the `app.py` file with your own database credentials.

