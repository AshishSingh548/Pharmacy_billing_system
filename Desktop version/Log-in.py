from tkinter import *
from tkinter import messagebox
import pymysql as sql
from PIL import ImageTk

# Set up the Main Windows
top = Tk()
top.geometry("1200x700")
top.title("Welcome")
# top.resizable(0,0)
top.config(bg='light blue')

try:
    img = ImageTk.PhotoImage(file=r"C:\Users\VICTUS1\Downloads\pharmacy-background-bomnaifdze6cde601.jpg")
    L9 = Label(top, image=img)
    L9.place(x=0, y=0)
except Exception:
    print("Image not found, skipping image display.")


def login():
    db = sql.connect(host='localhost', user='root', password='0805', db='log')
    cur = db.cursor()
    cur.execute("select * from dongra where name=%s and password = %s", (e_emp_name.get(), e_password.get()))
    result = cur.fetchone()  # Fetch one record instead of all

    if result is None:  # Check if result is empty
        messagebox.showerror("Error", "Invalid User Name and Password")
    else:
        messagebox.showinfo("Success", "Login Successful")
        top.destroy()
        import Project
    db.close()

# Updated ShowPassword to be flexible
def ShowPassword(target_entry):
    if target_entry.cget('show') == "*":
        target_entry.config(show='')
    else:
        target_entry.config(show="*")


def UpdatePass():
    top2 = Toplevel()
    top2.geometry("1200x700")
    top2.title("Reset Password")

    try:
        global img2
        img2 = ImageTk.PhotoImage(
            file=r"C:\Users\VICTUS1\Downloads\pharmacy-background-bomnaifdze6cde601.jpg")
        Label(top2, image=img2).place(x=0, y=0)
    except Exception:
        print("Image not found.")

    Label(top2, text='Reset Your Password', fg='black', bg='light blue', font='Arial 23 bold').place(x=780, y=80)

    # Input Fields
    Label(top2, text='Enter Name', fg='black', bg='light blue', font='Helvetica 18 bold').place(x=700, y=180)
    e_name = Entry(top2, font='Arial 20 bold')
    e_name.place(x=900, y=180, width=220)

    Label(top2, text='Old Password', fg='black', bg='light blue', font='Helvetica 18 bold').place(x=700, y=230)
    e_old_pass = Entry(top2, font='Arial 20 bold', show="*")
    e_old_pass.place(x=900, y=230, width=220)

    Label(top2, text='New Password', fg='black', bg='light blue', font='Helvetica 18 bold').place(x=700, y=280)
    e_new_pass = Entry(top2, font='Arial 20 bold', show="*")
    e_new_pass.place(x=900, y=280, width=220)

    def SaveNewPass():
        name = e_name.get()
        old_p = e_old_pass.get()
        new_p = e_new_pass.get()

        if not name or not old_p or not new_p:
            messagebox.showwarning("Input Error", "All fields are required")
            return

        try:
            db = sql.connect(host='localhost', user='root', password='0805', db='log')
            cur = db.cursor()

            # Does if Name and Old Password match
            check_query = "SELECT * FROM dongra WHERE name=%s AND password=%s"
            cur.execute(check_query, (name, old_p))
            user_record = cur.fetchone()

            if user_record:
                # STEP 2: If match
                update_query = "UPDATE dongra SET password=%s WHERE name=%s"
                cur.execute(update_query, (new_p, name))
                db.commit()
                messagebox.showinfo("Success", "Password Updated Successfully")
                top2.destroy()
            else:
                # STEP 3: If they don't match
                messagebox.showerror("Error", "Old password is incorrect. Please enter a valid password.")

            db.close()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # Buttons and Checkboxes
    Button(top2, text='Update Password', font='Arial 18 bold', command=SaveNewPass).place(x=840, y=340)

    # Checkbox to show/hide the NEW password
    Checkbutton(top2, command=lambda: ShowPassword(e_new_pass)).place(x=1125, y=285)

    top2.mainloop()




    # 4. Setup UI Widgets
Label(top, text='Admin-Log-In', fg='black', bg='light blue', font='Arial 23 bold').place(x=850, y=50)

# Name
Label(top, text='Emp-Name', fg='black', bg='light blue', font='Helvetica 18 bold').place(x=750, y=150)
e_emp_name = Entry(top, font='Helvetica 18 bold')
e_emp_name.place(x=900, y=150, width=255)

# Password
Label(top, text='Password', fg='black', bg='light blue', font='Helvetica 18 bold').place(x=750, y=200)
e_password = Entry(top, font='Helvetica 18 bold', show="*")
e_password.place(x=900, y=200, width=255)

# Buttons
Button(top, text='Log-In', font='Helvetica 17 bold', command=login).place(x=800, y=260)

Button(top, text='Forgot Password', font='Helvetica 17 bold', command=UpdatePass).place(x=930, y=260)

Checkbutton(top, command=lambda: ShowPassword(e_password)).place(x=1165, y=205)

# Start the Loop
top.mainloop()