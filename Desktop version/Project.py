from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import pymysql as sql
import datetime
from tkcalendar import DateEntry


db_config = {'host': 'localhost','user': 'root','password': '0805','database': 'log'}
bill_no = NONE

current_tax_per = 0.0

# Main Window
top = Tk()
top.geometry("1300x900")
top.title("Bill")
# top.resizable(0, 0)
# top.iconbitmap(r"C:\Users\VICTUS1\Downloads\animal_animals_bird_zoo_ornithology_vulture_icon_266850.webp")
top.config(bg='light blue')

# Logics
def db_conn():
    try:
        return sql.connect(**db_config)
    except Exception as e:
        messagebox.showerror("DB Error",  str(e))
        return None

def next_bill_no():           # Ye auto-generate the bill no
    conn = db_conn()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(bill_no) FROM bills")
            res = cursor.fetchone()[0]
            next_no = 1 if res is None else res + 1

            # Update the Bill No Entry
            if e_bill_no:
                e_bill_no.delete(0, END)
                e_bill_no.insert(0, next_no)
        except Exception as e:
            print("Error fetching bill no", str(e))
        finally:
            conn.close()

def get_product_details(gulabo):
    name = e_name.get()
    if not name:
        return

    conn = db_conn()
    global current_tax_per

    if conn:
        try:
            cursor = conn.cursor()
            # This will Fetch Rate and Tax% from database
            cursor.execute("SELECT rate, tax_per FROM products WHERE name=%s", (name,))
            row = cursor.fetchone()

            if row:
                rate = float(row[0])
                current_tax_per = float(row[1])

                e_rate.delete(0, END)
                e_rate.insert(0, rate)

                # Move focus to Quantity box
                e_qty.focus_set()
            else:
                messagebox.showerror("Error", "Medicine not found!")
                e_rate.delete(0, END)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

def add_to_list(gulabo):

    try:
        name = e_name.get()
        rate_str = e_rate.get()
        qty_str = e_qty.get()

        if not name or not rate_str or not qty_str:
            messagebox.showwarning("Missing Data", "Please ensure Name, Rate and Qty are filled")
            return

        rate = float(rate_str)
        qty = int(qty_str)

        # Calculate Amount
        amount = rate * qty
        e_amt.delete(0, END)
        e_amt.insert(0, amount)

        dis_per = 0.0           # Always 0
        dis_amt = 0.0

        # Add to Treeview
        # Values: Name, Rate, Qty, Amount, Dis%, DisAmt, Total, Tax%
        tv2.insert('', 'end', values=(name, rate, qty, amount, dis_per, dis_amt, amount, current_tax_per))

        # Clear the Input fields for next medicine
        e_name.delete(0, END)
        e_qty.delete(0, END)
        e_rate.delete(0, END)
        e_amt.delete(0, END)

        # Update the Bottom Totals
        calculate_bottom_totals()

        # Set focus back to Name for next item
        e_name.focus_set()

    except ValueError:
        messagebox.showerror("Error", "Please enter valid Quantity")

def fetch_bill_data(bill_number):
    conn = db_conn()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # 1. Fetch Header Info from 'bills' table
        # Matches the order in your Save function
        query = "SELECT * FROM bills WHERE bill_no = %s"
        cursor.execute(query, (bill_number,))
        row = cursor.fetchone()

        if row:
            # Found the bill Clear current screen first
            refresh()

            # --- Fill Header Fields ---
            # row[0] is bill_no
            e_bill_no.delete(0, END)
            e_bill_no.insert(0, row[0])

            # row[1] is Date. Update DateEntry
            cal.set_date(row[1])

            update_entry(e_dr, row[2])  # Dr Name
            update_entry(e_pt, row[3])  # Pt Name
            update_entry(e_mob, row[4])  # Mobile
            update_entry(e_addr, row[5])  # Address
            update_entry(e_diag, row[6])  # Diagnosis

            #  Bottom Totals
            update_entry(e_total_items, row[7])
            update_entry(e_total_qty, row[8])
            update_entry(e_sub_total, row[9])
            update_entry(e_dis_per, row[10])
            update_entry(e_dis_amt, row[11])

            # CGST/SGST/Grand Total
            update_entry(e_cgst, row[12])
            update_entry(e_sgst, row[13])
            update_entry(e_igst, row[14])
            update_entry(e_grand_total, row[15])
            update_entry(e_add_amt, row[16])
            update_entry(e_round_off, row[17])
            update_entry(e_net_total, row[18])

            # Pay Mode
            e_pay_mode.set(row[19])

            # Recalculate Net Total for display
            try:
                g_tot = float(row[12])
                net = round(g_tot)
                update_entry(e_net_total, f"{net}.00")
                update_entry(e_round_off, f"{net - g_tot:.2f}")
            except:
                pass

            # Fetching Items from bill_items table
            cursor.execute("SELECT * FROM bill_items WHERE bill_no = %s", (bill_number,))
            items = cursor.fetchall()

            # Insert into Treeview
            for item in items:

                name = item[2]
                rate = item[3]
                qty = item[4]
                amt = item[5]
                total = item[6]
                tax = item[7]

                # Insert row
                tv2.insert('', 'end', values=(name, rate, qty, amt, "0", "0", total, tax))

        else:
            messagebox.showerror("Not Found", f"Bill Number {bill_number} does not exist.")

    except Exception as e:
        messagebox.showerror("Error", f"Could not fetch bill: {e}")
    finally:
        conn.close()


def load_last_bill():

    try:
        current_no = int(e_bill_no.get())
        if current_no > 1:
            fetch_bill_data(current_no - 1)
        else:
            messagebox.showinfo("Info", "This is the first bill.")
    except ValueError:
        messagebox.showerror("Error", "Invalid Bill Number")


def load_next_bill():

    try:
        current_no = int(e_bill_no.get())
        fetch_bill_data(current_no + 1)
    except ValueError:
        messagebox.showerror("Error", "Invalid Bill Number")


def show_last_50_bills():

    win = Toplevel(top)
    win.title("Search History")
    win.geometry("1000x600") 
    win.config(bg="light blue")
    
    # Search Section 
    # Bill Number Search
    Label(win, text="Search by Bill No:", bg="light blue", font=("Arial", 11, "bold")).place(x=20, y=20)

    e_search_bill = Entry(win, font=("Arial", 11), width=12)
    e_search_bill.place(x=170, y=20)

    btn_bill = Button(win, text="Search No 🔢", bg="Pale green", font=("Arial", 10, "bold"))
    btn_bill.place(x=290, y=18)

    #  OR Separator
    Label(win, text="| OR |", bg="light blue", fg="gray", font=("Arial", 12, "bold")).place(x=410, y=20)

    # Date Search
    Label(win, text="Search by Date:", bg="light blue", font=("Arial", 11, "bold")).place(x=470, y=20)

    e_search_date = DateEntry(win, width=12, font=("Arial", 11), date_pattern='mm/dd/yy')
    e_search_date.place(x=600, y=20)

    btn_date = Button(win, text="Search Date 📅", bg="Pale green", font=("Arial", 10, "bold"))
    btn_date.place(x=730, y=18)

    # Reset Button
    btn_reset = Button(win, text="Show All 🔄", bg="Pale green", font=("Arial", 10, "bold"))
    btn_reset.place(x=860, y=18)

    #  Treeview Section 
    cols = ("Bill No", "Date", "Patient", "Total", "Mode")
    tv3 = ttk.Treeview(win, columns=cols, show="headings")

    tv3.heading("Bill No", text="Bill No")
    tv3.heading("Date", text="Date")
    tv3.heading("Patient", text="Patient Name")
    tv3.heading("Total", text="Grand Total")
    tv3.heading("Mode", text="Pay Mode")

    tv3.column("Bill No", width=80, anchor="center")
    tv3.column("Date", width=100, anchor="center")
    tv3.column("Patient", width=250,anchor="center")
    tv3.column("Total", width=100, anchor="center")
    tv3.column("Mode", width=100, anchor="center")

    # Placing the treeview manually
    tv3.place(x=20, y=70, width=960, height=500)

    # logic

    def clear_tree():
        for item in tv3.get_children():
            tv3.delete(item)

    def run_query(query, params=()):
        conn = db_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            clear_tree()
            for row in rows:
                tv3.insert("", "end", values=row)
            if not rows:
                messagebox.showinfo("Result", "No bills found.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def search_by_bill():
        bill_num = e_search_bill.get()
        if not bill_num:
            messagebox.showwarning("Warning", "Please enter a Bill Number")
            return
        e_search_date.delete(0, END)
        sql = "SELECT bill_no, bill_date, pt_name, grand_total, pay_mode FROM bills WHERE bill_no = %s"
        run_query(sql, (bill_num,))

    def search_by_date():
        raw_date = e_search_date.get()
        e_search_bill.delete(0, END)
        try:
            dt_obj = datetime.datetime.strptime(raw_date, '%m/%d/%y')
            sql_date = dt_obj.strftime('%Y-%m-%d')
            sql = "SELECT bill_no, bill_date, pt_name, grand_total, pay_mode FROM bills WHERE bill_date = %s"
            run_query(sql, (sql_date,))
        except ValueError:
            messagebox.showerror("Error", "Invalid Date Format")

    def show_all():
        e_search_bill.delete(0, END)
        sql = "SELECT bill_no, bill_date, pt_name, grand_total, pay_mode FROM bills ORDER BY bill_no DESC LIMIT 50"
        run_query(sql)

# Disable wala logic

    def on_bill_focus(gulabo):
        e_search_date.delete(0, END)

    def on_date_focus(gulabo):
        e_search_bill.delete(0, END)

    e_search_bill.bind("<FocusIn>", on_bill_focus)
    e_search_date.bind("<FocusIn>", on_date_focus)
    e_search_date._top_cal.bind("<FocusIn>", on_date_focus)

    # Connect Buttons
    btn_bill.config(command=search_by_bill)
    btn_date.config(command=search_by_date)
    btn_reset.config(command=show_all)

    # Load all data
    show_all()

def calculate_bottom_totals():
    # updates all bottom fields

    total_items = 0
    total_qty = 0
    sub_total = 0.0
    total_cgst_amt = 0.0
    total_sgst_amt = 0.0

    # Iterate through all items in Treeview
    for child in tv2.get_children():
        values = tv2.item(child)["values"]
        # values[2] is Qty, values[3] is Amount (before tax)
        qty = int(values[2])
        amt = float(values[3])
        tax_p = float(values[7])

        total_items += 1
        total_qty += qty
        sub_total += amt

        # Calculate Tax Amount for this row
        gst_amt = (amt * tax_p) / 100
        total_cgst_amt += gst_amt / 2
        total_sgst_amt += gst_amt / 2

    grand_total = sub_total + total_cgst_amt + total_sgst_amt

    # Update UI Fields
    update_entry(e_total_items, total_items)
    update_entry(e_total_qty, total_qty)
    update_entry(e_sub_total, f"{sub_total:.2f}")

    # Discount/IGST is 0 as requested
    update_entry(e_dis_per, "0")
    update_entry(e_dis_amt, "0")
    update_entry(e_igst, "0")

    update_entry(e_cgst, f"{total_cgst_amt:.2f}")
    update_entry(e_sgst, f"{total_sgst_amt:.2f}")

    update_entry(e_grand_total, f"{grand_total:.2f}")

    # Net Total
    net_tot = round(grand_total)
    update_entry(e_net_total, f"{net_tot}.00")

    # Additional Amount
    add_amt = grand_total - sub_total
    update_entry(e_add_amt, f"{add_amt:.2f}")

    # Round off
    round_diff = net_tot - grand_total
    update_entry(e_round_off, f"{round_diff:.2f}")

def update_entry(entry_widget, value):

    entry_widget.delete(0, END)
    if value is None:
        value = ""
    entry_widget.insert(0, str(value))

def save_bill():
    # Database saver
    bill_no = e_bill_no.get()

    # Get date from DateEntry
    raw_date = cal.get()
    try:
        # Convert mm/dd/yy format to yyyy-mm-dd format for my database
        dt_obj = datetime.datetime.strptime(raw_date, '%m/%d/%y')
        b_date = dt_obj.strftime('%Y-%m-%d')
    except:
        b_date = datetime.datetime.now().strftime('%Y-%m-%d')

    dr = e_dr.get()
    pt = e_pt.get()
    mob = e_mob.get()
    addr = e_addr.get()
    diag = e_diag.get()

    # Bottom values
    tot_items = e_total_items.get()
    tot_qty = e_total_qty.get()
    sub_tot = e_sub_total.get()
    dis_per = e_dis_per.get()
    dis_amt = e_dis_amt.get()
    cgst_val = e_cgst.get()
    sgst_val = e_sgst.get()
    igst_val = e_igst.get()
    grand = e_grand_total.get()
    add_amt = e_add_amt.get()
    round_off = e_round_off.get()
    net_tot = e_net_total.get()
    pay = e_pay_mode.get()

    if not bill_no or not pt:
        messagebox.showerror("Error", "Bill No and Patient Name are required")
        return

    conn = db_conn()
    if conn:
        try:
            cursor = conn.cursor()

            #  Insert into Bills table
            q1 = """INSERT INTO bills (bill_no, bill_date, dr_name, pt_name, mobile, address, diagnosis,
                                       total_items, total_qty, sub_total,dis_per,dis_amt, cgst, sgst,igst, grand_total,add_amt,round_off,net_total,
                                       pay_mode)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s , %s, %s, %s, %s, %s, %s)"""
            v1 = (bill_no, b_date, dr, pt, mob, addr, diag, tot_items, tot_qty, sub_tot,dis_per, dis_amt, cgst_val, sgst_val,igst_val, grand,
                  add_amt, round_off, net_tot,pay)
            cursor.execute(q1, v1)

            #  Insert Items into BILL_ITEMS table
            for child in tv2.get_children():
                val = tv2.item(child)["values"]

                q2 = """INSERT INTO bill_items (bill_no, item_name, rate, quantity, amount,dis_per,dis_amt, total, tax_per)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                v2 = (bill_no, val[0], val[1], val[2], val[3],val[4],val[5], val[6], val[7])
                cursor.execute(q2, v2)

            conn.commit()
            messagebox.showinfo("Success", "Bill Saved Successfully")

            # Clear Everything
            refresh()

            # Generate next bill no
            next_bill_no()

        except Exception as e:
            messagebox.showerror("Error", f"Saving Failed: {e}")
            conn.rollback()
        finally:
            conn.close()

def refresh():
    # Clear Treeview
    for item in tv2.get_children():
        tv2.delete(item)

    # Clear Patient Info
    e_dr.delete(0, END)
    e_pt.delete(0, END)
    e_mob.delete(0, END)
    e_addr.delete(0, END)
    e_diag.delete(0, END)

    # Clear Items
    e_name.delete(0, END)
    e_qty.delete(0, END)
    e_rate.delete(0, END)
    e_amt.delete(0, END)

    # Clear Totals
    update_entry(e_total_items, "")
    update_entry(e_total_qty, "")
    update_entry(e_sub_total, "")
    update_entry(e_grand_total, "")
    update_entry(e_net_total, "")
    update_entry(e_round_off, "")
    update_entry(e_cgst, "")
    update_entry(e_sgst, "")
    update_entry(e_igst, "")
    update_entry(e_dis_per, "")
    update_entry(e_dis_amt, "")
    update_entry(e_add_amt, "")
    update_entry(e_pay_mode, "")

    conn = db_conn()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(bill_no) FROM bills")
            row = cursor.fetchone()
            # row[0] is bill no
            last_bill_no = row[0]

            if last_bill_no is None:
                next_no = 1    # if empty this will stats with 1
            else:
                next_no = int(last_bill_no) + 1

            update_entry(e_bill_no, str(next_no))

        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch next bill number: {e}")
        finally:
            conn.close()

def Delete():

    current_bill_no = e_bill_no.get()
    if not current_bill_no:
        messagebox.showerror("Error", "No Bill Number Selected")
        return

    conn = db_conn()
    if conn:
        try:
            cursor = conn.cursor()

            #  Delete from bill_items table
            q1 = "delete from bill_items where bill_no = %s"
            cursor.execute(q1,(current_bill_no,))

            #  Delete from Bills table
            q2 = "delete from bills where bill_no = %s"
            cursor.execute(q2,(current_bill_no,))

            conn.commit()
            messagebox.showinfo("Success", "Bill Deleted Successfully")

            # Clear Everything
            refresh()

            # Generate next bill no
            next_bill_no()

        except Exception as e:
            messagebox.showerror("Error", f"Deleting Failed: {e}")
            conn.rollback()
        finally:
            conn.close()





# Upper View
Label(top, text='Retail Bill:', fg="Purple", font='Helvetica 32 bold', bg="light blue").place(x=5, y=15)

# Bill no
Label(top, text='Bill no', fg='Black', bg='light blue', font='Helvetica 14 bold').place(x=10, y=120)
e_bill_no = Entry(top, font='Calibri 15 bold',relief="ridge", borderwidth=2)
e_bill_no.place(x=110, y=120, width=100)

# Date
Label(top, text='Date', fg='Black', bg='light blue', font='Helvetica 14 bold').place(x=300, y=120)
cal = DateEntry(top, width=20, bg="darkblue", fg="white", year=2026, font='Calibri 15 bold')
cal.place(x=365, y=120, width=250)

# Medicine Name
Label(top, text='Name', fg='Black', bg='light blue', font='Helvetica 14 bold').place(x=10, y=190)
e_name = Entry(top, font='Calibri 15 bold', relief="ridge", borderwidth=2)
e_name.place(x=110, y=190, width=510)
e_name.bind('<Return>', get_product_details)

# Quantity
Label(top, text='Quantity', fg='Black', bg='light blue', font='Helvetica 14 bold').place(x=10, y=230)
e_qty = Entry(top, font='Calibri 15 bold',relief="ridge", borderwidth=2)
e_qty.place(x=110, y=230, width=100)
e_qty.bind('<Return>', add_to_list)

# Rate
Label(top, text='Rate', fg='Black', bg='light blue', font='Helvetica 14 bold').place(x=230, y=230)
e_rate = Entry(top, font='Calibri 15 bold',relief="ridge", borderwidth=2)
e_rate.place(x=280, y=230, width=115)

# Amount
Label(top, text='Amount', fg='Black', bg='light blue', font='Helvetica 14 bold').place(x=415, y=230)
e_amt = Entry(top, font='Calibri 15 bold',relief="ridge", borderwidth=2)
e_amt.place(x=500, y=230, width=120)

k1 = cal.get()  # DateEntry returns a string
# Date Format Handling
try:
    date_obj = datetime.datetime.strptime(k1, '%m/%d/%y') # Tries to match the format coming from the calendar
    n = date_obj.strftime('%Y-%m-%d')
except ValueError:
    n = k1 # If format differs, just use the raw string

# Treeview
tv = ttk.Treeview(top, height=15)
tv.column('#0', width=0, stretch=NO)

Label(top, text='Dr. Name', fg='Black', bg='white', font='Helvetica 13 bold').place(x=860, y=90)
e_dr = Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_dr.place(x=960, y=90, width=250)

Label(top, text='Pt. Name', fg='Black', bg='white', font='Helvetica 13 bold').place(x=860, y=125)
e_pt = Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_pt.place(x=960, y=125, width=250)

Label(top, text='Mobile', fg='Black', bg='white', font='Helvetica 13 bold').place(x=860, y=160)
e_mob = Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_mob.place(x=960, y=160, width=250)

Label(top, text='Address', fg='Black', bg='white', font='Helvetica 13 bold').place(x=860, y=200)
e_addr = Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_addr.place(x=960, y=200, width=250)

Label(top, text='Diagnosis', fg='Black', bg='white', font='Helvetica 13 bold').place(x=860, y=240)
e_diag = Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_diag.place(x=960, y=240, width=250)
tv.place(x=850, y=80, width=400, height=200)

# style
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview.Heading",background="Pale green",foreground="black",font=('Helvetica', 10, 'bold'))
style.configure("Green.TCombobox", fieldbackground="Light Yellow",background="white")

# Mid-View
tv2 = ttk.Treeview(top, height=10)
tv2['columns'] = ('Name', 'Rate', 'Quantity', 'Amount', 'Dis%', 'Dis Amt', 'Total', 'Tax%')
tv2.column('#0', width=0, stretch=NO)

tv2.column('Name', anchor="w", width=300)
tv2.column('Rate', anchor="w", width=100)
tv2.column('Quantity', anchor="w", width=100)
tv2.column('Amount', anchor="w", width=150)
tv2.column('Dis%', anchor="w", width=100)
tv2.column('Dis Amt', anchor="w", width=150)
tv2.column('Total', anchor="w", width=150)
tv2.column('Tax%', anchor="w", width=100)

tv2.heading('Name', text='Name', anchor="w")
tv2.heading('Rate', text='Rate', anchor="w")
tv2.heading('Quantity', text='Quantity', anchor="w")
tv2.heading('Amount', text='Amount', anchor="w")
tv2.heading('Dis%', text='Dis%', anchor="w")
tv2.heading('Dis Amt', text='Dis Amt', anchor="w")
tv2.heading('Total', text='Total', anchor="w")
tv2.heading('Tax%', text='Tax%', anchor="w")

# Create the scrollbar
hbar = ttk.Style() # Re-using style is fine, but we need the widget:
hbar = ttk.Scrollbar(top, orient="horizontal", command=tv2.xview)
# Link Treeview to Scrollbar
tv2.configure(xscrollcommand=hbar.set)
tv2.place(x=10, y=300, width=1240, height=250)
hbar.place(x=10, y=550, width=1240)

# Bottom-View
Label(top, text='Total Items', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=10, y=600)
e_total_items= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_total_items.place(x=120, y=600, width=100)

Label(top, text='Total QTY', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=250, y=600)
e_total_qty= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_total_qty.place(x=350, y=600, width=100)

Label(top, text='Sub Total', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=500, y=600)
e_sub_total= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_sub_total.place(x=600, y=600, width=100)

Label(top, text='Discount%', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=750, y=600)
e_dis_per= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_dis_per.place(x=850, y=600, width=100)

Label(top, text='Discount Amount', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=990, y=600)
e_dis_amt= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_dis_amt.place(x=1150, y=600, width=100)

Label(top, text='CGST', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=10, y=650)
e_cgst= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_cgst.place(x=120, y=650, width=100)

Label(top, text='SGST', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=250, y=650)
e_sgst= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_sgst.place(x=350, y=650, width=100)

Label(top, text='IGST', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=500, y=650)
e_igst= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_igst.place(x=600, y=650, width=100)

Label(top, text='Grand Total', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=750, y=650)
e_grand_total= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_grand_total.place(x=850, y=650, width=400)

Label(top, text='Add Amt', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=10, y=700)
e_add_amt= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_add_amt.place(x=120, y=700, width=100)

Label(top, text='Round Off', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=250, y=700)
e_round_off= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_round_off.place(x=350, y=700, width=100)

Label(top, text='Net Total', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=500, y=700)
e_net_total= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_net_total.place(x=600, y=700, width=100)

Label(top, text='Pay Mode', fg='Black', bg='light blue', font='Helvetica 13 bold').place(x=750, y=700)
e_pay_mode= Entry(top, font='Calibri 13 bold',relief="ridge", borderwidth=2)
e_pay_mode.place(x=850, y=700, width=400)
e_pay_mode = ttk.Combobox(top, values=['Cash', 'Card', 'UPI'], font='Calibri 13 bold',style="Green.TCombobox")
e_pay_mode.place(x=850, y=700, width=400)
e_pay_mode.current(0)

# Buttons

Button(top, text='Save 🗃️', font='Arial 16 bold', fg='Black', bg='Pale green', command=save_bill).place(x=20, y=760)

Button(top, text=' Delete Bill 🗑️', font='Arial 16 bold', fg='Black', bg='Pale green',command=Delete).place(x=190, y=760)

Button(top, text='Last Bill ⬅️', font='Arial 16 bold', fg='Black', bg='Pale green', command=load_last_bill).place(x=390, y=760)

Button(top, text='Next Bill ➡️', font='Arial 16 bold', fg='Black', bg='Pale green', command=load_next_bill).place(x=565, y=760)

Button(top, text='Last 50 Bill 🔍', font='Arial 16 bold', fg='Black', bg='Pale green', command=show_last_50_bills).place(x=750, y=760)

Button(top, text='Refresh 🔄', font='Arial 16 bold', fg='Black', bg='Pale green', command=refresh).place(x=950, y=760)

Button(top, text='End ❌', font='Arial 16 bold', fg='Black', bg='Pale green', command=top.destroy).place(x=1120, y=760)

# Initialize Bill Number at Start
next_bill_no()

top.mainloop()

