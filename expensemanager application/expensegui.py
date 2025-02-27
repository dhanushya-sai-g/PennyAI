from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pymongo
import smtplib
import random
import ssl
from email.message import EmailMessage
import sys
from gtts import gTTS
from io import BytesIO
import pygame
import pandas as pd
import json
import requests
import speech_recognition as sr
import pyttsx3
from datetime import date, datetime, timedelta
from bson import ObjectId 
import matplotlib.pyplot as plt
import io
import base64
user_id = None
app = Flask(__name__)
MONGO_URI = "mongodb+srv://dhanushya:frooti@projects.r87yn.mongodb.net/?retryWrites=true&w=majority&appName=Projects"
client = pymongo.MongoClient(MONGO_URI)
db = client["PennyAI"]  # Database Name
users = db["users"]  # Collection Name
expense = db["expense"]
category = db["categories"] 
subcategory = db["subcategories"]

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "yuvaraj.offical06@gmail.com"  # Replace with your email
SENDER_PASSWORD = "muyl feop nvdm fooy" 
sent_otp = None
email = None


# Import MongoDB data to Pandas DataFrames
def import_mongodb_data():
    # Initialize empty dictionaries to store DataFrames
    dataframes = {}

    # Iterate over each collection in the database
    for collection_name in db.list_collection_names():
        # Get the collection object
        collection = db[collection_name]

        # Convert the collection data to a Pandas DataFrame
        df = pd.DataFrame(list(collection.find()))

        # Add the DataFrame to the dictionary
        dataframes[collection_name] = df

    return dataframes



# Call the function to import data
dataframes = import_mongodb_data()

# Access each DataFrame by its collection name
users_df = dataframes['users']
expenses_df = dataframes['expense']
categories_df = dataframes['categories']
subcategories_df = dataframes['subcategories']

dataframes = import_mongodb_data()

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    global user_id
    global dataframes
    if request.method == 'POST':
        otp = request.form.get('otp')        
        print(f"Entered OTP: {otp}, Sent OTP: {sent_otp}")  # Debugging line
        if otp == sent_otp:
            user = users.find_one({'email': email})
            if user:
                user_id = user['_id']
            print(f'user_id: {user_id}')
            print(dataframes)  # Debugging line
            return render_template('dashboard.html')
        else:
            return render_template('error.html')

def send_otp(email):
    """Generate and send OTP via email"""
    global sent_otp
    sent_otp = str(random.randint(100000, 999999))

    message = EmailMessage()
    message.set_content(f"Your OTP is: {sent_otp}")
    message["Subject"] = "Your Login OTP"
    message["From"] = SENDER_EMAIL
    message["To"] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=ssl.create_default_context())  # Secure connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        print(f"OTP sent successfully!: {sent_otp}")
        return sent_otp
    except Exception as e:
        print("Error sending email:", e)
        return None

@app.route('/', methods=['GET', 'POST'])
def authentication():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global user_id
    if request.method == 'POST':
        email = request.form.get('email')
        user = users.find_one({'email': email})
        if user:
            user_id = user['_id']
            print('user_id updated' + str(user_id))
            return redirect(url_for('home'))
    return render_template('login.html')



@app.route('/relogin',methods=['GET','POST'])
def relogin():
    global user_id
    if request.method=='POST':
        otp=request.form.get('otp')
        if sent_otp==otp:
            users.insert_one({
                'email':email,
                'first_name':firstname,
                'last_name':lastname
            })
            user = users.find_one({'email': email})
            if user:
                user_id = user['_id']
        return render_template('login.html')



@app.route('/enterotp', methods=['POST','GET'])
def enterotp():
    global email
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            return redirect(url_for('login'))
        user = users.find_one({'email':email})
        if user:
            otp = send_otp(email)
            print(otp)
            if otp:
                return render_template('enterotp.html', email=email, otp=otp)
            else:
                return "Failed to send OTP"
        else:
            return redirect('error.html')
        


@app.route('/signupotp', methods=['POST','GET'])
def signupotp():
    if request.method == 'POST':
        global firstname, lastname, email  # Declare as global to use in other functions
        email = request.form.get('email')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        if not email or not firstname or not lastname:
            return redirect('error.html')
        user = users.find_one({"email":email})
        if user:
            return "you already have an account, try logging in instead"
        else:
            otp = send_otp(email)
            if otp:             
                return render_template('signupotp.html', email=email, firstname=firstname, lastname=lastname)
            else:
                return redirect('error.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')



@app.route('/categories')
def categories():
    global user_id, category
    if not user_id:
        return "User not authenticated", 401

    # Fetch all categories for the user
    categories = list(category.find({"user_id": user_id}, {"_id": 0, "category": 1}))
    category_list = [cat["category"] for cat in categories]

    # Group categories into slides of 5 items each
    slides = [category_list[i:i + 5] for i in range(0, len(category_list), 5)]

    return render_template('categories.html', slides=slides)


@app.route('/deletecat', methods=['GET', 'POST'])
def deletecat():
    if request.method == 'POST':
        global user_id, category
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        catname = request.form.get('catname')
        print("Received catname:", catname)  # Debugging

        if not catname:
            return jsonify({"error": "Invalid or missing category"}), 400

        query = {"user_id": user_id, "category": catname}
        print("Querying with:", query)  # Debugging

        found = list(category.find(query, {'_id': 0}))
        print("Found categories:", found)  # Debugging

        if not found:
            return jsonify({"message": "No expenses found"}), 404

        category.delete_many(query)
        return redirect(url_for('categories'))

    return render_template('categories.html')

        



@app.route('/addcat', methods=['GET', 'POST'])
def addcat():
    global user_id, category, subcategory
    if request.method == 'POST':
        category_input = request.form.get('category').strip()
        subcategory_input = request.form.get('subcategory').strip()

        if not category_input or not subcategory_input:
            return "fields cannot be empty"

        category_doc = category.find_one({"user_id": user_id, "category": category_input})
        
        if category_doc:
            print(category_doc)
        
        # Insert category and get its ID
        new_category = {
            "user_id": user_id,
            "category": category_input
        }
        category_insert = category.insert_one(new_category)
        newcatid = category_insert.inserted_id

        # Check if subcategory exists
        subcategory_doc = subcategory.find_one({"user_id": user_id, "category_id": newcatid, "subcategory": subcategory_input})


        # Insert subcategory
        new_subcategory = {
            "user_id": user_id,
            "category_id": newcatid,
            "category": category_input,
            "subcategory": subcategory_input,
        }
        subcategory.insert_one(new_subcategory)

        
        return redirect(url_for('categories'))

    return render_template('category.html')

@app.route('/subcategories', methods=['GET', 'POST'])
def subcategories():
    global user_id, category, subcategory
    categories = list(category.find({}, {"_id": 0, "category": 1}))
        
        
    category_dict = {}
    
    for item in categories:
        category_name = item["category"]
    
        subcategories = list(subcategory.find({"category": category_name}, {"_id": 0, "subcategory": 1}))
        category_dict[category_name] = [sub["subcategory"] for sub in subcategories]
    
    return render_template('subcategories.html', category_dict=category_dict)
    

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
        global user_id,expense,categories,subcategories
        if not user_id:
            return "User ID is required", 400

        query = {'user_id': user_id}
        expenses_list = list(expense.find(query, {'_id': 0}))  # Fetch all expenses for user_id

        return render_template("expenses.html", expenses=expenses_list)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    return render_template('profile.html')

def generate_graph():
    try:
        plt.figure(figsize=(5, 3))
        x = [1, 2, 3, 4, 5]
        y = [10, 15, 7, 12, 18]
        plt.plot(x, y, marker='o')
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")
        plt.title("Generated Graph")

        # Save plot to a BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        
        # Encode to Base64
        graph_url = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        return graph_url
    except Exception as e:
        print(f"Error generating graph: {e}")
        return None

@app.route('/home',methods=['GET','POST'])
def home():
    data = {
        "January":3000,
        "February":4000,
        "March":5000,   
        "April":6000,
        "May":7000,
        "June":8000,
        "July":9000,
        "August":10000,
        "September":11000,
        "October":12000,
        "November":13000,
        "December":14000
    }
    labels=[row[0] for row in data]
    values=[row[1] for row in data]
    print(f"Labels: {labels}")
    print(f"Values: {values}")
    return render_template("dashboard.html",labels=labels, values=values)

print(user_id)


@app.route('/deletesubcat', methods=['POST'])
def deletesubcat():
    if request.method=='POST':
        global user_id, category, subcategory, db

        if not user_id:
            return "OOPS! an error occoured, try logging in once again"

        cat = request.form.get('category')
        subcat = request.form.get('subcategory')

        if not cat or not subcat:
            return redirect(url_for('subcategories'))

        query = {"user_id":user_id}

        if cat:
            query["category"] = cat
        else:
            return 'error! invalid or no category'

        if subcat:
            query["subcategory"] = subcat
        else:
            return 'error! invalid or no subcategory'

        found = list(subcategory.find(query, {'_id': 0})) 

        if not found:
            return jsonify({"message": "No expenses found"}), 404
        else:
            subcategory.delete_one(query)
            return redirect(url_for('subcategories'))
    return redirect(url_for('subcategories'))






@app.route('/deleteexpense', methods=['GET', 'POST'])
def deleteexpense():

    global user_id, expense, category, subcategory

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    amount = request.form.get('amount')
    category_input = request.form.get('category')
    subcategory_input = request.form.get('subcategory')
    date_input = request.form.get('date')

    print(f'amount: {amount}, category: {category_input}, subcategory: {subcategory_input}, date: {date_input}')

    query = {'user_id': user_id}

    if amount:
        try:
            amount = float(amount)
            query['amount'] = amount
        except ValueError:
            return jsonify({"error": "Invalid Amount"}), 400

    if category_input:
        category_entered = category.find_one({'category': category_input})
        if category_entered:
            query['category'] = category_entered['category']
        else:
            return jsonify({"error": "Invalid Category"}), 400

    if subcategory_input:
        subcategory_entered = subcategory.find_one({'subcategory': subcategory_input})
        if subcategory_entered:
            query['subcategory'] = subcategory_entered['subcategory']
        else:
            return jsonify({"error": "Invalid Subcategory"}), 400

    if date_input:
        try:
            # Handle multiple date formats (DD/MM/YYYY or YYYY-MM-DD)
            if "/" in date_input:
                parsed_date = datetime.strptime(date_input, "%d/%m/%Y")  # If format is DD/MM/YYYY
            elif "-" in date_input:
                parsed_date = datetime.strptime(date_input, "%Y-%m-%d")  # If format is YYYY-MM-DD
            else:
                return jsonify({"error": "Invalid Date Format. Use DD/MM/YYYY or YYYY-MM-DD"}), 400

            # Convert to start and end of the day
            start_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

            query['date'] = {'$gte': start_date, '$lt': end_date}
        except ValueError as e:
            print(f"Date parsing error: {e}")  # Debugging message
            return jsonify({"error": "Invalid Date Format. Use DD/MM/YYYY or YYYY-MM-DD"}), 400

    found = list(db.expense.find(query, {'_id': 0}))  # Convert cursor to list

    if not found:
        return jsonify({"message": "No expenses found"}), 404

    db.expense.delete_one(query)

    return redirect(url_for('expenses'))

@app.route('/addsubcat', methods=['GET', 'POST'])
def addsubcat():
    if request.method == 'POST':
        global user_id, category, subcategory  # Ensure these are properly defined elsewhere.

        category_input = request.form.get('category')
        subcategory_input = request.form.get('subcategory')  # Correct variable name

        category_doc = category.find_one({"user_id": user_id, "category": category_input})
        if not category_doc:
            return 'Category not found. Check the table above for available categories.'
        
        category_entered = category.find_one({'category': category_input})
        subcategory_entered = subcategory.find_one({'subcategory': subcategory_input})

        if category_entered:
            if subcategory_entered:
                return 'Subcategory already exists. Please choose a different one.'

        category_id = category_doc["_id"]

        new_subcategory = {
            "user_id": user_id,
            "category_id": category_id,
            "category": category_input,  # Fix: Use category name instead of collection
            "subcategory": subcategory_input  # Fix: Correct variable name
        }

        # Ensure subcategory is the correct MongoDB collection reference
        subcollection = db.subcategories  # Use the actual MongoDB collection
        result = subcollection.insert_one(new_subcategory)

        return url_for('subcategories')
    return render_template('subcategory.html')



@app.route('/addexpense',methods=['GET','POST'])
def addexpense():    
    if request.method == 'POST':
        global user_id
        global category
        global subcategory
        if not user_id:
            return 'User not logged in'

        if user_id is None:
            return 'User not logged in'
        
        print(user_id)

        category_input = request.form.get('category')
        subcategory_input = request.form.get('subcategory')
        amount = request.form.get('amount')

        print(category,subcategory,amount)

        # Validate amount
        try:
            amount = float(amount)
        except ValueError:
            return render_template('error.html', error='Invalid Amount')
        print(user_id)

        user = users.find_one({'_id': user_id})
        print(user)

        if user:
            category_entered = category.find_one({'category': category_input})
            subcategory_entered = subcategory.find_one({'subcategory': subcategory_input, 'category': category_input})
            if category_entered and subcategory_entered:
                expense.insert_one({
                    'user_id': user_id,
                    'category': category_entered['category'],
                    'subcategory': subcategory_entered['subcategory'],
                    'amount': amount,
                    'date': datetime.now()
                })
                return redirect(url_for('expenses'))
            else:
                return f'invalid category, create it first to better organise your expenses'
        else:
            return 'invalid user'



if __name__ == "__main__":
    app.run(debug=True)
