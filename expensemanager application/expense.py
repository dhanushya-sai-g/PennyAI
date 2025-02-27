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
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox

user_id = None

# MongoDB Atlas Connection
MONGO_URI = "mongodb+srv://dhanushya:frooti@projects.r87yn.mongodb.net/?retryWrites=true&w=majority&appName=Projects"
client = pymongo.MongoClient(MONGO_URI)
db = client["PennyAI"]  # Database Name
users_collection = db["users"]  # Collection Name
expenses_collection = db["expense"]
categories_collection = db["categories"] 
subcategories_collection = db["subcategories"]

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "yuvaraj.offical06@gmail.com"  # Replace with your email
SENDER_PASSWORD = "muyl feop nvdm fooy"  # Replace with your app password

def list_categories():
    categories = categories_collection.find({"user_id": user_id})
    return list(categories)

def send_otp(email):
    """Generate and send OTP via email"""
    otp = str(random.randint(100000, 999999))

    message = EmailMessage()
    message.set_content(f"Your OTP is: {otp}")
    message["Subject"] = "Your Login OTP"
    message["From"] = SENDER_EMAIL
    message["To"] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=ssl.create_default_context())  # Secure connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        print("OTP sent successfully!")
        return otp
    except Exception as e:
        print("Error sending email:", e)
        return None

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("800x600")
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initially show login/signup frame
        self.show_auth_frame()
        
    def show_auth_frame(self):
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Welcome to Expense Tracker", font=('Helvetica', 16)).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Button(self.main_frame, text="Login", command=self.show_login_frame).grid(row=1, column=0, padx=10)
        ttk.Button(self.main_frame, text="Signup", command=self.show_signup_frame).grid(row=1, column=1, padx=10)
        
    def show_login_frame(self):
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Login", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(self.main_frame, text="Email:").grid(row=1, column=0)
        email_entry = ttk.Entry(self.main_frame)
        email_entry.grid(row=1, column=1)
        
        def handle_login():
            email = email_entry.get()
            user = users_collection.find_one({"email": email})
            
            if not user:
                messagebox.showerror("Error", "Email not found! Please sign up first.")
                self.show_signup_frame()
                return
                
            otp_sent = send_otp(email)
            if otp_sent:
                otp_window = tk.Toplevel(self.root)
                otp_window.title("OTP Verification")
                
                ttk.Label(otp_window, text="Enter OTP:").grid(row=0, column=0)
                otp_entry = ttk.Entry(otp_window)
                otp_entry.grid(row=0, column=1)
                
                def verify_otp():
                    global user_id
                    if otp_entry.get() == otp_sent:
                        user_id = user["_id"]
                        messagebox.showinfo("Success", "Login successful!")
                        otp_window.destroy()
                        self.show_main_menu()
                    else:
                        messagebox.showerror("Error", "Invalid OTP")
                        otp_window.destroy()
                        
                ttk.Button(otp_window, text="Verify", command=verify_otp).grid(row=1, column=0, columnspan=2)
                
        ttk.Button(self.main_frame, text="Login", command=handle_login).grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text="Back", command=self.show_auth_frame).grid(row=3, column=0, columnspan=2)
        
    def show_signup_frame(self):
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Signup", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(self.main_frame, text="First Name:").grid(row=1, column=0)
        first_name_entry = ttk.Entry(self.main_frame)
        first_name_entry.grid(row=1, column=1)
        
        ttk.Label(self.main_frame, text="Last Name:").grid(row=2, column=0)
        last_name_entry = ttk.Entry(self.main_frame)
        last_name_entry.grid(row=2, column=1)
        
        ttk.Label(self.main_frame, text="Email:").grid(row=3, column=0)
        email_entry = ttk.Entry(self.main_frame)
        email_entry.grid(row=3, column=1)
        
        def handle_signup():
            email = email_entry.get()
            if users_collection.find_one({"email": email}):
                messagebox.showerror("Error", "Email already registered!")
                return
                
            otp_sent = send_otp(email)
            if otp_sent:
                otp_window = tk.Toplevel(self.root)
                otp_window.title("OTP Verification")
                
                ttk.Label(otp_window, text="Enter OTP:").grid(row=0, column=0)
                otp_entry = ttk.Entry(otp_window)
                otp_entry.grid(row=0, column=1)
                
                def verify_otp():
                    if otp_entry.get() == otp_sent:
                        users_collection.insert_one({
                            "first_name": first_name_entry.get(),
                            "last_name": last_name_entry.get(),
                            "email": email
                        })
                        messagebox.showinfo("Success", "Signup successful!")
                        otp_window.destroy()
                        self.show_login_frame()
                    else:
                        messagebox.showerror("Error", "Invalid OTP")
                        otp_window.destroy()
                        
                ttk.Button(otp_window, text="Verify", command=verify_otp).grid(row=1, column=0, columnspan=2)
                
        ttk.Button(self.main_frame, text="Signup", command=handle_signup).grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text="Back", command=self.show_auth_frame).grid(row=5, column=0, columnspan=2)
        
    def show_main_menu(self):
        self.clear_frame()
        
        buttons = [
            ("Add Expense", self.show_add_expense),
            ("View Expenses", self.show_view_expenses),
            ("Delete Expense", self.show_delete_expense),
            ("Create Category", self.show_create_category),
            ("Delete Category", self.show_delete_category),
            ("Create Subcategory", self.show_create_subcategory),
            ("Delete Subcategory", self.show_delete_subcategory),
            ("Display Summary", self.show_summary),
            ("Display Expenses Table", self.show_expenses_table),
            ("List Categories", self.show_categories),
            ("List Subcategories", self.show_subcategories),
            ("Logout", self.show_auth_frame)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(self.main_frame, text=text, command=command).grid(row=i, column=0, pady=5, padx=10, sticky="ew")
            
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
    def show_add_expense(self):
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Add Expense", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(self.main_frame, text="Category:").grid(row=1, column=0)
        category_entry = ttk.Entry(self.main_frame)
        category_entry.grid(row=1, column=1)
        
        ttk.Label(self.main_frame, text="Subcategory:").grid(row=2, column=0)
        subcategory_entry = ttk.Entry(self.main_frame)
        subcategory_entry.grid(row=2, column=1)
        
        ttk.Label(self.main_frame, text="Amount:").grid(row=3, column=0)
        amount_entry = ttk.Entry(self.main_frame)
        amount_entry.grid(row=3, column=1)
        
        def handle_add():
            category = category_entry.get()
            subcategory = subcategory_entry.get()
            try:
                amount = float(amount_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number")
                return
                
            date = datetime.now()
            expenses_collection.insert_one({
                "user_id": user_id,
                "category": category,
                "subcategory": subcategory,
                "amount": amount,
                "date": date
            })
            messagebox.showinfo("Success", "Expense added successfully!")
            self.show_main_menu()
            
        ttk.Button(self.main_frame, text="Add", command=handle_add).grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=5, column=0, columnspan=2)
        
    def show_view_expenses(self):
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="View Expenses", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        expenses = expenses_collection.find({"user_id": user_id})
        for i, expense in enumerate(expenses, 1):
            text = f"{expense['category']} - {expense['subcategory']} - ${expense['amount']} on {expense['date']}"
            ttk.Label(self.main_frame, text=text).grid(row=i, column=0, columnspan=2)
            
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=i+1, column=0, columnspan=2, pady=20)
        
    def show_delete_expense(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Delete Expense", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        expenses = expenses_collection.find({"user_id": user_id})
        expense_list = list(expenses)
        
        if not expense_list:
            ttk.Label(self.main_frame, text="No expenses found").grid(row=1, column=0, columnspan=2)
        else:
            for i, expense in enumerate(expense_list, 1):
                text = f"{expense['category']} - {expense['subcategory']} - ${expense['amount']} on {expense['date']}"
                ttk.Label(self.main_frame, text=text).grid(row=i, column=0)
                
                def create_delete_handler(exp_id):
                    def handle_delete():
                        expenses_collection.delete_one({"_id": exp_id})
                        messagebox.showinfo("Success", "Expense deleted successfully!")
                        self.show_delete_expense()
                    return handle_delete
                
                delete_btn = ttk.Button(
                    self.main_frame, 
                    text="Delete",
                    command=create_delete_handler(expense['_id'])
                )
                delete_btn.grid(row=i, column=1)
        
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(
            row=len(expense_list)+1 if expense_list else 2, 
            column=0, 
            columnspan=2, 
            pady=20
        )
        
    def show_create_category(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Create Category", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(self.main_frame, text="Category Name:").grid(row=1, column=0, pady=5)
        category_name = ttk.Entry(self.main_frame)
        category_name.grid(row=1, column=1, pady=5)
        
        def save_category():
            name = category_name.get().strip()
            if name:
                categories_collection.insert_one({
                    "user_id": user_id,
                    "name": name,
                    "created_at": datetime.now()
                })
                messagebox.showinfo("Success", "Category created successfully!")
                category_name.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Please enter a category name")
                
        ttk.Button(self.main_frame, text="Save", command=save_category).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=3, column=0, columnspan=2, pady=10)
        
    def show_delete_category(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Delete Category", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        categories = list_categories()
        
        if not categories:
            ttk.Label(self.main_frame, text="No categories found").grid(row=1, column=0, columnspan=2)
        else:
            for i, category in enumerate(categories):
                text = f"{category['name']}"
                ttk.Label(self.main_frame, text=text).grid(row=i+1, column=0)
                
                def create_delete_handler(cat_id):
                    def handle_delete():
                        # Delete all expenses in this category first
                        expenses_collection.delete_many({"category": cat_id})
                        # Delete all subcategories in this category
                        subcategories_collection.delete_many({"category_id": cat_id})
                        # Delete the category
                        categories_collection.delete_one({"_id": cat_id})
                        messagebox.showinfo("Success", "Category and related items deleted successfully!")
                        self.show_delete_category()
                    return handle_delete
                
                delete_btn = ttk.Button(
                    self.main_frame,
                    text="Delete",
                    command=create_delete_handler(category['_id'])
                )
                delete_btn.grid(row=i+1, column=1)
        
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(
            row=len(categories)+1 if categories else 2,
            column=0,
            columnspan=2,
            pady=20
        )
        
    def show_create_subcategory(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Create Subcategory", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        # Get list of categories for dropdown
        categories = list_categories()
        if not categories:
            ttk.Label(self.main_frame, text="Please create a category first").grid(row=1, column=0, columnspan=2)
            ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=2, column=0, columnspan=2, pady=10)
            return
            
        ttk.Label(self.main_frame, text="Select Category:").grid(row=1, column=0)
        category_var = tk.StringVar()
        category_dropdown = ttk.Combobox(self.main_frame, textvariable=category_var)
        category_dropdown['values'] = [cat['name'] for cat in categories]
        category_dropdown.grid(row=1, column=1)
        
        ttk.Label(self.main_frame, text="Subcategory Name:").grid(row=2, column=0)
        subcategory_name = ttk.Entry(self.main_frame)
        subcategory_name.grid(row=2, column=1)
        
        def save_subcategory():
            selected_category = category_var.get()
            subcat_name = subcategory_name.get()
            
            if selected_category and subcat_name:
                # Find the category id
                category = next((cat for cat in categories if cat['name'] == selected_category), None)
                if category:
                    subcategories_collection.insert_one({
                        "name": subcat_name,
                        "category_id": category['_id'],
                        "user_id": user_id
                    })
                    messagebox.showinfo("Success", "Subcategory created successfully!")
                    subcategory_name.delete(0, tk.END)
                    category_dropdown.set('')
                else:
                    messagebox.showerror("Error", "Please select a valid category")
            else:
                messagebox.showerror("Error", "Please fill all fields")
                
        ttk.Button(self.main_frame, text="Save", command=save_subcategory).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=4, column=0, columnspan=2, pady=10)
        
    def show_delete_subcategory(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Delete Subcategory", font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        # Get list of categories and their subcategories
        categories = list_categories()
        if not categories:
            ttk.Label(self.main_frame, text="No categories found").grid(row=1, column=0, columnspan=2)
            ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=2, column=0, columnspan=2, pady=10)
            return
            
        # Category dropdown
        ttk.Label(self.main_frame, text="Select Category:").grid(row=1, column=0)
        category_var = tk.StringVar()
        category_dropdown = ttk.Combobox(self.main_frame, textvariable=category_var)
        category_dropdown['values'] = [cat['name'] for cat in categories]
        category_dropdown.grid(row=1, column=1)
        
        # Subcategory dropdown
        ttk.Label(self.main_frame, text="Select Subcategory:").grid(row=2, column=0)
        subcategory_var = tk.StringVar()
        subcategory_dropdown = ttk.Combobox(self.main_frame, textvariable=subcategory_var)
        subcategory_dropdown.grid(row=2, column=1)
        
        def update_subcategories(*args):
            selected_category = category_var.get()
            category = next((cat for cat in categories if cat['name'] == selected_category), None)
            if category:
                subcategories = list(subcategories_collection.find({"category_id": category['_id'], "user_id": user_id}))
                subcategory_dropdown['values'] = [subcat['name'] for subcat in subcategories]
            else:
                subcategory_dropdown['values'] = []
            subcategory_dropdown.set('')
            
        category_var.trace('w', update_subcategories)
        
        def delete_subcategory():
            selected_category = category_var.get()
            selected_subcategory = subcategory_var.get()
            
            if not selected_category or not selected_subcategory:
                messagebox.showerror("Error", "Please select both category and subcategory")
                return
                
            category = next((cat for cat in categories if cat['name'] == selected_category), None)
            if category:
                result = subcategories_collection.delete_one({
                    "name": selected_subcategory,
                    "category_id": category['_id'],
                    "user_id": user_id
                })
                
                if result.deleted_count > 0:
                    messagebox.showinfo("Success", "Subcategory deleted successfully!")
                    category_dropdown.set('')
                    subcategory_dropdown.set('')
                else:
                    messagebox.showerror("Error", "Failed to delete subcategory")
                    
        ttk.Button(self.main_frame, text="Delete", command=delete_subcategory).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(self.main_frame, text="Back", command=self.show_main_menu).grid(row=4, column=0, columnspan=2, pady=10)
        
    def show_summary(self):
        self.clear_frame()
        # Similar implementation for summary
        
    def show_expenses_table(self):
        self.clear_frame()
        # Similar implementation for expenses table
        
    def show_categories(self):
        self.clear_frame()
        # Similar implementation for categories list
        
    def show_subcategories(self):
        self.clear_frame()
        # Similar implementation for subcategories list

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
