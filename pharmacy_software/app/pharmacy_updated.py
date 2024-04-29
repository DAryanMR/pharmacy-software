import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
from datetime import datetime
from num2words import num2words
import subprocess
import win32print
from PIL import ImageGrab
from PIL import Image, ImageTk
import os
import time


# *****************************************************#                    # *****************************************************#
# ********** Auth & Controls **************************#                    # ********** Auth & Controls **************************#
# *****************************************************#                    # *****************************************************#


# Define globally accessibles
global find_window, find_entry, isset_category_info

# Make connection to database
conn = sqlite3.connect('database/pharmacy.db')
# conn = sqlite3.connect('pharmacy.db')


# # Provide the UNC path to the shared folder location
# database_path = r'\\DESKTOP-R8CPIML\shared\pharmacy.db'


# # Connect to the SQLite database
# conn = sqlite3.connect(database_path)

cursor = conn.cursor()

# Basic controls


def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def focus_previous_widget(event):
    event.widget.tk_focusPrev().focus()
    return "break"


def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return "break"


def click_selected_widget(event):
    event.widget.invoke()
    return "break"


def destroy(window):
    window.destroy()


def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File '{file_path}' successfully deleted.")
    except OSError as e:
        print(f"Error deleting file '{file_path}': {e}")


def select_previous_value(table_container, find_entry):
    selected_item = table_container.focus()
    previous_item = table_container.prev(selected_item)
    if previous_item:
        table_container.selection_set(previous_item)
        table_container.focus(previous_item)
        table_container.see(previous_item)

        return "break"  # To prevent further event propagation
    else:
        find_entry.focus_force()


def select_next_value(table_container):
    selected_item = table_container.focus()
    next_item = table_container.next(selected_item)
    if next_item:
        table_container.selection_set(next_item)
        table_container.focus(next_item)
        table_container.see(next_item)

        return "break"  # To prevent further event propagation


# Auth
def login():
    username = username_entry.get()
    password = password_entry.get()

    cursor.execute(
        "SELECT * FROM Users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()

    if user:
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        login_label.config(text=f"Hi, {user[1]}", fg="green")
        date = datetime.now().strftime("%d-%m-%Y")
        login_time = datetime.now().strftime("%H:%M:%S")

        # Insert monitoring info only for employees
        if not user[3] == 'md':
            cursor.execute(
                "INSERT INTO Monitors ( date, u_id,login_time) VALUES (?,?,?)", (date, user[0], login_time))
            conn.commit()

        # Open the main application window
        open_main_app(user)
    else:
        password_entry.delete(0, tk.END)
        login_label.config(text="Invalid username or password!", fg="red")


def update_user_info():
    # Create a new popup window
    popup = tk.Toplevel()
    popup.title("Update User Info")

    # Calculate the position to open the popup window in the middle of the screen
    popup_width = 400  # Set the width of the popup window
    popup_height = 200  # Set the height of the popup window
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    position_x = int((screen_width - popup_width) / 2)
    position_y = int((screen_height - popup_height) / 2)
    popup.geometry(f"{popup_width}x{popup_height}+{position_x}+{position_y}")

    # Create labels
    username_label = tk.Label(popup, text="Username:")
    username_label.grid(row=0, column=0, padx=10, pady=5)

    current_password_label = tk.Label(popup, text="Current Password:")
    current_password_label.grid(row=1, column=0, padx=10, pady=5)

    new_password_label = tk.Label(popup, text="New Password:")
    new_password_label.grid(row=2, column=0, padx=10, pady=5)

    # Create entry fields
    username_entry = tk.Entry(popup)
    username_entry.grid(row=0, column=1, padx=10, pady=5)

    current_password_entry = tk.Entry(popup, show="*")
    current_password_entry.grid(row=1, column=1, padx=10, pady=5)

    new_password_entry = tk.Entry(popup, show="*")
    new_password_entry.grid(row=2, column=1, padx=10, pady=5)

    # Define the update function
    def perform_update():
        username = username_entry.get()
        current_password = current_password_entry.get()
        new_password = new_password_entry.get()

        # Perform the update logic
        cursor.execute(
            "SELECT * FROM Users WHERE username LIKE ?", (username,))
        user = cursor.fetchone()

        if user is None:
            messagebox.showerror("Error", "User not found!")
            return

        # Assuming password is stored in the second column of the table
        stored_password = user[2]

        if current_password != stored_password:
            messagebox.showerror("Error", "Incorrect current password!")
            return

        # Update the username and password
        cursor.execute("UPDATE Users SET username=?, password=? WHERE username LIKE ?",
                       (username, new_password, username))
        conn.commit()

        messagebox.showinfo("Success", "User info updated successfully!")

        # Close the popup window after successful update
        popup.destroy()

    # Create the update button
    update_button = tk.Button(popup, text="Update", command=perform_update)
    update_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

    popup.focus_force()
    username_entry.focus()

    popup.bind("<Down>", focus_next_widget)
    username_entry.bind("<Return>", focus_next_widget)
    current_password_entry.bind("<Return>", focus_next_widget)
    new_password_entry.bind("<Return>", focus_next_widget)
    popup.bind("<Up>", focus_previous_widget)
    update_button.bind("<Return>", lambda event: perform_update())


# *****************************************************#                    # *****************************************************#
# ********** Auth & Controls End **********************#                    # ********** Auth & Controls End **********************#
# *****************************************************#                    # *****************************************************#

# *****************************************************#                    # *****************************************************#
# ********** Pharmacy Application *********************#                    # ********** Pharmacy Application *********************#
# *****************************************************#                    # *****************************************************#


def open_main_app(user):
    def kill_main_app():
        if main_app:
            main_app.destroy()

    def logout():
        date = datetime.now().strftime("%d-%m-%Y")
        logout_time = datetime.now().strftime("%H:%M:%S")
        if not user[3] == 'md':
            cursor.execute(
                '''UPDATE Monitors SET logout_time = ? 
                WHERE date = ? AND u_id = ? AND logout_time IS NULL''',
                (logout_time, date, user[0])
            )

            conn.commit()
        global username_entry, password_entry, login_label, window
        # if main_app:
        #     main_app.destroy()

        kill_main_app()

        # Create the login window
        window = tk.Tk()
        window.title("Login Form")

        # Create a canvas as the background with the desired color
        canvas = tk.Canvas(window, bg="#145DA0")
        canvas.pack(fill="both", expand=True)

        # Get the screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Set the window size to fill the screen
        window.geometry(f"{screen_width}x{screen_height}")

        # Load the logo image
        logo_image = Image.open("images/logo.jpg")
        # Resize the image to be slightly smaller
        new_width = int(logo_image.width * 0.6)
        new_height = int(logo_image.height * 0.6)
        logo_image = logo_image.resize(
            (new_width, new_height), resample=Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)

        # Create a Label widget for the logo background
        logo_label = tk.Label(canvas, image=logo_photo, bg="#145DA0")
        logo_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Create the header label
        header_label = tk.Label(canvas, text="AL-Amin Pharmacy Login",
                                font=("Arial", 24, "bold"), bg="#145DA0", fg="white")
        header_label.pack(pady=(10, 20))

        # Center the window on the screen
        window.update_idletasks()
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        position_right = int(window.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(window.winfo_screenheight() /
                            2 - window_height / 2)
        window.geometry("+{}+{}".format(position_right, position_down))

        # Create a frame as a container
        # Set the background color of the container
        container = tk.Frame(canvas, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=100, pady=100)

        # Create a canvas with a transparent background
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Set the container frame as the parent of the canvas
        container.update()

        # Get the dimensions of the canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Calculate the position to place the image slightly below the center
        image_x = (canvas_width - logo_image.width) // 2
        image_y = (canvas_height - logo_image.height) // 2
        # Adjust the position down by 5% of the canvas height
        image_x += int(canvas_height * 0.015)
        # Adjust the position down by 5% of the canvas height
        image_y += int(canvas_height * 0.10)

        # Place the logo image on the canvas
        canvas.create_image(image_x, image_y, anchor="nw", image=logo_photo)

        # Create the username label and input field
        username_label = tk.Label(
            canvas, text="Username:", bg="white", font=16)
        username_label.pack()

        username_entry = tk.Entry(canvas, bg="white", width=30, font=16)
        username_entry.pack()
        username_entry.focus_force()

        # Create the password label and input field
        password_label = tk.Label(
            canvas, text="Password:", bg="white", font=16)
        password_label.pack()

        password_entry = tk.Entry(
            canvas, show="*", bg="white", width=30, font=16)
        password_entry.pack(pady=10)

        login_btn_container = tk.Frame(canvas, bg="white")
        login_btn_container.pack()

        # Create the login button
        login_button = tk.Button(login_btn_container, text="Login",
                                 command=login, font=10, bg="#18A558", fg='white')
        # login_button.pack()
        login_button.grid(row=0, column=0, padx=3)

        # Create the login button
        update_button = tk.Button(login_btn_container, text="Update Info",
                                  command=update_user_info, font=10, bg='#75E6DA')
        # update_button.pack()
        update_button.grid(row=0, column=1)

        # Create the login status label
        login_label = tk.Label(canvas, text="", fg="red", bg="white")
        login_label.pack(pady=10)

        # Bind arrow keys to move between input fields
        window.bind("<Down>", focus_next_widget)
        window.bind("<Up>", focus_previous_widget)
        username_entry.bind("<Down>", focus_next_widget)
        password_entry.bind("<Down>", focus_next_widget)
        password_entry.bind("<Up>", focus_previous_widget)
        login_button.bind("<Up>", focus_previous_widget)

        # Bind Enter key to click the currently selected input field or button
        username_entry.bind("<Return>", focus_next_widget)
        password_entry.bind("<Return>", lambda event: login())
        login_button.bind("<Return>", click_selected_widget)

        window.configure(bg="#145DA0")

        # Run the Tkinter event loop for the login window
        window.mainloop()

    def make_table_frame():
        # Define Basic Table Layout

        # Calculate the desired height for 15 visible rows
        row_height = 35  # Adjust this value based on your row height
        visible_rows = 8
        desired_height = (visible_rows + 1) * \
            row_height  # Add 1 for the header row

        # Create a new container for the table
        table_container = tk.Frame(body_container, bg="white")
        table_container.place(relx=0.5, rely=0.6,
                              anchor="center", relwidth=0.95)

        # Create a scrollable frame for the table
        canvas = tk.Canvas(table_container)
        canvas.pack(side="left", fill="both", expand=True)

        # Add a scrollbar for the frame
        scrollbar = ttk.Scrollbar(
            table_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the canvas to use the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame inside the canvas for the table content
        table_frame = tk.Frame(canvas, bg="white")
        table_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        # Create a window inside the canvas to hold the table frame
        canvas.create_window((0, 0), window=table_frame, anchor="nw")

        # Configure the scrollbar to scroll the canvas
        def scroll_canvas(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        table_frame.bind_all("<MouseWheel>", scroll_canvas)

        # Configure the height of the table container and the canvas
        table_container.config(height=desired_height)
        canvas.config(height=desired_height)
        global scroll_down

        def scroll_down():
            # Update the canvas view to include the new rows
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            canvas.config(scrollregion=bbox)
            # Move the scrollbar to the bottom
            canvas.yview_moveto(1.0)

        return table_frame

    def click_first_item(table_container, find_window):
        table_container.focus_force()
        first_item = table_container.get_children()[0]
        if first_item:
            table_container.selection_set(first_item)
            table_container.focus(first_item)
            table_container.see(first_item)

    def select_next_supplier(table_container):
        selected_item = table_container.focus()
        next_item = table_container.next(selected_item)
        if next_item:
            table_container.selection_set(next_item)
            table_container.focus(next_item)
            table_container.see(next_item)

            return "break"  # To prevent further event propagation

    def select_previous_supplier(table_container, find_entry):
        selected_item = table_container.focus()
        previous_item = table_container.prev(selected_item)
        if previous_item:
            table_container.selection_set(previous_item)
            table_container.focus(previous_item)
            table_container.see(previous_item)

            return "break"  # To prevent further event propagation
        else:
            find_entry.focus_force()

    def insert_results_into_table(table_container, results):
        # Clear previous data
        table_container.delete(*table_container.get_children())

        # Insert rows into the table container
        for row in results:
            table_container.insert("", "end", values=row)

    def open_glob_sup_window(event, supplier_name_entry):

        def update_results(table_container, find_entry):
            # Get the new supplier name
            new_supplier = find_entry.get()

            # Generate new results
            cursor.execute(
                "SELECT * FROM Suppliers WHERE supplier_name LIKE ?", ('%' + new_supplier + '%',))
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)

        def select_supplier_from_table(table_container, find_window):
            selected_item = table_container.focus()
            if selected_item:
                supplier = table_container.item(selected_item)["values"][1]
                supplier_id = table_container.item(selected_item)["values"][0]
                select_supplier(supplier_id, supplier, find_window)

        def select_supplier(supplier_id, supplier, find_window):

            # Destroy find window
            find_window.destroy()

            # # Add supplier id to supplier_id_label
            supplier_id_label_add_win.configure(text=supplier_id)

            # Clear the supplier entry field
            supplier_name_entry.delete(0, tk.END)

            # Insert user's query to supplier entry field
            supplier_name_entry.insert(0, supplier)

        # Create a new window
        find_window = tk.Toplevel(main_app)
        find_window.title("Find")

        # Create the "Find" label
        find_label = tk.Label(
            find_window, text="Find:", font=("Arial", 10))
        find_label.grid(row=0, column=0, padx=10, pady=10)

        # Create the entry field
        find_entry = tk.Entry(find_window, font=("Arial", 10))
        find_entry.grid(row=0, column=1, padx=10, pady=10)

        # Give the main_app window focus
        find_window.focus_force()

        # Take the user's entry
        supplier = supplier_name_entry.get()

        # Set the value of find_entry to the supplier name
        find_entry.insert(0, supplier)

        # Create the table container
        table_container = ttk.Treeview(find_window)
        table_container.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10)

        # Define the column names
        column_names = ["Supplier ID", "Supplier Name"]

        # Configure the table container
        table_container["columns"] = column_names
        table_container["show"] = "headings"

        # Set the column properties
        for column in column_names:
            table_container.heading(column, text=column)
            table_container.column(column, width=100)

        # Generate initial results
        cursor.execute(
            "SELECT * FROM Suppliers WHERE supplier_name LIKE ?", ('%' + supplier + '%',))
        results = cursor.fetchall()

        # Insert the results into the table container
        insert_results_into_table(table_container, results)

        # Update results upon further querying
        find_entry.bind('<KeyRelease>', lambda event: update_results(
            table_container, find_entry))

        # Bind arrow keys and Enter key
        table_container.bind(
            '<Up>', lambda event: select_previous_supplier(table_container, find_entry))
        table_container.bind(
            '<Down>', lambda event: select_next_supplier(table_container))
        table_container.bind('<Return>', lambda event: select_supplier_from_table(
            table_container, find_window))

        # Bind Enter key on find_entry to click on the first item
        find_entry.bind(
            '<Down>', lambda event: click_first_item(table_container, find_window))

        # Destroy window
        find_window.bind('<Escape>', lambda event: destroy(find_window))

        find_entry.focus_force()

    def open_glob_cat_window(event, category_entry):

        def update_category_results(table_container, find_entry, category_entry, find_window):
            # Get the new supplier name
            new_category = find_entry.get()

            # Generate new results
            cursor.execute(
                "SELECT * FROM Categories WHERE category_name LIKE ?", ('%' + new_category + '%',))
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))

        def select_category_from_table(table_container, find_window, category_entry):
            selected_item = table_container.focus()
            if selected_item:
                category = table_container.item(selected_item)["values"][1]
                category_id = table_container.item(selected_item)["values"][0]

                select_category(category, category_id,
                                category_entry, find_window)

        def select_category(category, category_id, category_entry, find_window):

            # Destroy find window
            if find_window:
                find_window.destroy()

            category_entry.delete(0, tk.END)
            category_entry.insert(0, category)
            category_id_label_add_win.configure(text=category_id)

        category = category_entry.get()

        # Create a new window
        find_window = tk.Toplevel(main_app)
        find_window.title("Find")

        # Create the "Find" label
        find_label = tk.Label(
            find_window, text="Find:", font=("Arial", 10))
        find_label.grid(row=0, column=0, padx=10, pady=10)

        # Create the entry field
        find_entry = tk.Entry(find_window, font=("Arial", 10))
        find_entry.grid(row=0, column=1, padx=10, pady=10)

        # Give the main_app window focus
        find_window.focus_force()

        # Set the value of find_entry to the supplier name
        find_entry.insert(0, category)

        # Create the table container
        table_container = ttk.Treeview(find_window)
        table_container.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10)

        # Define the column names
        column_names = ["Category ID", "Category Name"]

        # Configure the table container
        table_container["columns"] = column_names
        table_container["show"] = "headings"

        # Set the column properties
        for column in column_names:
            table_container.heading(column, text=column)
            table_container.column(column, width=100)

        # Generate initial results
        cursor.execute(
            "SELECT * FROM Categories WHERE category_name LIKE ?", ('%' + category + '%',))
        results = cursor.fetchall()

        # Insert the results into the table container
        insert_results_into_table(table_container, results)

        # Update results upon further querying
        find_entry.bind('<KeyRelease>', lambda event: update_category_results(
            table_container, find_entry, category_entry, find_window))

        # Bind arrow keys and Enter key
        table_container.bind(
            '<Up>', lambda event: select_previous_supplier(table_container, find_entry))
        table_container.bind(
            '<Down>', lambda event: select_next_supplier(table_container))
        table_container.bind('<Return>', lambda event: select_category_from_table(
            table_container, find_window, category_entry))
        # Bind Enter key on find_entry to click on the first item
        find_entry.bind(
            '<Down>', lambda event: click_first_item(table_container, find_window))

        find_entry.focus_force()

    def calculate_dynamic_total(table_container, total_amt_label):
        # Calculate total amount
        total_purchase_amt = 0
        current_last_row = table_container.grid_size()[1] - 1
        # Iterate through each row in the table container
        for row in range(1, current_last_row+1):
            # Clear the text in the columns of the current row
            for col in range(8):  # Assuming there are 5 columns
                if col == 7:

                    widget = table_container.grid_slaves(
                        row=row, column=col-2)[0]
                    current_amt = widget.get()
                    print("tpa", current_amt)
                    if current_amt:
                        total_purchase_amt += float(current_amt)
                    else:
                        current_amt = 0

        total_amt_label.configure(text=total_purchase_amt)

    # *****************************************************#                    # *****************************************************#
    # ********** Info Page ********************************#                    # ********** Info Page ********************************#
    # *****************************************************#                    # *****************************************************#

    def open_info_page():
        # Implement the code to open the "Medicine Purchase" page here

        def search_categories(event):
            search_query = category_input_field.get()

            # Execute the database query
            cursor.execute(
                "SELECT id, category_name FROM Categories WHERE category_name LIKE ?", ('%' + search_query + '%',))
            results = cursor.fetchall()

            # Clear the current dropdowns
            category_input_field['values'] = []

            # Generate dropdowns for each suggestion
            suggestion_values = []
            category_ids = []
            for category in results:
                category_id = category[0]  # Assuming category_id is at index 0
                # Assuming category_name is at index 1
                category_name = category[1]
                suggestion_values.append(category_name)
                category_ids.append(category_id)

            category_input_field['values'] = suggestion_values

            return category_ids, suggestion_values

        def select_category(event):
            isset_category_info = False
            selected_index = category_input_field.current()
            category_ids, suggestion_values = search_categories(event)

            if selected_index >= 0 and selected_index < len(category_ids):
                isset_category_info = True
                category_id = category_ids[selected_index]
                category_name = suggestion_values[selected_index]
                # Handle the selected category using category_id and category_name
                if isset_category_info:
                    print("Selected category_id:", category_id)
                    print("Selected category_name:", category_name)

                return category_id, isset_category_info

            # Return default values when no category is selected
            return None, False

        def update_category(event):
            search_results = search_categories(event)
            print(search_results)

        def search_items(event):
            category_id, isset_category_info = select_category(event)
            search_query = item_input_field.get()
            # Execute the database query
            cursor.execute(
                "SELECT * FROM Items WHERE category_id = ? AND item_name LIKE ?", (category_id, '%' + search_query + '%'))
            results = cursor.fetchall()

            # Clear the current dropdowns
            item_input_field['values'] = []

            # Generate dropdowns for each suggestion
            suggestion_values = []
            item_ids = []
            for item in results:
                item_id = item[0]  # Assuming item_id is at index 0
                # Assuming item_name is at index 3
                item_name = item[3]
                suggestion_values.append(item_name)
                item_ids.append(item_id)

            item_input_field['values'] = suggestion_values

            return item_ids, suggestion_values

        def select_item(event):
            selected_index = item_input_field.current()
            item_ids, suggestion_values = search_items(event)

            if selected_index >= 0 and selected_index < len(item_ids):
                item_id = item_ids[selected_index]
                item_name = suggestion_values[selected_index]
                # Handle the selected item using item_id and item_name
                print("Selected item_id:", item_id)
                print("Selected item_name:", item_name)

                return item_id

        def update_item(event):
            search_results = search_items(event)
            print(search_results)

        def delete_item(item_id):
            item_name_q = "SELECT item_name FROM items WHERE id = ?"
            cursor.execute(item_name_q, (item_id,))
            item_name = cursor.fetchone()

            # Create a confirmation dialog
            confirmed = messagebox.askokcancel(
                "Confirmation", f"Are you sure you want to delete the item {item_name} ?")

            if confirmed:
                # Execute the DELETE query
                delete_query = "DELETE FROM items WHERE id = ?"
                cursor.execute(delete_query, (item_id,))

                # Commit the changes and close the connection
                conn.commit()
                messagebox.showinfo("Success", "Item deleted successfully.")
            else:
                messagebox.showinfo("Cancellation", "Deletion cancelled.")

            # Reload page
            open_info_page()

        def delete_focused_row(event):
            focused_widget = event.widget
            if isinstance(focused_widget, tk.Entry):
                row_index = int(focused_widget.grid_info()['row'])

                item_id_entry = table_frame.grid_slaves(
                    row=row_index, column=1)[0]
                item_id = int(item_id_entry.get())

                print("Deketeee", item_id)
                delete_item(item_id)

        def generate_medicine_info(rows):
            # Create the column names
            column_names = ["Category", "Item ID", "Item Name",
                            "Brand", "Unit", "Buy Rate", "Sale Rate", "Min-Stock", "Action"]
            num_columns = len(column_names)

            # Adjust the percentage as needed
            table_width = round(window_width * 0.69 * 0.1)
            column_width = round(table_width / num_columns)
            print(column_width)

            for i, name in enumerate(column_names):
                label = tk.Label(table_frame, text=name, font=(
                    "Arial", 10, "bold"), bg="white", padx=10, pady=5, relief="solid", width=column_width)
                label.grid(row=0, column=i, sticky="nsew")

            # Create rows in the table
            for row_index, row_data in enumerate(rows):
                row_data = list(row_data)
                row_data.insert(4, "PCS")
                row_data.insert(7, 0)
                item_id = row_data[1]
                for col_index, value in enumerate(row_data):
                    # print("COL INDEX SALE INFO:::", col_index)
                    if col_index == 2 or col_index == 5 or col_index == 6:  # Column index for "Buy Rate" and "Sale Rate"
                        entry = tk.Entry(table_frame, font=(
                            "Arial", 10), bg="white", relief="solid")
                        entry.insert(0, value)
                        entry.grid(row=row_index + 1,
                                   column=col_index, sticky="nsew")

                        # Bind the <Return> key event to update the value in the database
                        entry.bind('<Return>', lambda event, item_id=item_id, col_index=col_index,
                                   entry=entry: update_value(event, item_id, col_index, entry))

                    else:
                        entry = tk.Entry(table_frame, font=(
                            "Arial", 10), bg="white", relief="solid")
                        entry.insert(0, value)
                        entry.grid(row=row_index + 1,
                                   column=col_index, sticky="nsew")

                    if col_index == 7:  # Delete button
                        delete_item_button = tk.Button(
                            table_frame, text="Delete Item", width=button_width, font=("Arial", 8))
                        delete_item_button.grid(
                            row=row_index + 1, column=col_index+1, padx=10)

                delete_item_button.bind(
                    '<Button-1>', lambda event, item_id=item_id: delete_item(item_id))
                delete_item_button.bind(
                    "<Return>", lambda event, item_id=item_id: delete_item(item_id))

                table_frame.bind_all('<Control-d>', delete_focused_row)

        def update_value(event, item_id, col_index, entry):
            new_value = entry.get()  # Retrieve the updated value from the entry field

            # Perform the update query
            print(item_id)
            if col_index == 2:  # Item Particulars column
                update_query = "UPDATE Items SET item_name = ? WHERE id = ?"
            if col_index == 5:  # Buy Rate column
                update_query = "UPDATE Items SET buy_rate = ? WHERE id = ?"
            elif col_index == 6:  # Sale Rate column
                update_query = "UPDATE Items SET sell_rate = ? WHERE id = ?"

            # Execute the update query with the new value and item ID
            cursor.execute(update_query, (new_value, item_id))
            conn.commit()  # Commit the changes to the database

            # Reload
            open_info_page()

        def filter_results(event):
            category_id, _ = select_category(event)
            search_query = category_input_field.get()

            # Execute the filtered database query
            cursor.execute(
                '''
                SELECT Categories.category_name, Items.id, Items.item_name, Suppliers.supplier_name, Items.buy_rate, Items.sell_rate
                FROM Items
                INNER JOIN Categories ON Items.category_id = Categories.id
                INNER JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
                WHERE Categories.id = ? AND Categories.category_name LIKE ?
                ''',
                (category_id, '%' + search_query + '%')
            )
            results = cursor.fetchall()

            # Clear the current table content
            for widget in table_frame.winfo_children():
                widget.destroy()

            generate_medicine_info(results)

        def filter_item_results(event):
            # Clear the current table content
            for widget in table_frame.winfo_children():
                widget.destroy()
            search_query = item_input_field.get()
            item_id = select_item(event)
            category_id, isset_category_info = select_category(event)

            if isset_category_info:
                print("Category Set:")
                # Execute the filtered database query
                cursor.execute(
                    '''
                    SELECT Categories.category_name, Items.id, Items.item_name, Suppliers.supplier_name, Items.buy_rate, Items.sell_rate
                    FROM Items
                    INNER JOIN Categories ON Items.category_id = Categories.id
                    INNER JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
                    WHERE Items.category_id = ? AND Items.item_name LIKE ?
                    ''',
                    (category_id, '%' + search_query + '%',)
                )
            else:
                print("Category Not Set:")

                # Execute the filtered database query
                cursor.execute(
                    '''
                    SELECT Categories.category_name, Items.id, Items.item_name, Suppliers.supplier_name, Items.buy_rate, Items.sell_rate
                    FROM Items
                    INNER JOIN Categories ON Items.category_id = Categories.id
                    INNER JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
                    WHERE Items.item_name LIKE ?
                    ''',
                    ('%' + search_query + '%',)
                )
            results = cursor.fetchall()

            generate_medicine_info(results)

        def add_category():
            # Create a new window for adding a category
            category_window = tk.Toplevel()
            category_window.title("Add Category")

            # Set the window dimensions and position it in the center
            window_width = 300
            window_height = 150
            screen_width = category_window.winfo_screenwidth()
            screen_height = category_window.winfo_screenheight()
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            category_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Function to handle the submit button click event
            def submit_category():
                category_name = category_entry.get()

                # Check if the category name is empty
                if not category_name:
                    messagebox.showwarning(
                        "Error", "Please enter a category name.")
                    return

                # Perform the database insert query here
                cursor.execute(
                    "INSERT INTO categories (category_name) VALUES (?)", (category_name,))
                # Execute the insert query using your database library
                conn.commit()

                # Show a success message
                messagebox.showinfo("Success", "Category added successfully.")

                # Close the category window
                category_window.destroy()

            # Create the category entry field
            category_label = tk.Label(category_window, font=(
                "Arial", 12), text="Category Name:")
            category_label.pack(pady=10)
            category_entry = tk.Entry(category_window, font=("Arial", 12))
            category_entry.pack(pady=10)
            category_entry.focus()

            # Create the submit button
            submit_button = tk.Button(category_window, text="Submit", font=(
                "Arial", 12), command=submit_category)
            submit_button.pack()

            # Bind Enter key press to the submit_category function
            category_entry.bind("<Return>", lambda event: submit_category())

            # Run the main event loop for the category window
            category_window.mainloop()

        def add_supplier():
            # Create a new window for adding a supplier
            supplier_window = tk.Toplevel()
            supplier_window.title("Add supplier")

            # Set the window dimensions and position it in the center
            window_width = 300
            window_height = 150
            screen_width = supplier_window.winfo_screenwidth()
            screen_height = supplier_window.winfo_screenheight()
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            supplier_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Function to handle the submit button click event
            def submit_supplier(event):
                supplier_name = supplier_entry.get()

                # Check if the supplier name is empty
                if not supplier_name:
                    messagebox.showwarning(
                        "Error", "Please enter a supplier name.")
                    return

                # Perform the database insert query here
                cursor.execute(
                    "INSERT INTO Suppliers (supplier_name) VALUES (?)", (supplier_name,))
                # Execute the insert query using your database library
                conn.commit()

                # Show a success message
                messagebox.showinfo("Success", "supplier added successfully.")

                # Close the supplier window
                supplier_window.destroy()

            # Create the supplier entry field
            supplier_label = tk.Label(supplier_window, font=(
                "Arial", 12), text="Supplier Name:")
            supplier_label.pack(pady=10)
            supplier_entry = tk.Entry(supplier_window, font=("Arial", 12))
            supplier_entry.pack(pady=10)
            supplier_entry.focus()

            # Create the submit button
            submit_button = tk.Button(supplier_window, text="Submit", font=(
                "Arial", 12), command=submit_supplier)
            submit_button.pack()

            # Bind keys
            supplier_entry.bind('<Return>', submit_supplier)

            # Run the main event loop for the supplier window
            supplier_window.mainloop()

        def add_item():
            # Create a new window for adding an item
            item_window = tk.Toplevel()
            item_window.title("Add Item")

            # Set the window dimensions and position it in the center
            window_width = 400
            window_height = 300
            screen_width = item_window.winfo_screenwidth()
            screen_height = item_window.winfo_screenheight()
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            item_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Function to handle the submit button click event
            def submit_item():
                selected_category_id = category_id_label_add_win.cget("text")
                selected_category = category_var.get()
                selected_supplier_id = supplier_id_label_add_win.cget("text")
                selected_supplier = supplier_var.get()
                item_name = item_name_var.get()
                item_count = item_count_var.get()
                buy_rate = buy_rate_var.get()
                sell_rate = sell_rate_var.get()

                # Check if a category and supplier are selected
                if selected_category_id == "" or selected_supplier_id == "" or item_name == "" or item_count == "" or buy_rate == "" or sell_rate == "":
                    messagebox.showwarning(
                        "Error", "Please select a category and a supplier.")
                    return

                item_infos = [int(selected_supplier_id), int(selected_category_id), item_name, int(
                    item_count), float(buy_rate), float(sell_rate)]
                item_infos = [tuple(item_infos)]

                print("ITEM INFO!!!!", item_infos)

                # Establish a connection to the SQLite database
                # conn = sqlite3.connect("database/pharmacy.db")
                # conn = sqlite3.connect("pharmacy.db")
                cursor = conn.cursor()

                # Perform the database insert query here
                cursor.executemany(
                    '''
                    INSERT INTO Items (supplier_id, category_id, item_name, item_count, buy_rate, sell_rate) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    item_infos
                )
                conn.commit()

                # Show a success message
                messagebox.showinfo("Success", "Item added successfully.")

                # Close the item window
                item_window.destroy()

                # Reload page
                open_info_page()

            # Get the category and supplier values from the database

            # Create the supplier dropdown menu
            supplier_label = tk.Label(
                item_window, text="Supplier:", font=("Arial", 8))
            supplier_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

            supplier_var = tk.Entry(item_window, font=("Arial", 8))
            supplier_var.grid(row=0, column=1, pady=10, sticky="w")
            supplier_var.bind(
                '<Return>', lambda event: open_glob_sup_window(event, supplier_var))

            global supplier_id_label_add_win
            supplier_id_label_add_win = tk.Label(
                item_window, font=("Arial", 8), width=4)
            supplier_id_label_add_win.grid(row=0, column=2, pady=10)

            # Create the category dropdown menu
            category_label = tk.Label(
                item_window, text="Category:", font=("Arial", 8))
            category_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

            category_var = tk.Entry(item_window, font=("Arial", 8))
            category_var.grid(row=1, column=1, padx=10, pady=10, sticky="w")
            category_var.bind(
                '<Return>', lambda event: open_glob_cat_window(event, category_var))

            global category_id_label_add_win
            category_id_label_add_win = tk.Label(
                item_window, font=("Arial", 8), width=4)
            category_id_label_add_win.grid(row=1, column=2, pady=10)

            # Create the item name entry field
            item_name_label = tk.Label(
                item_window, text="Item Name:", font=("Arial", 8))
            item_name_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")
            item_name_var = tk.Entry(item_window, font=("Arial", 8))
            item_name_var.grid(row=2, column=1, pady=10, sticky="w")

            # Create the item count entry field
            item_count_label = tk.Label(
                item_window, text="Item Count:", font=("Arial", 8))
            item_count_label.grid(
                row=3, column=0, padx=10, pady=10, sticky="e")
            item_count_var = tk.Entry(item_window, font=("Arial", 8))
            item_count_var.grid(row=3, column=1, pady=10, sticky="w")

            # Create the buy rate entry field
            buy_rate_label = tk.Label(
                item_window, text="Buy Rate:", font=("Arial", 8))
            buy_rate_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")
            buy_rate_var = tk.Entry(item_window, font=("Arial", 8))
            buy_rate_var.grid(row=4, column=1, pady=10, sticky="w")

            # Create the sell rate entry field
            sell_rate_label = tk.Label(
                item_window, text="Sell Rate:", font=("Arial", 8))
            sell_rate_label.grid(row=5, column=0, padx=10, pady=10, sticky="e")
            sell_rate_var = tk.Entry(item_window, font=("Arial", 8))
            sell_rate_var.grid(row=5, column=1, pady=10, sticky="w")

            # Create the submit button
            submit_button = tk.Button(item_window, text="Submit", font=(
                "Arial", 8), command=submit_item)
            submit_button.grid(row=6, column=1, padx=10, pady=10, sticky="e")

            submit_button.bind("<Return>", lambda event: submit_item())

            item_window.bind("<Down>", focus_next_widget)
            item_window.bind("<Up>", focus_previous_widget)

            item_window.focus_force()
            supplier_var.focus()

            # Run the main event loop for the item window
            item_window.mainloop()

        def short_stock():
            # Create a new Tkinter window
            stock_window = tk.Tk()
            stock_window.title("Short Stock")

            # Center the window on the screen
            window_width = 800
            window_height = 400
            screen_width = stock_window.winfo_screenwidth()
            screen_height = stock_window.winfo_screenheight()
            x = int((screen_width / 2) - (window_width / 2))
            y = int((screen_height / 2) - (window_height / 2))
            stock_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Create an entry field for the count
            count_label = tk.Label(stock_window, text="Enter Count:")
            count_label.pack()

            count_entry = tk.Entry(stock_window)
            count_entry.pack()

            # Create a button to execute the SELECT query
            search_button = tk.Button(
                stock_window, text="Search", bg='#4169E1', fg='white', command=lambda: get_short_stocks(count_entry.get()))
            search_button.pack()

            # Create a Treeview widget
            treeview = ttk.Treeview(stock_window, columns=(
                "ID", "Item Name", "Item Count"))
            treeview.pack()

            # Configure the columns
            treeview.heading("ID", text="ID")
            treeview.heading("Item Name", text="Item Name")
            treeview.heading("Item Count", text="Item Count")

            # Store the Treeview as an attribute
            short_stock.treeview = treeview

            count_entry.bind(
                "<Return>", lambda event: get_short_stocks(count_entry.get()))

            stock_window.bind("<Down>", focus_next_widget)
            stock_window.bind("<Up>", focus_previous_widget)

            stock_window.bind('<Escape>', lambda event: destroy(find_window))

            stock_window.focus_force()
            # count_entry.focus()

        def get_short_stocks(count):
            # Execute the SELECT query
            select_query = "SELECT id, item_name, item_count FROM items WHERE item_count <= ?"
            cursor.execute(select_query, (count,))

            # Fetch the results
            results = cursor.fetchall()

            # Clear the existing items
            short_stock.treeview.delete(*short_stock.treeview.get_children())

            # Insert the results into the Treeview
            for result in results:
                short_stock.treeview.insert("", "end", values=result)

        # Clear previous elements
        clear_frame(body_container)

        # Create the header label
        header_label = tk.Label(body_container, text="Medicine Information",
                                font=("Arial", 24, "bold"), borderwidth=1, relief='solid', bg="#F5F5DC", fg="black")
        header_label.pack(pady=(10, 20))

        # Create the info container
        info_container = tk.Frame(body_container, bg="white")
        info_container.pack()

        # Create the "Category Name" label
        category_label = tk.Label(
            info_container, text="Category Name:", font=("Arial", 14), bg="white")
        category_label.grid(row=0, column=0, padx=10, pady=10)

        # Create the "Item Name" label
        item_label = tk.Label(
            info_container, text="Item Name:", font=("Arial", 14), bg="white")
        item_label.grid(row=1, column=0, padx=10, pady=10)

        # Create the input field as a Combobox
        category_input_field = ttk.Combobox(
            info_container, font=("Arial", 14), width=20)
        category_input_field.grid(row=0, column=1, padx=10)

        # Create the item input field as a Combobox
        item_input_field = ttk.Combobox(
            info_container, font=("Arial", 14), width=20)
        item_input_field.grid(row=1, column=1, padx=10)
        # Create the info container
        btn_container = tk.Frame(body_container, bg="white")
        btn_container.pack()

        # Create buttons to add categories,brands,items
        add_category_button = tk.Button(
            btn_container, text="Add Category", width=button_width, font=("Arial", 8), command=add_category)
        add_category_button.grid(row=2, column=0, padx=3, pady=5)

        add_supplier_button = tk.Button(
            btn_container, text="Add Supplier", width=button_width, font=("Arial", 8), command=add_supplier)
        add_supplier_button.grid(row=2, column=1, padx=4, pady=5)

        add_item_button = tk.Button(
            btn_container, text="Add Item", width=button_width, font=("Arial", 8), command=add_item)
        add_item_button.grid(row=2, column=2, padx=3, pady=5)

        stock_short_button = tk.Button(
            btn_container, text="Short Stock", width=button_width, font=("Arial", 8), command=short_stock)
        stock_short_button.grid(row=2, column=3, padx=3, pady=5)

        # Bind the <KeyRelease> event to the search_categories function
        category_input_field.bind("<KeyRelease>", search_categories)

        # Bind the <KeyRelease> event to the search_items function
        item_input_field.bind("<KeyRelease>", search_items)

        # Bind the <<ComboboxSelected>> event to the select_category function
        category_input_field.bind("<<ComboboxSelected>>", select_category)
        category_input_field.bind("<Down>", update_category)

        # Bind the <<ComboboxSelected>> event to the select_item function
        item_input_field.bind("<<ComboboxSelected>>", select_item)
        item_input_field.bind("<Down>", update_item)

        # Fetch the data from the joined tables
        cursor.execute('''
            SELECT Categories.category_name, Items.id, Items.item_name, Suppliers.supplier_name, Items.buy_rate, Items.sell_rate
            FROM Items
            INNER JOIN Categories ON Items.category_id = Categories.id
            INNER JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
            ORDER BY Categories.category_name
        ''')
        rows = cursor.fetchall()  # Retrieve all the rows
        print(rows)

        # Generate table frame
        table_frame = make_table_frame()

        # Generate the medicine info table
        generate_medicine_info(rows)

        add_category_button.focus()

        # Bind the <KeyRelease> event to the filter_results function
        category_input_field.bind("<KeyRelease>", filter_results)
        category_input_field.bind("<Up>", focus_previous_widget)
        item_input_field.bind("<KeyRelease>", filter_item_results)
        item_input_field.bind("<Up>", focus_previous_widget)

    # *****************************************************#                    # *****************************************************#
    # ********** Info Page End ****************************#                    # ********** Info Page End ****************************#
    # *****************************************************#                    # *****************************************************#

    # *****************************************************#                    # *****************************************************#
    # ********** Purchase Page ****************************#                    # ********** Purchase Page ****************************#
    # *****************************************************#                    # *****************************************************#

    def open_purchase_page():
        transactions = {}

        global open_find_window

        def open_find_window(event):
            # Create a new window
            find_window = tk.Toplevel(main_app)
            find_window.title("Find")

            # Create the "Find" label
            find_label = tk.Label(
                find_window, text="Find:", font=("Arial", 10))
            find_label.grid(row=0, column=0, padx=10, pady=10)

            # Create the entry field
            find_entry = tk.Entry(find_window, font=("Arial", 10))
            find_entry.grid(row=0, column=1, padx=10, pady=10)

            # Give the main_app window focus
            find_window.focus_force()

            # Take the user's entry
            supplier = supplier_name_entry.get()

            # Set the value of find_entry to the supplier name
            find_entry.insert(0, supplier)

            # Create the table container
            table_container = ttk.Treeview(find_window)
            table_container.grid(
                row=1, column=0, columnspan=2, padx=10, pady=10)

            # Define the column names
            column_names = ["Supplier ID", "Supplier Name"]

            # Configure the table container
            table_container["columns"] = column_names
            table_container["show"] = "headings"

            # Set the column properties
            for column in column_names:
                table_container.heading(column, text=column)
                table_container.column(column, width=100)

            # Generate initial results
            cursor.execute(
                "SELECT * FROM Suppliers WHERE supplier_name LIKE ?", ('%' + supplier + '%',))
            results = cursor.fetchall()

            # Insert the results into the table container
            insert_results_into_table(table_container, results)

            # Update results upon further querying
            find_entry.bind('<KeyRelease>', lambda event: update_results(
                table_container, find_entry))

            # Bind arrow keys and Enter key
            table_container.bind(
                '<Up>', lambda event: select_previous_supplier(table_container, find_entry))
            table_container.bind(
                '<Down>', lambda event: select_next_supplier(table_container))
            table_container.bind('<Return>', lambda event: select_supplier_from_table(
                table_container, find_window))

            # Bind Enter key on find_entry to click on the first item
            find_entry.bind(
                '<Down>', lambda event: click_first_item(table_container, find_window))

            # Destroy window
            find_window.bind('<Escape>', lambda event: destroy(find_window))

            find_entry.focus_force()

        def click_first_item(table_container, find_window):
            table_container.focus_force()
            first_item = table_container.get_children()[0]
            if first_item:
                table_container.selection_set(first_item)
                table_container.focus(first_item)
                table_container.see(first_item)

        def select_previous_supplier(table_container, find_entry):
            selected_item = table_container.focus()
            previous_item = table_container.prev(selected_item)
            if previous_item:
                table_container.selection_set(previous_item)
                table_container.focus(previous_item)
                table_container.see(previous_item)

                return "break"  # To prevent further event propagation
            else:
                find_entry.focus_force()

        def select_next_supplier(table_container):
            selected_item = table_container.focus()
            next_item = table_container.next(selected_item)
            if next_item:
                table_container.selection_set(next_item)
                table_container.focus(next_item)
                table_container.see(next_item)

                return "break"  # To prevent further event propagation

        def select_supplier_from_table(table_container, find_window):
            selected_item = table_container.focus()
            if selected_item:
                supplier = table_container.item(selected_item)["values"][1]
                supplier_id = table_container.item(selected_item)["values"][0]
                select_supplier(supplier_id, supplier, find_window)

        def select_supplier(supplier_id, supplier, find_window):

            # Destroy find window
            find_window.destroy()

            # Add supplier id to supplier_id_label
            supplier_id_label.configure(text=supplier_id)

            # Clear the supplier entry field
            supplier_name_entry.delete(0, tk.END)

            # Insert user's query to supplier entry field
            supplier_name_entry.insert(0, supplier)

            # Focus on first category entry
            first_category = purchase_table_container.grid_slaves(
                row=1, column=0)[0]
            first_category.focus()

        def insert_results_into_table(table_container, results):
            # Clear previous data
            table_container.delete(*table_container.get_children())

            # Insert rows into the table container
            for row in results:
                table_container.insert("", "end", values=row)

        def update_results(table_container, find_entry):
            # Get the new supplier name
            new_supplier = find_entry.get()

            # Generate new results
            cursor.execute(
                "SELECT * FROM Suppliers WHERE supplier_name LIKE ?", ('%' + new_supplier + '%',))
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)

        def open_category_popup(event):
            # Create a new window
            category = event.widget.get()
            find_window = tk.Toplevel(main_app)
            find_window.title("Find")

            # Get the screen width and height
            screen_width = find_window.winfo_screenwidth()
            screen_height = find_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 220
            window_height = 300
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            # Set the window size and position
            find_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            category_entry = event.widget
            row_index = event.widget.grid_info()['row']

            # Create the "Find" label
            find_label = tk.Label(
                find_window, text="Find:", font=("Arial", 10))
            find_label.grid(row=0, column=0, padx=10, pady=10)

            # Create the entry field
            find_entry = tk.Entry(find_window, font=("Arial", 10))
            find_entry.grid(row=0, column=1, padx=10, pady=10)

            # Give the main_app window focus
            find_window.focus_force()

            # Set the value of find_entry to the supplier name
            find_entry.insert(0, category)

            # Create the table container
            table_container = ttk.Treeview(find_window)
            table_container.grid(
                row=1, column=0, columnspan=2, padx=10, pady=10)

            # Define the column names
            column_names = ["Category ID", "Category Name"]

            # Configure the table container
            table_container["columns"] = column_names
            table_container["show"] = "headings"

            # Set the column properties
            for column in column_names:
                table_container.heading(column, text=column)
                table_container.column(column, width=100)

            # Generate initial results
            cursor.execute(
                "SELECT * FROM Categories WHERE category_name LIKE ?", ('%' + category + '%',))
            results = cursor.fetchall()

            # Insert the results into the table container
            insert_results_into_table(table_container, results)
            global receive_row_index

            def receive_row_index():
                return row_index

            # Update results upon further querying
            find_entry.bind('<KeyRelease>', lambda event: update_category_results(
                table_container, find_entry, category_entry, find_window))

            # Bind arrow keys and Enter key
            table_container.bind(
                '<Up>', lambda event: select_previous_supplier(table_container, find_entry))
            table_container.bind(
                '<Down>', lambda event: select_next_supplier(table_container))
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))
            # Bind Enter key on find_entry to click on the first item
            find_entry.bind(
                '<Down>', lambda event: click_first_item(table_container, find_window))

            find_window.bind(
                '<Escape>', lambda event: destroy(find_window))

            click_first_item(table_container, find_window)

            # find_entry.focus_force()

        def update_category_results(table_container, find_entry, category_entry, find_window):
            # Get the new supplier name
            new_category = find_entry.get()

            # Generate new results
            cursor.execute(
                "SELECT * FROM Categories WHERE category_name LIKE ?", ('%' + new_category + '%',))
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))

        def select_category_from_table(table_container, find_window, category_entry):
            selected_item = table_container.focus()
            if selected_item:
                category = table_container.item(selected_item)["values"][1]
                category_id = table_container.item(selected_item)["values"][0]

                select_category(category, category_id,
                                category_entry, find_window)

        def select_category(category, category_id, category_entry, find_window):

            global get_category, receive_find_window

            def receive_find_window():
                return find_window

            def get_category():
                return category, category_id

            # Destroy find window
            if find_window:
                find_window.destroy()
            row_index = receive_row_index()

            # Update the category entry field in the currently modifying row
            category_entry.delete(0, tk.END)
            category_entry.insert(0, category)

            # Focus on item entry
            item_entry = purchase_table_container.grid_slaves(
                row=row_index, column=1)[0]
            item_entry.focus()

        def open_item_popup(event):
            # Create a new window
            item = event.widget.get()
            item_entry = event.widget
            row_index = event.widget.grid_info()['row']
            print("haaaaaaaaaaaaaaaaaaaaaaaa", row_index)
            find_window = tk.Toplevel(main_app)
            find_window.title("Find")

            # Get the screen width and height
            screen_width = find_window.winfo_screenwidth()
            screen_height = find_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 520
            window_height = 300
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            # Set the window size and position
            find_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Create the "Find" label
            find_label = tk.Label(
                find_window, text="Find:", font=("Arial", 10))
            find_label.grid(row=0, column=0, padx=10, pady=10)

            # Create the entry field
            find_entry = tk.Entry(find_window, font=("Arial", 10))
            find_entry.grid(row=0, column=1, padx=10, pady=10)

            # Give the main_app window focus
            find_window.focus_force()

            # Set the value of find_entry to the supplier name
            find_entry.insert(0, item)

            # Create or update the table container
            if hasattr(find_window, "table_container"):
                table_container = find_window.table_container
                # Clear existing data
                table_container.delete(*table_container.get_children())
            else:
                table_container = ttk.Treeview(find_window)
                table_container.grid(
                    row=1, column=0, columnspan=2, padx=10, pady=10)
                find_window.table_container = table_container

                # Define the column names
                column_names = ["Item Name",
                                "Category Name", "Item ID", "Rate"]

                # Configure the table container
                table_container["columns"] = column_names
                table_container["show"] = "headings"

                # Set the column properties
                for column in column_names:
                    table_container.heading(column, text=column)
                    table_container.column(column, width=100)

                # Bind arrow keys and Enter key
                table_container.bind('<Up>', lambda event: select_previous_value(
                    table_container, find_entry))
                table_container.bind(
                    '<Down>', lambda event: select_next_value(table_container))
                table_container.bind('<Return>', lambda event: select_item_from_table(
                    table_container, find_window, item_entry, row_index))
                # Bind Enter key on find_entry to click on the first item
                find_entry.bind('<Down>', lambda event: click_first_item(
                    table_container, find_window))

            # Generate initial results
            category, category_id = get_category()
            # Execute the filtered database query
            # SELECT Categories.category_name, Items.id, Items.item_name, items.item_count,  Items.sell_rate
            cursor.execute(
                '''
                SELECT Items.item_name, Categories.category_name, Items.id, Items.buy_rate
                FROM Items
                INNER JOIN Categories ON Items.category_id = Categories.id
                WHERE Categories.id = ? AND Items.item_name LIKE ?
                ''',
                (category_id, '%' + item + '%')
            )
            results = cursor.fetchall()

            # Insert the results into the table container
            insert_results_into_table(table_container, results)

            click_first_item(table_container, find_window)

            # Update results upon further querying
            find_entry.bind('<KeyRelease>', lambda event: update_item_results(
                table_container, find_entry, item_entry, find_window, row_index))
            # Destroy window upon hitting esc
            find_window.bind('<Escape>', lambda event: destroy(find_window))
            # find_entry.focus_force()

        def update_item_results(table_container, find_entry, item_entry, find_window, row_index):
            # Get the new supplier name
            new_item = find_entry.get()
            category, category_id = get_category()
            # Generate new results
            cursor.execute(
                '''
                SELECT Items.item_name, Categories.category_name, Items.id, Items.buy_rate
                FROM Items
                INNER JOIN Categories ON Items.category_id = Categories.id
                WHERE Categories.id = ? AND Items.item_name LIKE ?
                ''',
                (category_id, '%' + new_item + '%')
            )
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_item_from_table(
                table_container, find_window, item_entry, row_index))

        def select_item_from_table(table_container, find_window, item_entry, row_index):
            selected_item = table_container.selection()
            if selected_item:
                item = table_container.item(selected_item)["values"][0]
                item_id = table_container.item(selected_item)["values"][2]
                rate = table_container.item(selected_item)["values"][3]
                selected_row_index = table_container.index(selected_item) - 1
                select_item(item, item_id, rate, item_entry, selected_item,
                            table_container, find_window, row_index)

        def select_item(item, item_id, rate, item_entry, selected_item, table_container, find_window, row_index):
            update_rate(row_index, rate)
            global get_item_rate

            def get_item_rate():
                return row_index, rate

            global receive_item_id

            def receive_item_id():
                return item_id

            find_window.destroy()

            # Get supplier info based on item
            cursor.execute(
                '''
                SELECT Items.supplier_id, Suppliers.supplier_name
                FROM Items
                INNER JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
                WHERE Items.id = ?
                ''',
                (item_id,)
            )
            supp_info = cursor.fetchone()
            print("SUPPLIER INFO:::", supp_info)
            supp_id, supp_name = supp_info[0], supp_info[1]

            if supp_info:
                # Set value of supplier labels
                supplier_id_label.configure(text=supp_id)
                supplier_name_entry.delete(0, tk.END)
                supplier_name_entry.insert(0, supp_name)
            else:
                supplier_id_label.configure(text="")
                supplier_name_entry.delete(0, tk.END)

            # Set the value of the item_entry
            item_entry.delete(0, tk.END)
            item_entry.insert(0, item)

            qty_entry = purchase_table_container.grid_slaves(
                row=row_index, column=2)[0]
            qty_entry.focus_force()

        def show_qty_confirmation(event, table_frame):
            global get_new_qty, return_event

            def get_new_qty():
                return row_index, int(new_qty)

            def return_event():
                return event

            entry = event.widget
            new_qty = entry.get()

            row_index = entry.grid_info()["row"]

            _, rate = get_item_rate()
            _, category_id = get_category()
            item_id = receive_item_id()

            supplier_id = int(supplier_id_label.cget("text"))

            # Filter only the entry fields for the current row
            row_entries = [widget for widget in table_frame.grid_slaves(
                row=row_index) if isinstance(widget, tk.Entry)]

            # Retrieve the values from the entry fields
            row_data = [entry.get() for entry in row_entries]

            # Reverse the elements of the row_data list
            row_data_reversed = list(reversed(row_data))
            row_data_reversed = [
                item for item in row_data_reversed if item != '']
            print("foe_DATA",  row_data_reversed)
            row_data_reversed[2] = int(row_data_reversed[2])
            row_data_reversed[3] = float(row_data_reversed[3])
            print("fuck_DATA",  row_data_reversed)
            # Calculate row amount
            qty = row_data_reversed[2]
            rate = row_data_reversed[3]
            if qty:
                amount = float(qty) * float(rate)
            else:
                amount = 0.0

            # Update amount on Table column
            update_amount(int(row_index), amount)
            del row_data_reversed[-1]
            # Append rows to transaction
            row_data_reversed.append(category_id)
            row_data_reversed.append(item_id)
            # row_data_reversed.append(float(rate))
            row_data_reversed.append(float(amount))
            row_data_reversed.append(supplier_id)
            transactions[row_index] = row_data_reversed
            print("tataaaaa", transactions)
            total_purchase_amt = 0

            current_last_row = purchase_table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row+1):
                # Clear the text in the columns of the current row
                for col in range(8):  # Assuming there are 5 columns
                    if col == 7:
                        widget = purchase_table_container.grid_slaves(
                            row=row, column=col-3)[0]
                        current_amt = widget.get()
                        print("tpa", current_amt)
                        if current_amt:
                            total_purchase_amt += float(current_amt)
                        else:
                            current_amt = 0

            total_amt.configure(text=total_purchase_amt)

            amt_entry = purchase_table_container.grid_slaves(
                row=row_index, column=4)[0]
            amt_entry.focus()

        def show_amount_confirmation(event, table_container):
            global dialog
            if 'dialog' in globals():
                dialog.destroy()
            dialog = CustomDialog(row_values=transactions)
            dialog.bind('<Escape>', lambda event: destroy(dialog))
            dialog.show()

        class CustomDialog(tk.Toplevel):
            def __init__(self, row_values):
                super().__init__()
                self.row_values = row_values
                self.result = None
                self.title("Qty Confirmation")

                # Create and layout the dialog widgets
                message_label = tk.Label(self, text="Transactions:")
                message_label.pack()

                global receive_message_label

                def receive_message_label():
                    return message_label

                row_values_text = tk.Text(self, height=10, width=50)
                row_values_text.pack()

                # Iterate over the keys of the dictionary and format the values
                for key, values in self.row_values.items():
                    formatted_values = ' '.join(str(value) for value in values)
                    row_values_text.insert(
                        tk.END, f"Item: {key}\n{formatted_values}\n")

                next_category_btn = tk.Button(
                    self, text="Next Category", command=self.handle_next_category)
                next_category_btn.pack(side=tk.LEFT, padx=10)

                next_item_btn = tk.Button(
                    self, text="Next Item", command=self.handle_next_item)
                next_item_btn.pack(side=tk.LEFT, padx=10)

                confirm_btn = tk.Button(
                    self, text="Confirm", command=self.handle_confirm)
                confirm_btn.pack(side=tk.LEFT, padx=10)

                self.focus_force()

                confirm_btn.focus()

                # Get the screen width and height
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()

                # Calculate the x and y coordinates for the window to be centered
                x = int(screen_width / 2 - self.winfo_width() / 2)
                y = int(screen_height / 2 - self.winfo_height() / 2)

                # Set the window's position
                self.geometry(f"+{x}+{y}")

                # Bind left and right arrow keys
                self.bind("<Left>", lambda event: self.focus_previous_button())
                self.bind("<Right>", lambda event: self.focus_next_button())

                # Bind Enter key press to button commands
                next_category_btn.bind(
                    "<Return>", lambda event: next_category_btn.invoke())
                next_item_btn.bind(
                    "<Return>", lambda event: next_item_btn.invoke())
                confirm_btn.bind(
                    "<Return>", lambda event: confirm_btn.invoke())

            def focus_previous_button(self):
                current_focus = self.focus_get()
                buttons = self.get_buttons()

                if current_focus in buttons:
                    current_index = buttons.index(current_focus)
                    previous_index = (current_index - 1) % len(buttons)
                    buttons[previous_index].focus()

            def focus_next_button(self):
                current_focus = self.focus_get()
                buttons = self.get_buttons()

                if current_focus in buttons:
                    current_index = buttons.index(current_focus)
                    next_index = (current_index + 1) % len(buttons)
                    buttons[next_index].focus()

            def get_buttons(self):
                return [widget for widget in self.children.values() if isinstance(widget, tk.Button)]

            def handle_next_category(self):
                self.result = 'Next Category'
                self.destroy()
                # Get the currently focused widget
                event = return_event()
                current_widget = event.widget

                # Get the grid info of the currently focused widget
                current_widget_grid_info = current_widget.grid_info()

                # Get the row index of the currently focused widget
                row_idx = current_widget_grid_info['row']

                last_row_entry = purchase_table_container.grid_slaves(
                    row=row_idx, column=1)[0]

                current_last_row = purchase_table_container.grid_size()[1] - 1
                if row_idx == current_last_row:
                    if last_row_entry.get() != "":
                        # Generate new rows in the table
                        num_rows = 8  # Specify the number of rows to add
                        for i in range(num_rows):
                            new_row = row_idx + i + 1

                            # Category entry field
                            category_entry = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            category_entry.grid(
                                row=new_row, column=0, padx=10, pady=5)
                            category_entry.bind(
                                '<Return>', open_category_popup)

                            # Item Particular entry field
                            item_entry = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            item_entry.grid(
                                row=new_row, column=1, padx=10, pady=5)
                            item_entry.bind('<Return>', open_item_popup)

                            # Qty entry field
                            qty_entry = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            qty_entry.grid(
                                row=new_row, column=2, padx=10, pady=5)
                            qty_entry.bind('<Return>', lambda event: show_qty_confirmation(
                                event, purchase_table_container))

                            # Rate label
                            rate_label = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            rate_label.grid(
                                row=new_row, column=3, padx=10, pady=5)

                            # Amount label
                            amount_label = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            amount_label.grid(
                                row=new_row, column=4, padx=10, pady=5)
                            amount_label.bind(
                                '<Return>', lambda event: show_amount_confirmation(event, purchase_table_container))

                        scroll_down()

                # Get the category entry field in the next row
                next_category_entry = purchase_table_container.grid_slaves(
                    row=row_idx+1, column=0)[0]
                next_category_entry.focus()

            def handle_next_item(self):
                self.result = 'Next Item'
                self.destroy()
                # Get the currently focused widget
                event = return_event()
                row_idx = event.widget.grid_info()['row']
                category, category_id = get_category()
                find_window = receive_find_window()

                # Check if the last row is filled
                last_row_entry = purchase_table_container.grid_slaves(
                    row=row_idx, column=1)[0]

                current_last_row = purchase_table_container.grid_size()[1] - 1
                if row_idx == current_last_row:
                    if last_row_entry.get() != "":
                        # Generate new rows in the table
                        num_rows = 8  # Specify the number of rows to add
                        for i in range(num_rows):
                            new_row = row_idx + i + 1

                            # Category entry field
                            category_entry = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            category_entry.grid(
                                row=new_row, column=0, padx=10, pady=5)
                            category_entry.bind(
                                '<Return>', open_category_popup)

                            # Item Particular entry field
                            item_entry = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            item_entry.grid(
                                row=new_row, column=1, padx=10, pady=5)
                            item_entry.bind('<Return>', open_item_popup)

                            # Qty entry field
                            qty_entry = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            qty_entry.grid(
                                row=new_row, column=2, padx=10, pady=5)
                            qty_entry.bind('<Return>', lambda event: show_qty_confirmation(
                                event, purchase_table_container))

                            # Rate label
                            rate_label = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            rate_label.grid(
                                row=new_row, column=3, padx=10, pady=5)

                            # Amount label
                            amount_label = tk.Entry(
                                purchase_table_container, font=("Arial", 10))
                            amount_label.grid(
                                row=new_row, column=4, padx=10, pady=5)
                            amount_label.bind(
                                '<Return>', lambda event: show_amount_confirmation(event, purchase_table_container))

                        scroll_down()

                # Get the category entry field in the next row
                next_category_entry = purchase_table_container.grid_slaves(
                    row=row_idx+1, column=0)[0]

                next_row_entry = purchase_table_container.grid_slaves(
                    row=row_idx+1, column=1)[0]

                next_category = next_row_entry.get()
                if next_category == "":
                    # Call the select_category function with the next category and category ID
                    select_category(category, category_id,
                                    next_category_entry, find_window)
                next_row_entry.focus()

            def handle_confirm(self):
                self.result = 'Confirm'
                # Get the necessary column values to insert in the database
                invoice = int(invoice_number_entry.get())
                user_id = int(user[0])
                date = current_date_label.cget("text")
                # supplier_id = int(supplier_id_label.cget("text"))
                remark = str(remark_entry.get())
                form_type = selected_type.get()

                if form_type == "purchase":
                    # Create a list of tuples for insertion
                    medicine_purchases = []
                    unique_item_ids = set()  # Keep track of unique item IDs
                    print("trassasfasfasfasfasfasfasfasf", transactions)
                    for row in transactions.keys():
                        row_item_id = transactions[row][4]
                        row_item_quantity = int(transactions[row][2])
                        print(
                            f"Row item id is: {row_item_id}, Row item quantity is: {row_item_quantity}")
                        if row_item_id not in unique_item_ids:
                            unique_item_ids.add(row_item_id)
                            fixed_entries = [invoice, user_id,
                                             date, remark]

                            print("CURRENT FIXED ENTRIES:::::", fixed_entries)
                            for index, col in enumerate(transactions[row]):
                                if index > 1:
                                    fixed_entries.append(col)
                            medicine_purchases.append(tuple(fixed_entries))
                            print("mpppppppppppppp:", medicine_purchases)

                    try:
                        for row_idx, row_item_id in enumerate(unique_item_ids):
                            # Generate new results
                            cursor.execute(
                                "SELECT item_count FROM Items WHERE id=?", (row_item_id,))
                            row_item_count = cursor.fetchone()
                            print(row_item_count)
                            new_item_count = row_item_count[0] + \
                                row_item_quantity
                            cursor.execute(
                                "UPDATE Items SET item_count=? WHERE id=?", (new_item_count,  row_item_id))
                            purchase_ledgers = [medicine_purchases[row_idx][6],
                                                medicine_purchases[row_idx][2], medicine_purchases[row_idx][4], row_item_count[0], new_item_count]
                            purchase_ledgers = [tuple(purchase_ledgers)]
                            print("Purchase LEDGERS::", purchase_ledgers)
                            cursor.executemany(
                                "INSERT INTO ItemLedgers (item_id,date,purchase,opening,closing) VALUES (?,?,?,?,?)",
                                (purchase_ledgers)
                            )
                        print("Executing insert query::::::", row)
                        cursor.executemany(
                            "INSERT INTO MedicinePurchases (invoice_id, user_id, date, remarks, quantity, category_id, item_id, amount, supplier_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            medicine_purchases
                        )

                        cursor.execute("SELECT * FROM  ItemLedgers")

                        l_rows = cursor.fetchall()

                        # Print the rows
                        for l in l_rows:
                            print(l)

                        message_label = receive_message_label()
                        message_label.configure(
                            text="Data inserted successfully")
                        conn.commit()
                        self.destroy()
                        open_purchase_page()
                    except sqlite3.IntegrityError:
                        message_label = receive_message_label()
                        message_label.configure(
                            text="Cannot insert same category and item multiple times in a single invoice")

                if form_type == "purchase-search":
                    # Retrieve the document from the table based on the invoice number
                    cursor.execute(
                        "SELECT * FROM MedicinePurchases WHERE invoice_id=?", (invoice,))
                    rows = cursor.fetchall()
                    print("Hadasdsfsfa: ", rows)
                    # Iterate over the retrieved rows
                    for row_idx, row in enumerate(rows):
                        # Extract the necessary information from the row
                        purchase_id = row[0]
                        old_quantity = row[6]
                        old_amount = row[9]
                        item_id = row[8]
                        print("Transactions tarafas: ", transactions)
                        for key in transactions.keys():
                            if row_idx+1 == key:
                                updated_quantity = int(
                                    transactions[key][2])

                                # Calculate the difference in quantity
                                quantity_difference = updated_quantity - old_quantity
                                cursor.execute(
                                    "SELECT buy_rate FROM Items WHERE id=?", (item_id,))
                                current_item_rate = cursor.fetchone()[0]
                                # Update the quantity and amount in the MedicinePurchases table
                                updated_amount = updated_quantity * current_item_rate
                                cursor.execute("UPDATE MedicinePurchases SET quantity=?, amount=? WHERE purchase_id=?",
                                               (updated_quantity, updated_amount, purchase_id))

                                # Update the item count in the Items table based on the quantity difference
                                cursor.execute(
                                    "SELECT item_count FROM Items WHERE id=?", (item_id,))
                                current_item_count = cursor.fetchone()[0]
                                new_item_count = current_item_count + quantity_difference
                                cursor.execute(
                                    "UPDATE Items SET item_count=? WHERE id=?", (new_item_count, item_id))

                                sale_ledgers = [item_id, date,
                                                abs(quantity_difference), current_item_count, new_item_count]
                                sale_ledgers = [tuple(sale_ledgers)]
                                print("SALE LEDGERS::", sale_ledgers)

                                if updated_quantity <= old_quantity:

                                    cursor.executemany(
                                        "INSERT INTO ItemLedgers (item_id, date, return_buy, opening,closing) VALUES (?, ?, ?,?,?)",
                                        (sale_ledgers)
                                    )

                                elif updated_quantity > old_quantity:

                                    cursor.executemany(
                                        "INSERT INTO ItemLedgers (item_id, date, purchase,opening,closing) VALUES (?, ?, ?,?,?)",
                                        (sale_ledgers)
                                    )

                                conn.commit()
                                message_label = receive_message_label()
                                message_label.configure(
                                    text="Operation Completed")

                                self.destroy()

            def show(self):
                self.wait_window(self)
                return self.result

        def delete():
            current_last_row = purchase_table_container.grid_size()[1] - 1
            invoice = int(invoice_number_entry.get())
            form_type = selected_type.get()
            cursor.execute(
                "SELECT * FROM MedicinePurchases WHERE invoice_id=?", (invoice,))
            purchases = cursor.fetchall()
            cursor.execute(
                '''
                SELECT MedicinePurchases.purchase_id, Suppliers.supplier_id,Suppliers.supplier_name,MedicinePurchases.remarks,Categories.category_name,Items.id, Items.item_name,MedicinePurchases.quantity, Items.buy_rate, MedicinePurchases.amount,MedicinePurchases.date
                FROM MedicinePurchases
                INNER JOIN Suppliers ON MedicinePurchases.supplier_id = Suppliers.supplier_id
                INNER JOIN Categories ON MedicinePurchases.category_id = Categories.id
                INNER JOIN Items ON MedicinePurchases.item_id = Items.id
                WHERE MedicinePurchases.invoice_id = ?
                ''',
                (invoice,)
            )
            global previous_info
            previous_info = cursor.fetchall()
            print("xyzabcdefghijkl:", previous_info)
            confirmation = messagebox.askyesno(
                "Confirmation", "Are you sure you want to delete this row?")
            if confirmation:
                if form_type == "purchase":
                    # Find the focused entry field and clear the text in its row
                    row_index = None  # Initialize the row_index variable
                    for row in range(1, current_last_row + 1):
                        for col in range(5):  # Assuming there are 5 columns
                            widget = purchase_table_container.grid_slaves(
                                row=row, column=col)[0]
                            if isinstance(widget, tk.Entry) and widget == main_app.focus_get():
                                row_index = row  # Store the current row index
                                # Clear the text in the columns of the corresponding row
                                for clear_col in range(5):
                                    clear_widget = purchase_table_container.grid_slaves(
                                        row=row, column=clear_col)[0]
                                    if isinstance(clear_widget, tk.Entry):
                                        clear_widget.delete(0, tk.END)
                                    elif isinstance(clear_widget, tk.Label):
                                        clear_widget.configure(text="")
                                break  # Break the inner loop once the focused entry widget is found
                        else:
                            continue  # Continue to the next row if the focused entry widget is not found
                        break  # Break the outer loop once the row is cleared

                    # Use the row_index variable for further operations if needed
                    if row_index is not None:
                        if row_index in transactions:
                            del transactions[row_index]
                            print(transactions)
                            # Update the remaining row indices in the transactions dictionary
                            for idx in range(row_index + 1, current_last_row + 1):
                                if idx in transactions:
                                    transactions[idx -
                                                 1] = transactions.pop(idx)
                            # Call the update_amount() function to recalculate the total amount
                            total_purchase_amt = 0
                            for idx, info in transactions.items():
                                current_amt = info[5]
                                total_purchase_amt += current_amt

                            update_total_amount(total_purchase_amt)
                        else:
                            print("Row index not found in transactions dictionary.")

                    else:
                        print("No focused entry widget found.")
                    # Delete the text of the supplier name and ID
                    if isinstance(main_app.focus_get(), tk.Entry):
                        if main_app.focus_get() == supplier_name_entry:
                            supplier_name_entry.delete(0, tk.END)
                            supplier_id_label.configure(text="")
                if form_type == "purchase-search":
                    # Find the focused entry field and clear the text in its row
                    row_index = None  # Initialize the row_index variable
                    for row in range(1, current_last_row + 1):
                        for col in range(5):  # Assuming there are 5 columns
                            widget = purchase_table_container.grid_slaves(
                                row=row, column=col)[0]
                            if isinstance(widget, tk.Entry) and widget == main_app.focus_get():
                                row_index = row
                                deleting_row = previous_info[row-1]
                                deleting_row_purchase_id = deleting_row[0]
                                deleting_row_item_id = deleting_row[5]
                                deleting_row_qty = deleting_row[7]
                                deleting_row_date = deleting_row[-1]
                                cursor.execute(
                                    "DELETE FROM MedicinePurchases WHERE purchase_id=?", (deleting_row_purchase_id,))

                                cursor.execute(
                                    "SELECT item_count FROM Items WHERE id=?", (deleting_row_item_id,))
                                row_item_count = cursor.fetchone()
                                print(row_item_count)
                                new_item_count = row_item_count[0] - \
                                    deleting_row_qty
                                cursor.execute(
                                    "UPDATE Items SET item_count=? WHERE id=?", (new_item_count,  deleting_row_item_id))
                                purchase_ledgers = [
                                    deleting_row_item_id, deleting_row_date, deleting_row_qty]
                                purchase_ledgers = [tuple(purchase_ledgers)]
                                print("Purchase LEDGERS::", purchase_ledgers)
                                cursor.executemany(
                                    "INSERT INTO ItemLedgers (item_id, date, return_buy) VALUES (?, ?, ?)",
                                    (purchase_ledgers)
                                )
                                conn.commit()
                                search()

        def refresh():
            current_last_row = purchase_table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row + 1):
                # Clear the text in the columns of the current row
                for col in range(5):  # Assuming there are 5 columns
                    widget = purchase_table_container.grid_slaves(
                        row=row, column=col)[0]
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                    elif isinstance(widget, tk.Label):
                        widget.configure(text="")

            # Clear the transactions dictionary
            transactions.clear()
            supplier_id_label.configure(text="")
            supplier_name_entry.delete(0, tk.END)
            remark_entry.delete(0, tk.END)
            # Call the update_amount() function to reset the total amount
            update_total_amount(0)

        def hard_refresh():
            form_type = selected_type.get()
            current_last_row = purchase_table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row + 1):
                # Clear the text in the columns of the current row
                for col in range(5):  # Assuming there are 5 columns
                    widget = purchase_table_container.grid_slaves(
                        row=row, column=col)[0]
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                    elif isinstance(widget, tk.Label):
                        widget.configure(text="")

            # Clear the transactions dictionary
            transactions.clear()
            supplier_id_label.configure(text="")
            supplier_name_entry.delete(0, tk.END)
            remark_entry.delete(0, tk.END)

            # Call the update_amount() function to reset the total amount
            update_total_amount(0)

            if form_type == "purchase-search":
                search()

        def search():
            refresh()
            selected_type.set("purchase-search")
            g_label.configure(width=8)
            invoice = int(invoice_number_entry.get())
            cursor.execute(
                "SELECT * FROM MedicinePurchases WHERE invoice_id=?", (invoice,))
            purchases = cursor.fetchall()
            cursor.execute(
                '''
                SELECT Suppliers.supplier_id,Suppliers.supplier_name,MedicinePurchases.remarks,Categories.category_name,Items.id, Items.item_name,MedicinePurchases.quantity, Items.buy_rate, MedicinePurchases.amount,MedicinePurchases.date
                FROM MedicinePurchases
                INNER JOIN Suppliers ON MedicinePurchases.supplier_id = Suppliers.supplier_id
                INNER JOIN Categories ON MedicinePurchases.category_id = Categories.id
                INNER JOIN Items ON MedicinePurchases.item_id = Items.id
                WHERE MedicinePurchases.invoice_id = ?
                ''',
                (invoice,)
            )
            global previous_info
            previous_info = cursor.fetchall()
            print("ruck: ", previous_info)
            supplier_id, supplier_name, remark, current_date_pls = previous_info[
                0][0], previous_info[0][1], previous_info[0][2], previous_info[0][9]
            print("ASFDGHGDFSDFDGDFSDGdfagrhteyrwtrythgfdf", previous_info)

            supplier_id_label.configure(text=supplier_id)
            supplier_name_entry.delete(0, tk.END)
            supplier_name_entry.insert(0, supplier_name)
            remark_entry.delete(0, tk.END)
            remark_entry.insert(0, remark)
            current_date_label.configure(text=current_date_pls)
            for widget in purchase_table_container.winfo_children():
                widget.destroy()
            # Create the table headers
            headers = ["Category", "Item Particular", "Qty", "Rate", "Amount"]
            num_columns = len(headers)

            # Adjust the percentage as needed
            table_width = round(window_width * 0.69 * 0.1)
            column_width = round(table_width / num_columns)
            for col, header in enumerate(headers):
                header_label = tk.Label(purchase_table_container, text=header, font=(
                    "Arial", 10, "bold"), bg="white", borderwidth=1, relief="solid", width=column_width, padx=10, pady=5)
                header_label.grid(row=0, column=col)

            # Create rows in the table
            total_amount = 0
            for row_index, row_data in enumerate(previous_info):
                row_data = list(row_data)

                indices_to_remove = [0, 1, 2, 4, 9]
                # Sort the indices in descending order
                indices_to_remove.sort(reverse=True)

                for index in indices_to_remove:
                    del row_data[index]
                print("RRRRRRWOWWOWOWOWOWOW: ", row_data)
                for col_index, value in enumerate(row_data):
                    entry = tk.Entry(purchase_table_container, font=(
                        "Arial", 10), relief="solid", width=column_width, bg="white")
                    entry.insert(0, value)
                    entry.grid(row=row_index + 1,
                               column=col_index, sticky="nsew")
                    if col_index == 0:
                        entry.bind('<Return>', open_category_popup)
                    elif col_index == 1:
                        entry.bind('<Return>', open_item_popup)
                    elif col_index == 2:
                        entry.bind('<Return>', lambda event: show_qty_confirmation(
                            event, purchase_table_container))
                    elif col_index == 4:
                        entry.bind('<Return>', lambda event: show_amount_confirmation(
                            event, purchase_table_container))
                        total_amount += float(value)

            total_amt.configure(text=total_amount)

        def update_rate(row_idx, rate):
            # Find the rate label in the third row
            rate_label = purchase_table_container.grid_slaves(
                row=row_idx, column=3)[0]

            # Update the rate value
            rate_label.delete(0, tk.END)
            rate_label.insert(0, rate)

        def update_amount(row_index, amount):
            # Find the amount label in the third row
            amount_label = purchase_table_container.grid_slaves(
                row=row_index, column=4)[0]

            # Update the amount value
            amount_label.delete(0, tk.END)
            amount_label.insert(0, amount)

        global total_purchase_amt
        # total_purchase_amt = 0

        def update_total_amount(total_amount):
            # Update the amount value
            total_amt.config(text=total_amount)

        def below_category(event):
            current_row_index = event.widget.grid_info()['row']
            next_category_entry = purchase_table_container.grid_slaves(
                row=current_row_index+1, column=0)[1]

            next_category_entry.focus()

        # Clear previous elements
        clear_frame(body_container)

        # Create the header label
        header_label = tk.Label(body_container, text="Medicine Purchase",
                                font=("Arial", 24, "bold"), borderwidth=1, relief='solid', bg="#F5F5DC", fg="black")
        header_label.pack(pady=(10, 20))
        # Create the info container
        btn_container = tk.Frame(body_container, bg="white")
        btn_container.pack()
        delete_button = tk.Button(
            btn_container, text="Delete", width=5, font=2, bg='#C41E3A', fg='white', command=delete)
        delete_button.grid(row=0, column=0, pady=2)

        Refresh_button = tk.Button(
            btn_container, text="Refresh", width=6, font=2, bg='#50C878', fg='white', command=hard_refresh)
        Refresh_button.grid(row=0, column=1, pady=2)

        Search_button = tk.Button(
            btn_container, text="Search", width=6, font=2, bg='#4169E1', fg='white', command=search)
        Search_button.grid(row=0, column=2, pady=2)

        # Create the info container
        purchase_container = tk.Frame(body_container, bg="white")
        purchase_container.pack()

        # Create the "type" label
        type_purchase_label = tk.Label(
            purchase_container, text="Type:", font=("Arial", 10), bg="white")
        type_purchase_label.grid(row=1, column=0, pady=10)

        # Create the dropdown with the "purchase" option
        selected_type = tk.StringVar()
        selected_type.set("purchase")  # Set the default value
        type_purchase_dropdown = ttk.OptionMenu(
            purchase_container, selected_type, "purchase", "purchase", "purchase-search")
        type_purchase_dropdown.grid(row=1, column=1, columnspan=1, pady=10)
        # Create a gap of 7 columns on the left side
        g_label = tk.Label(purchase_container, text="", bg="white", width=13)
        g_label.grid(row=1, column=2)

        def on_type_change(*args):
            selected_value = selected_type.get()
            if selected_value == "purchase-search":
                g_label.config(width=8)
            else:
                g_label.config(width=13)

        # Add a trace to the selected_type variable to detect changes
        selected_type.trace_add("write", on_type_change)

        # Create the "Date" label
        date_label = ttk.Label(
            purchase_container, text="Date:", font=("Arial", 10), background="white")
        date_label.grid(row=1, column=3,  pady=10)

        # Get the current date
        current_date = datetime.now().strftime("%d-%m-%Y")
        # Create the label with the current date
        current_date_label = ttk.Label(
            purchase_container, text=current_date, font=("Arial", 10), background="white", borderwidth=1, relief="solid")
        current_date_label.grid(row=1, column=4, columnspan=1,  pady=10)
        # Create a gap of 7 columns on the left side
        g1_label = tk.Label(purchase_container, text="", bg="white", width=12)
        g1_label.grid(row=1, column=5)
        # Create the "Invoice No." label
        invoice_label = tk.Label(
            purchase_container, text="Invoice:", font=("Arial", 10), bg="white")
        invoice_label.grid(row=1, column=6, padx=2, pady=10)

        # Execute the query to fetch all rows from "MedicinePurchases" table
        cursor.execute("SELECT MAX(invoice_id) FROM MedicinePurchases")

        # Fetch the result
        result = cursor.fetchone()

        # Get the largest invoice ID
        largest_invoice_id = result[0] if result[0] is not None else 0

        # Generate invoice number by adding 1 to the largest invoice ID
        invoice_number = largest_invoice_id + 1

        # Create the entry field for the invoice number
        invoice_number_entry = ttk.Entry(
            purchase_container, font=("Arial", 10), width=10)
        invoice_number_entry.insert(0, invoice_number)
        invoice_number_entry.grid(row=1, column=7, pady=10)

        s_container = tk.Frame(body_container, bg="white")
        s_container.pack()

        # Create the "Supplier ID" label
        supplier_name_label = tk.Label(
            s_container, text="Supplier Name:", font=("Arial", 10), bg="white")
        supplier_name_label.grid(row=2, column=0, padx=0, pady=10)

        # Create the "Supplier Name" label
        supplier_id_label = tk.Label(
            s_container, text="", font=("Arial", 10), bg="white", width=10, borderwidth=1, relief="solid")
        supplier_id_label.grid(row=2, column=1, padx=0, pady=10)

        # Create the entry field
        supplier_name_entry = tk.Entry(s_container, font=("Arial", 10))
        supplier_name_entry.grid(row=2, column=2, padx=10, pady=10)
        # supplier_name_entry.focus_force()
        # Create a gap of 7 columns on the left side
        g2_label = tk.Label(s_container, text="", bg="white", width=27)
        g2_label.grid(row=2, column=3)
        # Bind the event to open the find window to the Return key press
        supplier_name_entry.bind(
            '<Return>', lambda event: open_find_window(event))
        r_container = tk.Frame(body_container, bg="white")
        r_container.pack()
        # Create the "Remark" label
        remark_label = tk.Label(
            r_container, text="Remarks:", font=("Arial", 10), bg="white", width=10, borderwidth=1, relief="solid")
        remark_label.grid(row=3, column=0, padx=2, pady=10)

        # Create the entry field
        remark_entry = tk.Entry(r_container, font=("Arial", 10))
        remark_entry.grid(row=3, column=1, padx=10, pady=10)
        # Create a gap of 7 columns on the left side
        g3_label = tk.Label(r_container, text="", bg="white", width=40)
        g3_label.grid(row=3, column=2)
        purchase_table_container = make_table_frame()
        # Create the table headers
        headers = ["Category", "Item Particular", "Qty", "Rate", "Amount"]
        num_columns = len(headers)

        # Adjust the percentage as needed
        table_width = round(window_width * 0.69 * 0.1)
        column_width = round(table_width / num_columns)
        print(column_width)

        for col, header in enumerate(headers):
            header_label = tk.Label(purchase_table_container, text=header, font=(
                "Arial", 10, "bold"), bg="white", padx=10, pady=5, relief="solid", width=column_width)
            header_label.grid(row=0, column=col, sticky="nsew")

        # Create the rows
        num_rows = 8  # Specify the number of rows in the table
        for row in range(1, num_rows + 1):
            # Category entry field
            category_entry = tk.Entry(
                purchase_table_container, font=("Arial", 10))
            category_entry.grid(row=row, column=0, padx=10, pady=5)
            # Bind the Return key event
            category_entry.bind('<Return>', open_category_popup)
            category_entry.bind('<Down>', lambda event: below_category(event))

            # Item Particular entry field
            item_entry = tk.Entry(purchase_table_container, font=("Arial", 10))
            item_entry.grid(row=row, column=1, padx=10, pady=5)
            item_entry.bind('<Return>', open_item_popup)

            # Qty entry field
            qty_entry = tk.Entry(purchase_table_container, font=("Arial", 10))
            qty_entry.grid(row=row, column=2, padx=10, pady=5)
            qty_entry.bind('<Return>', lambda event: show_qty_confirmation(
                event, purchase_table_container))

            # Rate label
            rate_label = tk.Entry(
                purchase_table_container, font=("Arial", 10))
            rate_label.grid(row=row, column=3, padx=10, pady=5)

            # Amount label
            amount_label = tk.Entry(
                purchase_table_container, font=("Arial", 10))
            amount_label.grid(row=row, column=4, padx=10, pady=5)
            amount_label.bind(
                '<Return>', lambda event: show_amount_confirmation(event, purchase_table_container))
        # Create a separate frame outside the scrollable frame for fixed elements
        fixed_frame = tk.Frame(body_container, bg="white")
        fixed_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.95)

        # Create a gap of 7 columns on the left side
        gap_label = tk.Label(fixed_frame, text="", bg="white", width=97)
        gap_label.grid(row=0, column=0)

        total_label = tk.Label(
            fixed_frame, text="Total:", font=("Arial", 10), bg="white", width=10, borderwidth=1, relief="solid")
        total_label.grid(row=0, column=1, padx=10, pady=10)

        total_amt = tk.Label(fixed_frame, font=(
            "Arial", 10), borderwidth=1, relief="solid", width=10)
        total_amt.grid(row=0, column=2, padx=10, pady=10)

        first_cat = purchase_table_container.grid_slaves(row=1, column=0)[0]
        first_cat.focus()

        delete_button.bind_all("<Control-d>", lambda event: delete())
        Refresh_button.bind_all("<Control-r>", lambda event: hard_refresh())
        Search_button.bind_all("<Control-s>", lambda event: search())
        invoice_number_entry.bind("<Return>", lambda event: search())
    # *****************************************************#                    # *****************************************************#
    # ********** Purchase Page End ************************#                    # ********** Purchase Page End ************************#
    # *****************************************************#                    # *****************************************************#

    # *****************************************************#                    # *****************************************************#
    # ********** Sale Page ********************************#                    # ********** Sale Page ********************************#
    # *****************************************************#                    # *****************************************************#

    def open_sales_page():
        transactions = {}

        def click_first_item(table_container, find_window):
            table_container.focus_force()
            first_item = table_container.get_children()[0]
            if first_item:
                table_container.selection_set(first_item)
                table_container.focus(first_item)
                table_container.see(first_item)

        def select_previous_category(table_container, find_entry):
            selected_item = table_container.focus()
            previous_item = table_container.prev(selected_item)
            if previous_item:
                table_container.selection_set(previous_item)
                table_container.focus(previous_item)
                table_container.see(previous_item)

                return "break"  # To prevent further event propagation
            else:
                find_entry.focus_force()

        def select_next_category(table_container):
            selected_item = table_container.focus()
            next_item = table_container.next(selected_item)
            if next_item:
                table_container.selection_set(next_item)
                table_container.focus(next_item)
                table_container.see(next_item)

                return "break"  # To prevent further event propagation

        def insert_results_into_table(table_container, results):
            # Clear previous data
            table_container.delete(*table_container.get_children())

            # Insert rows into the table container
            for row in results:
                table_container.insert("", "end", values=row)

        def open_category_popup(event):

            global receive_row_index

            def receive_row_index():
                return row_index

            # Create a new window
            category = event.widget.get()
            find_window = tk.Toplevel(main_app)
            find_window.title("Find")

            # Get the screen width and height
            screen_width = find_window.winfo_screenwidth()
            screen_height = find_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 220
            window_height = 300
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            # Set the window size and position
            find_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            category_entry = event.widget
            row_index = event.widget.grid_info()['row']

            # Create the "Find" label
            find_label = tk.Label(
                find_window, text="Find:", font=("Arial", 10))
            find_label.grid(row=0, column=0, padx=10, pady=10)

            # Create the entry field
            find_entry = tk.Entry(find_window, font=("Arial", 10))
            find_entry.grid(row=0, column=1, padx=10, pady=10)

            # Give the main_app window focus
            find_window.focus_force()

            # Set the value of find_entry to the supplier name
            find_entry.insert(0, category)

            # Create the table container
            table_container = ttk.Treeview(find_window)
            table_container.grid(
                row=1, column=0, columnspan=2, padx=10, pady=10)

            # Define the column names
            column_names = ["Category ID", "Category Name"]

            # Configure the table container
            table_container["columns"] = column_names
            table_container["show"] = "headings"

            # Set the column properties
            for column in column_names:
                table_container.heading(column, text=column)
                table_container.column(column, width=100)

            # Generate initial results
            cursor.execute(
                "SELECT * FROM Categories WHERE category_name LIKE ?", ('%' + category + '%',))
            results = cursor.fetchall()

            # Insert the results into the table container
            insert_results_into_table(table_container, results)

            # Update results upon further querying
            find_entry.bind('<KeyRelease>', lambda event: update_category_results(
                table_container, find_entry, category_entry, find_window))

            # Bind arrow keys and Enter key
            table_container.bind(
                '<Up>', lambda event: select_previous_category(table_container, find_entry))
            table_container.bind(
                '<Down>', lambda event: select_next_category(table_container))
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))
            # Bind Enter key on find_entry to click on the first item
            find_entry.bind(
                '<Down>', lambda event: click_first_item(table_container, find_window))

            find_window.bind(
                '<Escape>', lambda event: destroy(find_window))

            click_first_item(table_container, find_window)

            # find_entry.focus_force()

        def update_category_results(table_container, find_entry, category_entry, find_window):
            # Get the new supplier name
            new_category = find_entry.get()

            # Generate new results
            cursor.execute(
                "SELECT * FROM Categories WHERE category_name LIKE ?", ('%' + new_category + '%',))
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_category_from_table(
                table_container, find_window, category_entry))

        def select_category_from_table(table_container, find_window, category_entry):
            selected_item = table_container.focus()
            if selected_item:
                category = table_container.item(selected_item)["values"][1]
                category_id = table_container.item(selected_item)["values"][0]

                select_category(category, category_id,
                                category_entry, find_window)

        def select_category(category,  category_id, category_entry, find_window):
            # Destroy find window
            if find_window:
                find_window.destroy()
            row_index = receive_row_index()
            # Update the category entry field in the currently modifying row
            category_entry.delete(0, tk.END)
            category_entry.insert(0, category)
            global get_category, receive_find_window

            def receive_find_window():
                return find_window

            def get_category():
                return category, category_id
            # Focus on item entry
            item_entry = sale_table_container.grid_slaves(
                row=row_index, column=1)[0]
            item_entry.focus()

        def open_item_popup(event):
            # Create a new window
            item = event.widget.get()
            item_entry = event.widget
            row_index = event.widget.grid_info()['row']
            print("haaaaaaaaaaaaaaaaaaaaaaaa", row_index)

            qty_entry = sale_table_container.grid_slaves(
                row=row_index, column=3)[0]
            qty_entry.focus()

            find_window = tk.Toplevel(main_app)
            find_window.title("Find")

            # Get the screen width and height
            screen_width = find_window.winfo_screenwidth()
            screen_height = find_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 520
            window_height = 300
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            # Set the window size and position
            find_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Create the "Find" label
            find_label = tk.Label(
                find_window, text="Find:", font=("Arial", 10))
            find_label.grid(row=0, column=0, padx=10, pady=10)

            # Create the entry field
            find_entry = tk.Entry(find_window, font=("Arial", 10))
            find_entry.grid(row=0, column=1, padx=10, pady=10)

            # Give the main_app window focus
            find_window.focus_force()

            # Set the value of find_entry to the supplier name
            find_entry.insert(0, item)

            # Create or update the table container
            if hasattr(find_window, "table_container"):
                table_container = find_window.table_container
                # Clear existing data
                table_container.delete(*table_container.get_children())
            else:
                table_container = ttk.Treeview(find_window)
                table_container.grid(
                    row=1, column=0, columnspan=2, padx=10, pady=10)
                find_window.table_container = table_container

                # Define the column names
                column_names = ["Category Name", "Item ID",
                                "Item Name", "Count", "Rate"]

                # Configure the table container
                table_container["columns"] = column_names
                table_container["show"] = "headings"

                # Set the column properties
                for column in column_names:
                    table_container.heading(column, text=column)
                    table_container.column(column, width=100)

                # Bind arrow keys and Enter key
                table_container.bind('<Up>', lambda event: select_previous_category(
                    table_container, find_entry))
                table_container.bind(
                    '<Down>', lambda event: select_next_category(table_container))
                table_container.bind('<Return>', lambda event: select_item_from_table(
                    table_container, find_window, item_entry, row_index))
                # Bind Enter key on find_entry to click on the first item
                find_entry.bind('<Down>', lambda event: click_first_item(
                    table_container, find_window))

                find_window.bind(
                    '<Escape>', lambda event: destroy(find_window))

            # Generate initial results
            category, category_id = get_category()
            # Execute the filtered database query
            cursor.execute(
                '''
                SELECT Categories.category_name, Items.id, Items.item_name,items.item_count,  Items.sell_rate
                FROM Items
                INNER JOIN Categories ON Items.category_id = Categories.id
                WHERE Categories.id = ? AND Items.item_name LIKE ?
                ''',
                (category_id, '%' + item + '%')
            )
            results = cursor.fetchall()

            # Insert the results into the table container
            insert_results_into_table(table_container, results)
            click_first_item(table_container, find_window)

            # Update results upon further querying
            find_entry.bind('<KeyRelease>', lambda event: update_item_results(
                table_container, find_entry, item_entry, find_window, row_index))
            # Destroy window upon hitting esc
            find_window.bind('<Escape>', lambda event: destroy(find_window))
            # find_entry.focus_force()

        def update_item_results(table_container, find_entry, item_entry, find_window, row_index):
            # Get the new supplier name
            new_item = find_entry.get()
            category, category_id = get_category()
            # Generate new results
            cursor.execute(
                '''
                SELECT Categories.category_name, Items.id, Items.item_name, items.item_count, Items.sell_rate
                FROM Items
                INNER JOIN Categories ON Items.category_id = Categories.id
                WHERE Categories.id = ? AND Items.item_name LIKE ?
                ''',
                (category_id, '%' + new_item + '%')
            )
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_item_from_table(
                table_container, find_window, item_entry, row_index))

        def select_item_from_table(table_container, find_window, item_entry, row_index):
            selected_item = table_container.selection()
            if selected_item:
                item_id = table_container.item(selected_item)["values"][1]
                item = table_container.item(selected_item)["values"][2]
                count = table_container.item(selected_item)["values"][3]
                rate = table_container.item(selected_item)["values"][4]
                selected_row_index = table_container.index(selected_item) - 1
                select_item(item, item_id, count,  rate, item_entry, selected_item,
                            table_container, find_window, row_index)

        def select_item(item, item_id, count,  rate, item_entry, selected_item, table_container, find_window, row_index):
            find_window.destroy()

            # Set the value of the item_entry
            item_entry.delete(0, tk.END)
            item_entry.insert(0, item)
            global get_item_rate

            def get_item_rate():
                return row_index, rate
            global receive_item_id

            def receive_item_id():
                return item_id

            # Update the rate in the specified row index
            update_rate(row_index, rate)
            update_count(row_index, count)

            print("Current row, ", row_index)

            # qty_entry = None
            # if table_container.grid_slaves(row=row_index, column=3):
            #     qty_entry = table_container.grid_slaves(row=row_index, column=3)[0]

            # if qty_entry:
            #     qty_entry.focus()

        def show_qty_confirmation(event, table_frame):

            global get_new_qty, return_event

            def get_new_qty():
                return row_index, int(new_qty)

            def return_event():
                return event

            entry = event.widget
            new_qty = entry.get()
            row_index = entry.grid_info()["row"]

            # row_idx, rate = get_item_rate()
            _, category_id = get_category()
            item_id = receive_item_id()

            # Filter only the entry fields for the current row
            row_entries = [widget for widget in table_frame.grid_slaves(
                row=row_index) if isinstance(widget, tk.Entry)]

            # Retrieve the values from the entry fields
            row_data = [entry.get() for entry in row_entries]

            # Reverse the elements of the row_data list
            row_data_reversed = list(reversed(row_data))
            # row_data_reversed[5:]
            row_data_reversed = [
                item for item in row_data_reversed if item != '']
            print("toe_DATA",  row_data_reversed)
            # del row_data_reversed[-1]
            row_data_reversed[2] = int(row_data_reversed[2])
            row_data_reversed[3] = int(row_data_reversed[3])

            row_data_reversed[4] = float(row_data_reversed[4])

            # row_data_reversed[5] = float(row_data_reversed[5])
            print(" row_data_reversed", row_data_reversed)
            # Calculate row amount
            qty = row_data_reversed[3]
            rate = row_data_reversed[4]
            if qty:
                amount = float(qty) * float(rate)
            else:
                amount = 0.0

            # Update amount on Table column
            update_amount(int(row_index), amount)
            del row_data_reversed[-1]
            # Append rows to transaction
            row_data_reversed.append(category_id)
            row_data_reversed.append(item_id)
            row_data_reversed.append(float(amount))

            print(" row_data_reversed222222:", row_data_reversed)
            transactions[row_index] = row_data_reversed

            calculate_dynamic_total(sale_table_container, total_amt)

        def show_amount_confirmation(event, sale_table_container):
            global dialog
            if 'dialog' in globals():
                dialog.destroy()
            dialog = CustomDialog(row_values=transactions)
            dialog.bind('<Escape>', lambda event: destroy(dialog))
            dialog.show()

        class CustomDialog(tk.Toplevel):
            def __init__(self, row_values):
                super().__init__()
                self.row_values = row_values
                self.result = None
                self.title("Qty Confirmation")

                # Create and layout the dialog widgets
                message_label = tk.Label(self, text="Transactions:")
                message_label.pack()

                global receive_message_label

                def receive_message_label():
                    return message_label

                row_values_text = tk.Text(self, height=10, width=50)
                row_values_text.pack()

                # Iterate over the keys of the dictionary and format the values
                for key, values in self.row_values.items():
                    formatted_values = ' '.join(str(value) for value in values)
                    row_values_text.insert(
                        tk.END, f"Item: {key}\n{formatted_values}\n")

                next_category_btn = tk.Button(
                    self, text="Next Category", command=self.handle_next_category)
                next_category_btn.pack(side=tk.LEFT, padx=10)

                next_item_btn = tk.Button(
                    self, text="Next Item", command=self.handle_next_item)
                next_item_btn.pack(side=tk.LEFT, padx=10)

                confirm_btn = tk.Button(
                    self, text="Confirm", command=self.handle_confirm)
                confirm_btn.pack(side=tk.LEFT, padx=10)

                self.focus_force()

                confirm_btn.focus()

                # Get the screen width and height
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()

                # Calculate the x and y coordinates for the window to be centered
                x = int(screen_width / 2 - self.winfo_width() / 2)
                y = int(screen_height / 2 - self.winfo_height() / 2)

                # Set the window's position
                self.geometry(f"+{x}+{y}")

                # Bind left and right arrow keys
                self.bind("<Left>", lambda event: self.focus_previous_button())
                self.bind("<Right>", lambda event: self.focus_next_button())

                # Bind Enter key press to button commands
                next_category_btn.bind(
                    "<Return>", lambda event: next_category_btn.invoke())
                next_item_btn.bind(
                    "<Return>", lambda event: next_item_btn.invoke())
                confirm_btn.bind(
                    "<Return>", lambda event: confirm_btn.invoke())

            def focus_previous_button(self):
                current_focus = self.focus_get()
                buttons = self.get_buttons()

                if current_focus in buttons:
                    current_index = buttons.index(current_focus)
                    previous_index = (current_index - 1) % len(buttons)
                    buttons[previous_index].focus()

            def focus_next_button(self):
                current_focus = self.focus_get()
                buttons = self.get_buttons()

                if current_focus in buttons:
                    current_index = buttons.index(current_focus)
                    next_index = (current_index + 1) % len(buttons)
                    buttons[next_index].focus()

            def get_buttons(self):
                return [widget for widget in self.children.values() if isinstance(widget, tk.Button)]

            def handle_next_category(self):
                self.result = 'Next Category'
                self.destroy()
                # Get the currently focused widget
                event = return_event()
                current_widget = event.widget

                # Get the grid info of the currently focused widget
                current_widget_grid_info = current_widget.grid_info()

                # Get the row index of the currently focused widget
                row_idx = current_widget_grid_info['row']

                last_row_entry = sale_table_container.grid_slaves(
                    row=row_idx, column=1)[0]

                current_last_row = sale_table_container.grid_size()[1] - 1
                if row_idx == current_last_row:
                    if last_row_entry.get() != "":
                        # Generate new rows in the table
                        num_rows = 8  # Specify the number of rows to add
                        for i in range(num_rows):
                            new_row = row_idx + i + 1

                            # Category entry field
                            category_entry = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            category_entry.grid(
                                row=new_row, column=0, padx=10, pady=5)
                            category_entry.bind(
                                '<Return>', open_category_popup)

                            # Item Particular entry field
                            item_entry = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            item_entry.grid(
                                row=new_row, column=1, padx=10, pady=5)
                            item_entry.bind('<Return>', open_item_popup)

                            count_label = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            count_label.grid(
                                row=new_row, column=2, padx=10, pady=5)

                            # Qty entry field
                            qty_entry = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            qty_entry.grid(
                                row=new_row, column=3, padx=10, pady=5)
                            qty_entry.bind('<Return>', lambda event: show_qty_confirmation(
                                event, sale_table_container))

                            # Rate label
                            rate_label = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            rate_label.grid(
                                row=new_row, column=4, padx=10, pady=5)

                            # Amount label
                            amount_label = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            amount_label.grid(
                                row=new_row, column=5, padx=10, pady=5)
                            amount_label.bind(
                                '<Return>', lambda event: show_amount_confirmation(event, sale_table_container))

                        scroll_down()

                # Get the category entry field in the next row
                next_category_entry = sale_table_container.grid_slaves(
                    row=row_idx+1, column=0)[0]
                next_category_entry.focus()

            def handle_next_item(self):
                self.result = 'Next Item'
                self.destroy()
                # Get the currently focused widget
                event = return_event()
                row_idx = event.widget.grid_info()['row']
                category, category_id = get_category()
                find_window = receive_find_window()

                # Check if the last row is filled
                last_row_entry = sale_table_container.grid_slaves(
                    row=row_idx, column=1)[0]

                current_last_row = sale_table_container.grid_size()[1] - 1

                print("last, curr_last::::::", row_idx, current_last_row)

                if row_idx == current_last_row:
                    if last_row_entry.get() != "":
                        # Generate new rows in the table
                        num_rows = 8  # Specify the number of rows to add
                        for i in range(num_rows):
                            new_row = row_idx + i + 1

                            # Category entry field
                            category_entry = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            category_entry.grid(
                                row=new_row, column=0, padx=10, pady=5)
                            category_entry.bind(
                                '<Return>', open_category_popup)

                            # Item Particular entry field
                            item_entry = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            item_entry.grid(
                                row=new_row, column=1, padx=10, pady=5)
                            item_entry.bind('<Return>', open_item_popup)

                            count_label = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            count_label.grid(
                                row=new_row, column=2, padx=10, pady=5)

                            # Qty entry field
                            qty_entry = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            qty_entry.grid(
                                row=new_row, column=3, padx=10, pady=5)
                            qty_entry.bind('<Return>', lambda event: show_qty_confirmation(
                                event, sale_table_container))

                            # Rate label
                            rate_label = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            rate_label.grid(
                                row=new_row, column=4, padx=10, pady=5)

                            # Amount label
                            amount_label = tk.Entry(
                                sale_table_container, font=("Arial", 10))
                            amount_label.grid(
                                row=new_row, column=5, padx=10, pady=5)
                            amount_label.bind(
                                '<Return>', lambda event: show_amount_confirmation(event, sale_table_container))

                        scroll_down()

                next_category_entry = sale_table_container.grid_slaves(
                    row=row_idx+1, column=0)[0]
                next_row_entry = sale_table_container.grid_slaves(
                    row=row_idx+1, column=1)[0]
                next_category = next_row_entry.get()
                if next_category == "":
                    # Call the select_category function with the next category and category ID
                    select_category(category, category_id,
                                    next_category_entry, find_window)
                next_row_entry.focus()

            def handle_confirm(self):
                self.result = 'Confirm'
                # Get the necessary column values to insert in the database
                o = int(memo_number_entry.get())
                user_id = int(user[0])
                date = current_date_label.cget("text")
                customer = client_name_entry.get()

                form_type = type_sale_label.cget("text")
                if form_type == "Sale":
                    # Create a list of tuples for insertion
                    medicine_sales = []
                    unique_item_ids = set()  # Keep track of unique item IDs
                    print("Hola ! transactions", transactions)
                    for row in transactions.keys():
                        row_item_id = transactions[row][5]
                        row_item_quantity = transactions[row][3]
                        print(
                            f"Row item id is: {row_item_id}, Row item quantity is: {row_item_quantity}")
                        if row_item_id not in unique_item_ids:
                            unique_item_ids.add(row_item_id)
                            fixed_entries = [o, user_id, date, customer]
                            for index, col in enumerate(transactions[row]):
                                if index > 2:
                                    fixed_entries.append(col)
                            medicine_sales.append(tuple(fixed_entries))
                            print("mssssssssssssssssssssssss", medicine_sales)
                    try:
                        # Generate new results
                        # Update item count for unique items only
                        for row_idx, row_item_id in enumerate(unique_item_ids):
                            cursor.execute(
                                "SELECT item_count FROM Items WHERE id=?", (row_item_id,))
                            row_item_count = cursor.fetchone()
                            new_item_count = row_item_count[0] - \
                                row_item_quantity
                            cursor.execute(
                                "UPDATE Items SET item_count=? WHERE id=?", (new_item_count, row_item_id))

                            sale_ledgers = [medicine_sales[row_idx][6],
                                            medicine_sales[row_idx][2], medicine_sales[row_idx][4], row_item_count[0], new_item_count]
                            sale_ledgers = [tuple(sale_ledgers)]
                            print("SALE LEDGERS::", sale_ledgers)
                            cursor.executemany(
                                "INSERT INTO ItemLedgers (item_id, date, sale,opening,closing) VALUES (?, ?, ?,?,?)",
                                (sale_ledgers)
                            )

                        print("Executing insert query::::::", row)
                        cursor.executemany(
                            "INSERT INTO MedicineSales (memo_id, user_id, date, customer_name, quantity,category_id, item_id, amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            medicine_sales
                        )

                        message_label = receive_message_label()
                        message_label.configure(
                            text="Data inserted successfully")
                        conn.commit()
                        self.destroy()
                        open_sales_page()
                    except sqlite3.IntegrityError:
                        message_label = receive_message_label()
                        message_label.configure(
                            text="Cannot insert same category and item multiple times in a single invoice")
                if form_type == "Sale-Return":
                    print("sales-return")
                    # Retrieve the document from the table based on the invoice number
                    cursor.execute(
                        "SELECT * FROM MedicineSales WHERE memo_id=?", (o,))
                    rows = cursor.fetchall()
                    # Iterate over the retrieved rows
                    for row_idx, row in enumerate(rows):
                        # Extract the necessary information from the row
                        sale_id = row[0]
                        old_quantity = row[7]
                        old_amount = row[8]
                        item_id = row[6]
                        date = row[3]
                        print("Transactions: ", transactions)
                        for key in transactions.keys():
                            if row_idx+1 == key:
                                updated_quantity = int(
                                    transactions[key][3])
                                print("Uq: ", updated_quantity)
                                print("Oq: ", old_quantity)
                                if updated_quantity <= old_quantity:
                                    # Calculate the difference in quantity
                                    quantity_difference = old_quantity - updated_quantity
                                    cursor.execute(
                                        "SELECT sell_rate FROM Items WHERE id=?", (item_id,))
                                    current_item_rate = cursor.fetchone()[0]
                                    # Update the quantity and amount in the MedicinePurchases table
                                    updated_amount = updated_quantity * current_item_rate
                                    print("UA", updated_amount)
                                    cursor.execute("UPDATE MedicineSales SET quantity=?, amount=? WHERE sale_id=?",
                                                   (updated_quantity, updated_amount, sale_id))

                                    # Update the item count in the Items table based on the quantity difference
                                    cursor.execute(
                                        "SELECT item_count FROM Items WHERE id=?", (item_id,))
                                    current_item_count = cursor.fetchone()[0]
                                    new_item_count = current_item_count + quantity_difference
                                    cursor.execute(
                                        "UPDATE Items SET item_count=? WHERE id=?", (new_item_count, item_id))

                                    sale_ledgers = [
                                        item_id, date, quantity_difference, current_item_count, new_item_count]
                                    sale_ledgers = [tuple(sale_ledgers)]
                                    print("SALE LEDGERS::", sale_ledgers)
                                    cursor.executemany(
                                        "INSERT INTO ItemLedgers (item_id, date, return_sale, opening,closing) VALUES (?, ?, ?,?,?)",
                                        (sale_ledgers)
                                    )
                                    conn.commit()

                                    message_label = receive_message_label()

                                    message_label.configure(
                                        text="Data updated successfully")
                                    # self.destroy()

                                elif updated_quantity > old_quantity:
                                    message_label = receive_message_label()
                                    message_label.configure(
                                        text="Updated quantity should be less than old quantity")
                                    messagebox.showwarning(
                                        "Error", "Updated quantity should be less than old quantity")
                                    return

                    self.destroy()
                    search()

            def show(self):
                self.wait_window(self)
                return self.result

        def delete():
            current_last_row = sale_table_container.grid_size()[1] - 1
            form_type = type_sale_label.cget("text")
            memo_id = int(memo_number_entry.get())
            cursor.execute(
                "SELECT * FROM MedicineSales WHERE memo_id=?", (memo_id,))
            sales = cursor.fetchall()
            cursor.execute(
                '''
                SELECT MedicineSales.sale_id, MedicineSales.customer_name,Categories.category_name,Items.id, Items.item_name,Items.item_count,MedicineSales.quantity, Items.sell_rate, MedicineSales.amount
                FROM MedicineSales
                INNER JOIN Categories ON MedicineSales.category_id = Categories.id
                INNER JOIN Items ON MedicineSales.item_id = Items.id
                WHERE MedicineSales.memo_id = ?
                ''',
                (memo_id,)
            )
            global previous_info
            previous_info = cursor.fetchall()

            confirmation = messagebox.askyesno(
                "Confirmation", "Are you sure you want to delete this row?")
            if confirmation:
                if form_type == "Sale":
                    # Find the focused entry field and clear the text in its row
                    row_index = None  # Initialize the row_index variable
                    for row in range(1, current_last_row + 1):
                        for col in range(6):  # Assuming there are 5 columns
                            widget = sale_table_container.grid_slaves(
                                row=row, column=col)[0]
                            if isinstance(widget, tk.Entry) and widget == main_app.focus_get():
                                row_index = row  # Store the current row index
                                # Clear the text in the columns of the corresponding row
                                for clear_col in range(6):
                                    clear_widget = sale_table_container.grid_slaves(
                                        row=row, column=clear_col)[0]
                                    if isinstance(clear_widget, tk.Entry):
                                        clear_widget.delete(0, tk.END)
                                    elif isinstance(clear_widget, tk.Label):
                                        clear_widget.configure(text="")
                                break  # Break the inner loop once the focused entry widget is found
                        else:
                            continue  # Continue to the next row if the focused entry widget is not found
                        break  # Break the outer loop once the row is cleared

                    # Use the row_index variable for further operations if needed
                    if row_index is not None:
                        if row_index in transactions:
                            del transactions[row_index]
                            print(transactions)
                            # Update the remaining row indices in the transactions dictionary
                            for idx in range(row_index + 1, current_last_row + 1):
                                if idx in transactions:
                                    transactions[idx -
                                                 1] = transactions.pop(idx)

                            calculate_dynamic_total(
                                sale_table_container, total_amt)
                        else:
                            print("Row index not found in transactions dictionary.")

                    else:
                        print("No focused entry widget found.")

                if form_type == "Sale-Return":
                    # Find the focused entry field and clear the text in its row
                    row_index = None  # Initialize the row_index variable
                    for row in range(1, current_last_row + 1):
                        for col in range(6):  # Assuming there are 5 columns
                            widget = sale_table_container.grid_slaves(
                                row=row, column=col)[0]
                            if isinstance(widget, tk.Entry) and widget == main_app.focus_get():
                                row_index = row
                                deleting_row = previous_info[row-1]
                                deleting_row_sales_id = deleting_row[0]
                                deleting_row_item_id = deleting_row[3]
                                deleting_row_qty = deleting_row[6]
                                cursor.execute(
                                    "DELETE FROM MedicineSales WHERE sale_id=?", (deleting_row_sales_id,))

                                cursor.execute(
                                    "SELECT item_count FROM Items WHERE id=?", (deleting_row_item_id,))
                                row_item_count = cursor.fetchone()
                                print(row_item_count)
                                new_item_count = row_item_count[0] + \
                                    deleting_row_qty
                                cursor.execute(
                                    "UPDATE Items SET item_count=? WHERE id=?", (new_item_count,  deleting_row_item_id))
                                conn.commit()
                                search()

        def refresh():
            current_last_row = sale_table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row+1):
                # Clear the text in the columns of the current row
                for col in range(6):  # Assuming there are 5 columns
                    widget = sale_table_container.grid_slaves(
                        row=row, column=col)[0]
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                    elif isinstance(widget, tk.Label):
                        widget.configure(text="")

            # Clear the transactions dictionary
            transactions.clear()
            # Clear previous elements
            client_name_entry.delete(0, tk.END)
            client_name_entry.insert(0, "")
            update_total_amount(0)

        def hard_refresh():
            form_type = type_sale_label.cget("text")
            current_last_row = sale_table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row + 1):
                # Clear the text in the columns of the current row
                for col in range(6):  # Assuming there are 6 columns
                    widget = sale_table_container.grid_slaves(
                        row=row, column=col)[0]
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                    elif isinstance(widget, tk.Label):
                        widget.configure(text="")

            # Clear the transactions dictionary
            transactions.clear()
            type_sale_label.configure(text="Sale")
            client_name_entry.delete(0, tk.END)

            update_total_amount(0)
            # memo_number_entry.delete(0, tk.END)
            # memo_number_entry.insert(0, memo_number)

            if form_type == "Sale-Return":
                search()

        def search():
            refresh()
            type_sale_label.configure(text="Sale-Return")
            s_gap_label.configure(width=11)
            memo_id = int(memo_number_entry.get())
            cursor.execute(
                "SELECT * FROM MedicineSales WHERE memo_id=?", (memo_id,))
            sales = cursor.fetchall()
            cursor.execute(
                '''
                SELECT MedicineSales.customer_name,Categories.category_name,Items.id, Items.item_name,Items.item_count,MedicineSales.quantity, Items.sell_rate, MedicineSales.amount,MedicineSales.date
                FROM MedicineSales
                INNER JOIN Categories ON MedicineSales.category_id = Categories.id
                INNER JOIN Items ON MedicineSales.item_id = Items.id
                WHERE MedicineSales.memo_id = ?
                ''',
                (memo_id,)
            )
            global previous_info
            previous_info = cursor.fetchall()
            print("SDFSAF", previous_info)
            customer_name = previous_info[0][0]
            current_date_pl = previous_info[0][8]
            client_name_entry.delete(0, tk.END)
            client_name_entry.insert(0, customer_name)
            current_date_label.configure(text=current_date_pl)
            for widget in sale_table_container.winfo_children():
                widget.destroy()
            # Create the table headers
            headers = ["Category", "Item Particular",
                       " ", "Qty", "Rate", "Amount"]
            num_columns = len(headers)

            # Adjust the percentage as needed
            table_width = round(window_width * 0.69 * 0.1)
            column_width = round(table_width / num_columns)
            for col, header in enumerate(headers):
                header_label = tk.Label(sale_table_container, text=header, font=(
                    "Arial", 11, "bold"), bg="white", borderwidth=1, relief="solid", width=column_width, padx=10, pady=5)
                header_label.grid(row=0, column=col)

            # Create rows in the table
            total_amount = 0
            for row_index, row_data in enumerate(previous_info):
                row_data = list(row_data)

                indices_to_remove = [0, 2, 8]
                # Sort the indices in descending order
                indices_to_remove.sort(reverse=True)

                for index in indices_to_remove:
                    del row_data[index]
                for col_index, value in enumerate(row_data):
                    entry = tk.Entry(sale_table_container, font=(
                        "Arial", 11), relief="solid", width=column_width, bg="white")
                    entry.insert(0, value)
                    entry.grid(row=row_index + 1,
                               column=col_index, sticky="nsew")
                    if col_index == 0:
                        entry.bind('<Return>', open_category_popup)
                    elif col_index == 1:
                        entry.bind('<Return>', open_item_popup)
                    elif col_index == 3:
                        entry.bind('<Return>', lambda event: show_qty_confirmation(
                            event, sale_table_container))
                    elif col_index == 5:
                        entry.bind('<Return>', lambda event: show_amount_confirmation(
                            event, sale_table_container))
                        total_amount += float(value)

            total_amt.configure(text=total_amount)

        def handle_print():
            sales_print_window = tk.Tk()

            # Get the screen width and height
            screen_width = sales_print_window.winfo_screenwidth()
            screen_height = sales_print_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 800
            window_height = 600
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            sales_print_window.geometry(
                f"{window_width}x{window_height}+{x}+{y}")

            # Set the window background color to white
            sales_print_window.configure(bg="white")

            # Create the header label
            print_header_label = tk.Label(sales_print_window, text="AL-AMIN HOSPITAL (PVT.) LTD.",
                                          font=("Arial", 13, "bold"), bg="white", fg="black")
            print_header_label.pack(pady=3)

            print_body_label = tk.Label(sales_print_window, text="Near A.k. Khan Gate, P.O. Feroz Shah Colony, North Pahartali, Chittagong.\nPhone: 751943, 2770014.",
                                        font=("Arial", 8), bg="white", fg="black")
            print_body_label.pack(pady=3)

            print_s_header_label = tk.Label(sales_print_window, text="Invoice - Sales",
                                            font=("Arial", 12, "bold"), bg="white", fg="black", borderwidth=1, relief="solid")
            print_s_header_label.pack(pady=5)

            # Create the sale container
            pp_container = tk.Frame(
                sales_print_window, bg="white", borderwidth=1, relief="solid")
            pp_container.pack(pady=5)

            # Create the labels and align them using grid

            patient_name = tk.Label(
                pp_container, text=f"Customer: {client_name_entry.get()}", font=("Arial", 9), bg="white")
            patient_name.grid(row=0, column=0, padx=5, pady=2, sticky="e")

            cash_sale = tk.Label(
                pp_container, text="Cash Sale", font=("Arial", 9), bg="white")
            cash_sale.grid(row=0, column=1, padx=5, pady=2, sticky="e")

            year_label = tk.Label(
                pp_container, text=f"Year: {current_year}", font=("Arial", 9), bg="white")
            year_label.grid(row=0, column=2, padx=5, pady=2, sticky="e")

            memo_label = tk.Label(
                pp_container, text=f"Memo ID: {memo_number_entry.get()}", font=("Arial", 9), bg="white")
            memo_label.grid(row=1, column=0, padx=5, pady=2, sticky="e")

            admit_date_label = tk.Label(
                pp_container, text=f"Date: {current_date_label.cget('text')}", font=("Arial", 9), bg="white")
            admit_date_label.grid(row=1, column=1, padx=5, pady=2, sticky="e")

            cash = tk.Label(
                pp_container, text="CASH", font=("Arial", 9), bg="white")
            cash.grid(row=1, column=2, padx=5, pady=2, sticky="e")

            # Create the sale container
            print_container = tk.Frame(
                sales_print_window, bg="white", borderwidth=1, relief="solid")
            print_container.pack(pady=5)

            table_container1 = tk.Frame(print_container, bg="white")
            table_container1.grid(
                row=2, column=0, columnspan=4, padx=10, pady=10)

            # print(len(previous_info))

            for widget in table_container1.winfo_children():
                widget.destroy()
            # Create the table headers
            headers = ["Category", "Item Particular", "Qty", "Rate", "Amount"]
            for col, header in enumerate(headers):
                header_label = tk.Label(table_container1, text=header, font=(
                    "Arial", 9, "bold"), bg="white", borderwidth=1, relief="solid", width=12, padx=10, pady=5)
                header_label.grid(row=0, column=col)

            form_type = type_sale_label.cget('text')

            if form_type == 'Sale-Return':

                # Create rows in the table
                total_amount = 0
                for row_index, row_data in enumerate(previous_info):
                    row_data = list(row_data)

                    indices_to_remove = [0, 2, 4]
                    # Sort the indices in descending order
                    indices_to_remove.sort(reverse=True)

                    for index in indices_to_remove:
                        del row_data[index]
                    for col_index, value in enumerate(row_data):
                        if not col_index == 5:
                            # if not col_index == 0 or col_index == 2 or col_index == 4:  # Column index for "Buy Rate" and "Sale Rate"
                            entry = tk.Label(table_container1, font=(
                                "Arial", 9), width=12, bg="white", borderwidth=1, relief="solid", pady=5)
                            # Set the initial value of the entry field
                            entry.configure(text=value)
                            entry.grid(row=row_index + 1,
                                       column=col_index, sticky="nsew")
                            if col_index == 4:
                                total_amount += float(value)

                total_label = tk.Label(

                    table_container1, text="Total:", font=("Arial", 9), bg="white", width=10, borderwidth=1, relief="solid")
                total_label.grid(row=len(previous_info)+1,
                                 column=3, padx=5, pady=5)

                total_amt = tk.Label(table_container1, font=(
                    "Arial", 9), borderwidth=1, relief="solid", width=10)
                total_amt.grid(row=len(previous_info)+1,
                               column=4, padx=5, pady=5)
                total_amt.configure(text=total_amount)

                footer_container = tk.Frame(print_container, bg="white")
                footer_container.grid(
                    row=3, column=0, columnspan=4, padx=10, pady=10)

                total_amt_w = tk.Label(footer_container, font=(
                    "Arial", 9), width=50)
                total_amt_w.grid(row=num_rows, column=0, pady=5)
                total_amt_w.configure(
                    text=f"In words: {num2words(total_amount)} only.")

            if form_type == 'Sale':
                print("SAKE TRANS", transactions)

                # Create rows in the table
                total_amount = 0
                for row_index, row_data in enumerate(transactions.values()):
                    row_data = list(row_data)

                    indices_to_remove = [2, 4, 5]
                    # Sort the indices in descending order
                    indices_to_remove.sort(reverse=True)

                    for index in indices_to_remove:
                        del row_data[index]
                    for col_index, value in enumerate(row_data):
                        # if not col_index == 5:
                        if not col_index == 3:
                            entry = tk.Label(table_container1, font=(
                                "Arial", 9), width=12, bg="white", borderwidth=1, relief="solid", pady=5)
                            # Set the initial value of the entry field
                            entry.configure(text=value)
                            entry.grid(row=row_index + 1,
                                       column=col_index, sticky="nsew")
                        if col_index == 3:
                            total_amount += float(value)

                            rate = float(value) / row_data[2]

                            rate_entry = tk.Label(table_container1, font=(
                                "Arial", 9), width=12, bg="white", borderwidth=1, relief="solid", pady=5)
                            # Set the initial value of the rate_entry field
                            rate_entry.configure(text=rate)
                            rate_entry.grid(row=row_index + 1,
                                            column=col_index, sticky="nsew")

                            amt_entry = tk.Label(table_container1, font=(
                                "Arial", 9), width=12, bg="white", borderwidth=1, relief="solid", pady=5)
                            # Set the initial value of the amt_entry field
                            amt_entry.configure(text=value)
                            amt_entry.grid(row=row_index + 1,
                                           column=col_index+1, sticky="nsew")

                total_label = tk.Label(

                    table_container1, text="Total:", font=("Arial", 9), bg="white", width=10, borderwidth=1, relief="solid")
                total_label.grid(row=len(transactions)+1,
                                 column=3, padx=5, pady=5)

                total_amt = tk.Label(table_container1, font=(
                    "Arial", 9), borderwidth=1, relief="solid", width=10)
                total_amt.grid(row=len(transactions)+1,
                               column=4, padx=5, pady=5)
                total_amt.configure(text=total_amount)

                footer_container = tk.Frame(print_container, bg="white")
                footer_container.grid(
                    row=3, column=0, columnspan=4, padx=10, pady=10)

                total_amt_w = tk.Label(footer_container, font=(
                    "Arial", 9), width=50)
                total_amt_w.grid(row=num_rows, column=0, pady=5)
                total_amt_w.configure(
                    text=f"In words: {num2words(total_amount)} only.")

            # Create the labels with borders
            sign_container = tk.Frame(print_container, bg="white")
            sign_container.grid(
                row=4, column=0, columnspan=4, padx=10, pady=10)

            received_label = tk.Label(
                sign_container, text="-----------------------\nReceived By", bg="white", font=("Arial", 9), width=12)
            received_label.grid(row=1, column=0, padx=70, pady=30)

            pharmacist_label = tk.Label(
                sign_container, text="-----------------------\nPharmacist", bg="white", font=("Arial", 9), width=12)
            pharmacist_label.grid(row=1, column=1, padx=70, pady=30)

            authorized_label = tk.Label(
                sign_container, text="-----------------------\nAuthorised By", bg="white", font=("Arial", 9), width=12)
            authorized_label.grid(row=1, column=2, padx=70, pady=30)

            # Create the labels with borders
            print_btn_container = tk.Frame(print_container, bg="white")
            print_btn_container.grid(
                row=5, column=3, padx=10, pady=10)

            # Add a button to trigger the print dialog
            print_button = tk.Button(
                print_btn_container, text="Print", command=lambda: print_window_content(sales_print_window))
            print_button.pack(side="left")

            def print_window_content(sales_print_window):
                # Create a new top-level window
                new_window = tk.Toplevel(sales_print_window)

                # Set the window title
                new_window.title("Print Dialog")

                # Set the size of the window
                window_width = 400
                window_height = 300
                screen_width = sales_print_window.winfo_screenwidth()
                screen_height = sales_print_window.winfo_screenheight()

                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2

                new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

                # Create a range frame
                bmw_frame = tk.Frame(new_window)
                bmw_frame.grid(row=0, column=0, pady=10)

                # Add content to the new window
                label_name = tk.Label(bmw_frame, text="Printer Name:")
                label_name.grid(row=0, column=0, pady=10)

                # Fetch available printer names using win32print
                printer_names = [printer[2]
                                 for printer in win32print.EnumPrinters(2)]

                # Create a dropdown with available printer names
                selected_printer = tk.StringVar(bmw_frame)
                dropdown_printers = ttk.Combobox(
                    bmw_frame, textvariable=selected_printer, values=printer_names)
                dropdown_printers.grid(row=0, column=1, pady=10)

                # Set a default printer if available
                if printer_names:
                    selected_printer.set(printer_names[0])

                # Create a range frame
                range_frame = tk.Frame(new_window)
                range_frame.grid(row=1, column=0, pady=10)

                # Add "Print Range" label
                label_print_range = tk.Label(range_frame, text="Print Range:")
                label_print_range.grid(row=0, column=0, pady=5)

                # Add radio buttons for "All" and "Pages" in the same column but different rows
                print_range_var = tk.StringVar(
                    value="All")  # Set an initial value
                radio_all = tk.Radiobutton(
                    range_frame, text="All", variable=print_range_var, value="All")
                radio_all.grid(row=1, column=0, pady=5)

                radio_pages = tk.Radiobutton(
                    range_frame, text="Pages", variable=print_range_var, value="Pages")
                radio_pages.grid(row=1, column=1, pady=5)

                # Manually set the state of one radio button to selected
                radio_all.select()

                # Initially disable the entry widget
                rpe = tk.Entry(range_frame, state=tk.DISABLED)
                rpe.grid(row=1, column=2, pady=5)

                # Callback function to update the entry widget when radio buttons are selected
                def update_entry_widget(*args):
                    if print_range_var.get() == "Pages":
                        rpe.config(state=tk.NORMAL)
                    else:
                        rpe.delete(0, tk.END)
                        rpe.config(state=tk.DISABLED)

                # Bind the callback function to the StringVar
                print_range_var.trace_add('write', update_entry_widget)

                # Function to handle radio button selection
                def radio_button_selected(value):
                    print_range_var.set(value)

                # Attach the radio button selection function to the radio buttons
                radio_all.config(command=lambda: radio_button_selected("All"))
                radio_pages.config(
                    command=lambda: radio_button_selected("Pages"))

                # Create a copies frame
                copies_frame = tk.Frame(new_window)
                copies_frame.grid(row=2, column=0, pady=10)

                # Add content to the copies frame
                label_copies = tk.Label(copies_frame, text="Copies:")
                label_copies.grid(row=0, column=0, pady=5)

                label_num_copies = tk.Label(
                    copies_frame, text="Number of Copies:")
                label_num_copies.grid(row=1, column=0, pady=5)

                # Number entry field with increment and decrement options
                entry_num_copies = tk.Entry(copies_frame, width=5)
                entry_num_copies.grid(row=1, column=1, pady=5)

                entry_num_copies.insert(0, "1")

                btn_increment = tk.Button(
                    copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                btn_increment.grid(row=1, column=2, pady=5, padx=2)

                btn_decrement = tk.Button(
                    copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                # Create OK and Cancel buttons
                btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                    sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                btn_ok.grid(row=3, column=0, pady=10)

                btn_cancel = tk.Button(
                    new_window, text="Cancel", command=new_window.destroy)
                btn_cancel.grid(row=3, column=1, pady=10)

                new_window.focus_force()

                def increment_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(current_value + 1))

                def decrement_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    new_value = max(1, current_value - 1)
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(new_value))

                def bmw_engine(window, print_range_var, page_range, enc):

                    new_window.destroy()
                    time.sleep(1)

                    window.update()
                    x = window.winfo_rootx()
                    y = window.winfo_rooty()
                    x1 = x + window.winfo_width()
                    y1 = y + window.winfo_height()
                    screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
                    screenshot.save(
                        f"page_sales_inv_screenshot.png")
                    print(
                        f"Screenshot of Page sales_inv saved successfully.")
                    img_file = f"page_sales_inv_screenshot.png"
                    loop_completed = False
                    for _ in range(enc):
                        printer_name = selected_printer.get()
                        print(printer_name, img_file)
                        try:
                            subprocess.Popen(
                                ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                            time.sleep(1)
                        except subprocess.CalledProcessError as e:
                            print("Error:", e)
                            time.sleep(1)
                        time.sleep(1)  # Delay after printing

                    loop_completed = True  # Set loop completion flag

                    # Delete the image file after the loop
                    if loop_completed:
                        delete_file(img_file)

                new_window.mainloop()

            # Focus the print window
            sales_print_window.focus_force()

            # Bind keys
            sales_print_window.bind(
                '<Escape>', lambda event: destroy(sales_print_window))

            # sales_print_window.bind_all("<Control-p>", lambda event: print_window_content(sales_print_window))

            sales_print_window.mainloop()

        def update_rate(row_idx, rate):
            # Find the rate label in the third row
            rate_label = sale_table_container.grid_slaves(
                row=row_idx, column=4)[0]

            # Update the rate value
            rate_label.delete(0, tk.END)
            rate_label.insert(0, rate)

        def update_count(row_idx, count):
            # Find the rate label in the third row
            count_label = sale_table_container.grid_slaves(
                row=row_idx, column=2)[0]

            # Update the rate value
            count_label.delete(0, tk.END)
            count_label.insert(0, count)

        def update_amount(row_index, amount):
            # Find the amount label in the third row
            amount_label = sale_table_container.grid_slaves(
                row=row_index, column=5)[0]

            # Update the amount value
            amount_label.delete(0, tk.END)
            amount_label.insert(0, amount)

            amount_label.focus()

        global total_purchase_amt
        # total_purchase_amt = 0

        def update_total_amount(total_amount):
            # Update the amount value
            total_amt.config(text=total_amount)

        clear_frame(body_container)

        # Create the header label
        main_header_label = tk.Label(body_container, text="Medicine Sale",
                                     font=("Arial", 24, "bold"), borderwidth=1, relief='solid', bg="#F5F5DC", fg="black")
        main_header_label.pack(pady=(10, 20))

        btn_container = tk.Frame(body_container, bg="white")
        btn_container.pack()
        delete_button = tk.Button(
            btn_container, text="Delete", width=5, font=2, bg='#C41E3A', fg='white', command=delete)
        delete_button.grid(row=0, column=0, pady=2)

        Refresh_button = tk.Button(
            btn_container, text="Refresh", width=6, font=2, bg='#50C878', fg='white', command=hard_refresh)
        Refresh_button.grid(row=0, column=1, pady=2)

        search_btn = tk.Button(
            btn_container, text="Search", width=6, font=2, bg='#4169E1', fg='white', command=search)
        search_btn.grid(row=0, column=2, pady=2)

        print_btn = tk.Button(
            btn_container, text="Print", width=5, font=2, command=handle_print)
        print_btn.grid(row=0, column=3, pady=2)

        s_container = tk.Frame(body_container, bg="white")
        s_container.pack()

        # Create the "type" label
        ts_label = tk.Label(
            s_container, text="Type: ", font=("Arial", 10), bg="white")
        ts_label.grid(row=1, column=0, pady=5, sticky="w")

        # Create the "type" label
        type_sale_label = tk.Label(
            s_container, text="Sale", font=("Arial", 10), bg="white")
        type_sale_label.grid(row=1, column=1, padx=1, pady=5, columnspan=2)

        # Create a gap of 7 columns
        s_gap_label = tk.Label(s_container, text="", bg="white", width=17)
        s_gap_label.grid(row=1, column=3)

        cd_label = tk.Label(
            s_container, text="Date", font=("Arial", 10), bg="white")
        cd_label.grid(row=1, column=4, padx=2, pady=5)

        # Get the current date
        current_date = datetime.now().strftime("%d-%m-%Y")

        # Create the label with the current date
        current_date_label = ttk.Label(
            s_container, text=current_date, font=("Arial", 10), background="white", borderwidth=1, relief="solid")
        current_date_label.grid(row=1, column=5, padx=20, pady=5, columnspan=2)

        # Create a gap of 7 columns
        d_gap_label = tk.Label(s_container, text="", bg="white", width=16)
        d_gap_label.grid(row=1, column=7)

        # Create the "Invoice No." label
        memo_label = tk.Label(
            s_container, text="Memo ID:", font=("Arial", 10), bg="white")
        memo_label.grid(row=1, column=8, pady=5)

        # Execute the query to fetch all rows from "MedicineSales" table
        cursor.execute("SELECT MAX(memo_id) FROM MedicineSales")

        # Fetch the result
        result = cursor.fetchone()

        # Get the largest invoice ID
        largest_memo_id = result[0] if result[0] is not None else 0

        # Generate o number by adding 1 to the largest invoice ID
        memo_number = largest_memo_id + 1

        # Create the entry field for the invoice number
        memo_number_entry = ttk.Entry(
            s_container, font=("Arial", 10), width=10)
        memo_number_entry.insert(0, memo_number)
        memo_number_entry.grid(row=1, column=9, padx=2, pady=5)

        # Get the current year
        current_year = datetime.now().strftime("%Y")

        b_container = tk.Frame(body_container, bg="white")
        b_container.pack()
        # # Default Text
        default_text_label = ttk.Label(
            b_container, text="To return medicine the customer must bring this slip", font=("Arial", 10, "bold"))
        default_text_label.grid(row=2, column=2, padx=10, pady=5)

        # # Create the "Client Name" label
        client_name_label = tk.Label(
            b_container, text="Customer Name:", font=("Arial", 10), bg="white")
        client_name_label.grid(row=2, column=0, pady=5)

        # # Create the entry field for the client name
        client_name_entry = tk.Entry(b_container, font=("Arial", 10))
        client_name_entry.grid(row=2, column=1, padx=2, pady=5)
        client_name_entry.focus_force()

        sale_table_container = make_table_frame()

        # Create the table headers
        headers = ["Category", "Item Particular", " ", "Qty", "Rate", "Amount"]
        num_columns = len(headers)

        # Adjust the percentage as needed
        table_width = round(window_width * 0.69 * 0.1)
        column_width = round(table_width / num_columns)
        print(column_width)

        for col, header in enumerate(headers):
            header_label = tk.Label(sale_table_container, text=header, font=(
                "Arial", 10, "bold"), bg="white", padx=10, pady=5, relief="solid", width=column_width)
            header_label.grid(row=0, column=col, sticky="nsew")

        # Create the rows
        num_rows = 8  # Specify the number of rows in the table
        for row in range(1, num_rows + 1):
            # Category entry field
            category_entry = tk.Entry(sale_table_container, font=("Arial", 10))
            category_entry.grid(row=row, column=0, padx=10, pady=5)
            # Bind the Return key event
            category_entry.bind('<Return>', open_category_popup)

            # Item Particular entry field
            item_entry = tk.Entry(sale_table_container, font=("Arial", 10))
            item_entry.grid(row=row, column=1, padx=10, pady=5)
            item_entry.bind('<Return>', open_item_popup)

            count_label = tk.Entry(
                sale_table_container, font=("Arial", 10))
            count_label.grid(row=row, column=2, padx=10, pady=5)

            # Qty entry field
            qty_entry = tk.Entry(sale_table_container, font=("Arial", 10))
            qty_entry.grid(row=row, column=3, padx=10, pady=5)
            qty_entry.bind('<Return>', lambda event: show_qty_confirmation(
                event, sale_table_container))

            # Rate label
            rate_label = tk.Entry(
                sale_table_container, font=("Arial", 10))
            rate_label.grid(row=row, column=4, padx=10, pady=5)

            # Amount label
            amount_label = tk.Entry(
                sale_table_container, font=("Arial", 10))
            amount_label.grid(row=row, column=5, padx=10, pady=5)
            amount_label.bind(
                '<Return>', lambda event: show_amount_confirmation(event, sale_table_container))
        # Create a separate frame outside the scrollable frame for fixed elements
        fixed_frame = tk.Frame(body_container, bg="white")
        fixed_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.95)

        medicine_consumption_label = tk.Label(
            fixed_frame, text="Medicine Consumption", font=("Arial", 10), bg="white", width=20, borderwidth=1, relief="solid")
        medicine_consumption_label.grid(
            # Increased padx to 70
            row=0, column=0, padx=(10, 70), pady=10, columnspan=3)

        # Create a gap of 7 columns
        gap_label = tk.Label(fixed_frame, text="", bg="white", width=77)
        gap_label.grid(row=0, column=3)

        total_label = tk.Label(
            fixed_frame, text="Total:", font=("Arial", 10), bg="white", width=10, borderwidth=1, relief="solid")
        total_label.grid(row=0, column=4, padx=10, pady=10)

        total_amt = tk.Label(fixed_frame, font=(
            "Arial", 10), borderwidth=1, relief="solid", width=10)
        total_amt.grid(row=0, column=5, padx=10, pady=10)

        # Bind keys
        client_name_entry.bind(
            '<Return>', lambda event: focus_next_widget(event))

        memo_number_entry.bind(
            '<Return>', lambda event: search())
        print_btn.bind_all("<Control-p>", lambda event: handle_print())
        delete_button.bind_all("<Control-d>", lambda event: delete())
        Refresh_button.bind_all("<Control-r>", lambda event: hard_refresh())
        search_btn.bind_all("<Control-s>", lambda event: search())

    # *****************************************************#                    # *****************************************************#
    # ********** Sale Page End ****************************#                    # ********** Sale Page End ****************************#
    # *****************************************************#                    # *****************************************************#

    # *****************************************************#                    # *****************************************************#
    # ********** Report Page ******************************#                    # ********** Report Page ******************************#
    # *****************************************************#                    # *****************************************************#

    def open_report_page():

        def open_memo_summarized():
            sales_print_window = tk.Tk()

            # Get the screen width and height
            screen_width = sales_print_window.winfo_screenwidth()
            screen_height = sales_print_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 900
            window_height = 600
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            # Set the window size and position
            sales_print_window.geometry(
                f"{window_width}x{window_height}+{x}+{y}")

            # Set the window background color to white
            sales_print_window.configure(bg="white")

            # Create the header label
            print_header_label = tk.Label(sales_print_window, text="MEMO SALE SUMMARIZED",
                                          font=("Arial", 12, "bold"), bg="white", fg="black")
            print_header_label.pack(pady=10)
            current_date = date_entry.get()
            date_label = tk.Label(sales_print_window, text=f"Date: {current_date}",
                                  font=("Arial", 12), bg="white", fg="black", borderwidth=1, relief="solid")
            date_label.pack(pady=10)
            cursor.execute('''
                SELECT memo_id, SUM(amount) AS total_amount
                FROM MedicineSales
                WHERE date = ?
                GROUP BY memo_id''', (current_date,))

            rows = cursor.fetchall()
            print("hola!", rows)
            table_container1 = tk.Frame(sales_print_window, bg="white")
            table_container1.pack(padx=10, pady=10)

            rows_per_page = 13
            total_rows = len(rows)
            # Calculate total number of pages
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page

            current_page = 1
            start_index = 0
            end_index = rows_per_page

            def next_page():
                nonlocal current_page, start_index, end_index
                if current_page < total_pages:
                    current_page += 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    page_info.configure(
                        text=f"Page {current_page} of {total_pages}")
                    update_table()

            def previous_page():
                nonlocal current_page, start_index, end_index
                if current_page > 1:
                    current_page -= 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    page_info.configure(
                        text=f"Page {current_page} of {total_pages}")
                    update_table()

            def update_table():
                for widget in table_container1.grid_slaves():
                    widget.grid_forget()

                headers = ["Type", "Memo No", "Amount"]
                for col, header in enumerate(headers):
                    header_label = tk.Label(table_container1, text=header, font=(
                        "Arial", 10, "bold"), bg="white", borderwidth=1, width=20, relief="solid", padx=10, pady=5)
                    header_label.grid(row=0, column=col)

                start_index = (current_page - 1) * rows_per_page
                end_index = min(start_index + rows_per_page, total_rows)

                type_label = tk.Label(table_container1, text="CASH SALE", font=(
                    "Arial", 10, "bold"), bg="white", borderwidth=1, width=20, relief="solid", padx=10, pady=5)
                type_label.grid(row=1, column=0,
                                rowspan=len(rows), sticky="nsew")
                for row, data in enumerate(rows[start_index:end_index], start=1):
                    for col, col_data in enumerate(data):
                        if col == 0:
                            m_label = tk.Label(table_container1, text=col_data, font=(
                                "Arial", 10), bg="white", borderwidth=1, width=20, relief="solid", padx=10, pady=5)
                        if col == 1:
                            m_label = tk.Label(table_container1, text=col_data, font=(
                                "Arial", 10), bg="white", borderwidth=1, width=20, relief="solid", padx=10, pady=5)
                        m_label.grid(row=row, column=col+1)

                current_amt = 0
                for value in rows:
                    current_amt += value[1]

                total_amt_label = tk.Label(table_container1, text=f"Total: {current_amt}", font=(
                    "Arial", 10), bg="white", borderwidth=1, width=20, relief="solid", padx=10, pady=5)
                total_amt_label.grid(row=len(rows)+1, column=2)
                page_info.configure(
                    text=f"Page {current_page} of {total_pages}")
            # Add pagination buttons
            pagination_frame = tk.Frame(sales_print_window, bg="white")
            pagination_frame.pack(pady=10)

            previous_button = tk.Button(
                pagination_frame, text="Previous", command=previous_page)
            previous_button.pack(side="left")

            page_info = tk.Label(pagination_frame, text=f"Page {current_page} of {total_pages}", font=(
                "Arial", 10), bg="white", fg="black")
            page_info.pack(side="left", padx=10)

            next_button = tk.Button(
                pagination_frame, text="Next", command=next_page)
            next_button.pack(side="left")

            # Create an Entry widget for the page number
            page_entry = ttk.Entry(pagination_frame, width=7)
            page_entry.pack(side="left")

            # Add a button to trigger the print dialog
            print_button = tk.Button(
                pagination_frame, text="Print", command=lambda: print_window_content(sales_print_window))
            print_button.pack(side="left")

            def print_window_content(sales_print_window):
                # Create a new top-level window
                new_window = tk.Toplevel(sales_print_window)

                # Set the window title
                new_window.title("Print Dialog")

                # Set the size of the window
                window_width = 400
                window_height = 300
                screen_width = sales_print_window.winfo_screenwidth()
                screen_height = sales_print_window.winfo_screenheight()

                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2

                new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

                # Create a range frame
                bmw_frame = tk.Frame(new_window)
                bmw_frame.grid(row=0, column=0, pady=10)

                # Add content to the new window
                label_name = tk.Label(bmw_frame, text="Printer Name:")
                label_name.grid(row=0, column=0, pady=10)

                # Fetch available printer names using win32print
                printer_names = [printer[2]
                                 for printer in win32print.EnumPrinters(2)]

                # Create a dropdown with available printer names
                selected_printer = tk.StringVar(bmw_frame)
                dropdown_printers = ttk.Combobox(
                    bmw_frame, textvariable=selected_printer, values=printer_names)
                dropdown_printers.grid(row=0, column=1, pady=10)

                # Set a default printer if available
                if printer_names:
                    selected_printer.set(printer_names[0])

                # Create a range frame
                range_frame = tk.Frame(new_window)
                range_frame.grid(row=1, column=0, pady=10)

                # Add "Print Range" label
                label_print_range = tk.Label(range_frame, text="Print Range:")
                label_print_range.grid(row=0, column=0, pady=5)

                # Add radio buttons for "All" and "Pages" in the same column but different rows
                print_range_var = tk.StringVar(
                    value="All")  # Set an initial value
                radio_all = tk.Radiobutton(
                    range_frame, text="All", variable=print_range_var, value="All")
                radio_all.grid(row=1, column=0, pady=5)

                radio_pages = tk.Radiobutton(
                    range_frame, text="Pages", variable=print_range_var, value="Pages")
                radio_pages.grid(row=1, column=1, pady=5)

                # Manually set the state of one radio button to selected
                radio_all.select()

                # Initially disable the entry widget
                rpe = tk.Entry(range_frame, state=tk.DISABLED)
                rpe.grid(row=1, column=2, pady=5)

                # Callback function to update the entry widget when radio buttons are selected
                def update_entry_widget(*args):
                    if print_range_var.get() == "Pages":
                        rpe.config(state=tk.NORMAL)
                    else:
                        rpe.delete(0, tk.END)
                        rpe.config(state=tk.DISABLED)

                # Bind the callback function to the StringVar
                print_range_var.trace_add('write', update_entry_widget)

                # Function to handle radio button selection
                def radio_button_selected(value):
                    print_range_var.set(value)

                # Attach the radio button selection function to the radio buttons
                radio_all.config(command=lambda: radio_button_selected("All"))
                radio_pages.config(
                    command=lambda: radio_button_selected("Pages"))

                # Create a copies frame
                copies_frame = tk.Frame(new_window)
                copies_frame.grid(row=2, column=0, pady=10)

                # Add content to the copies frame
                label_copies = tk.Label(copies_frame, text="Copies:")
                label_copies.grid(row=0, column=0, pady=5)

                label_num_copies = tk.Label(
                    copies_frame, text="Number of Copies:")
                label_num_copies.grid(row=1, column=0, pady=5)

                # Number entry field with increment and decrement options
                entry_num_copies = tk.Entry(copies_frame, width=5)
                entry_num_copies.grid(row=1, column=1, pady=5)

                entry_num_copies.insert(0, "1")

                btn_increment = tk.Button(
                    copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                btn_increment.grid(row=1, column=2, pady=5, padx=2)

                btn_decrement = tk.Button(
                    copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                # Create OK and Cancel buttons
                btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                    sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                btn_ok.grid(row=3, column=0, pady=10)

                btn_cancel = tk.Button(
                    new_window, text="Cancel", command=new_window.destroy)
                btn_cancel.grid(row=3, column=1, pady=10)

                def increment_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(current_value + 1))

                def decrement_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    new_value = max(1, current_value - 1)
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(new_value))

                def bmw_engine(window, print_range_var, page_range, enc):
                    if print_range_var == 'Pages':
                        try:
                            new_window.destroy()
                            time.sleep(1)
                            print('toredaaa')
                            print(print_range_var)
                            # page_range = page_entry.get()
                            pages_to_capture = []

                            # Parse the page range input
                            for part in page_range.split(','):
                                if '-' in part:
                                    start, end = map(int, part.split('-'))
                                    pages_to_capture.extend(
                                        range(start, end + 1))
                                else:
                                    pages_to_capture.append(int(part))

                            # Ensure all page numbers are within valid bounds
                            invalid_pages = [page for page in pages_to_capture if not (
                                1 <= page <= total_pages)]
                            if invalid_pages:
                                print(
                                    f"Invalid page numbers: {', '.join(map(str, invalid_pages))}. Please enter valid page numbers.")
                                return

                            # Iterate over the specified pages and take screenshots
                            for page_number in pages_to_capture:
                                # Update the current_page variable and update the table
                                nonlocal current_page, start_index, end_index
                                current_page = page_number
                                start_index = (
                                    current_page - 1) * rows_per_page
                                end_index = min(
                                    start_index + rows_per_page, total_rows)
                                update_table()

                                # Take a screenshot of the current page
                                window.update()
                                x = window.winfo_rootx()
                                y = window.winfo_rooty()
                                x1 = x + window.winfo_width()
                                y1 = y + window.winfo_height()

                                screenshot = ImageGrab.grab(
                                    bbox=(x, y, x1, y1))
                                screenshot.save(
                                    f"page_{page_number}_screenshot.png")
                                print(
                                    f"Screenshot of Page {page_number} saved successfully.")

                                img_file = f"page_{page_number}_screenshot.png"
                                for _ in range(enc):
                                    printer_name = selected_printer.get()
                                    print(printer_name, img_file)

                                    try:
                                        subprocess.Popen(
                                            ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                        time.sleep(1)
                                    except subprocess.CalledProcessError as e:
                                        print("Error:", e)
                                        time.sleep(1)

                                    time.sleep(1)  # Delay after printing

                                loop_completed = True  # Set loop completion flag

                                # Delete the image file after the loop
                                if loop_completed:
                                    delete_file(img_file)

                        except ValueError:
                            print(
                                "Invalid page range format. Please enter a valid page range.")

                    elif print_range_var == 'All':
                        new_window.destroy()
                        time.sleep(1)
                        for page_number in range(1, total_pages+1):
                            # Update the current_page variable and update the table
                            current_page = page_number
                            start_index = (current_page - 1) * rows_per_page
                            end_index = min(
                                start_index + rows_per_page, total_rows)
                            update_table()

                            # Take a screenshot of the current page
                            window.update()
                            x = window.winfo_rootx()
                            y = window.winfo_rooty()
                            x1 = x + window.winfo_width()
                            y1 = y + window.winfo_height()

                            screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
                            screenshot.save(
                                f"page_{page_number}_screenshot.png")

                            print(
                                f"Screenshot of Page {page_number} saved successfully.")

                            img_file = f"page_{page_number}_screenshot.png"

                            for _ in range(enc):
                                printer_name = selected_printer.get()
                                print(printer_name, img_file)
                                try:
                                    subprocess.Popen(
                                        ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                    time.sleep(1)
                                except subprocess.CalledProcessError as e:
                                    print("Error:", e)
                                    time.sleep(1)
                                time.sleep(1)

                            loop_completed = True  # Set loop completion flag

                            # Delete the image file after the loop
                            if loop_completed:
                                delete_file(img_file)

                new_window.focus_force()
                new_window.mainloop()

            def nav_page(page_no):
                if page_no < current_page:
                    for i in range(current_page-page_no):
                        previous_page()
                elif page_no > current_page:
                    for i in range(page_no - current_page):
                        next_page()
            # Bind the <Return> event to load the entered page
            page_entry.bind('<Return>', lambda event: nav_page(
                int(page_entry.get())))
            update_table()

            # main_app.bind("<Down>", focus_next_widget)
            sales_print_window.bind("<Right>", focus_next_widget)
            # main_app.bind("<Up>", focus_previous_widget)
            sales_print_window.bind("<Left>", focus_previous_widget)
            # main_app.bind("<Return>", click_selected_widget)
            previous_button.bind(
                "<Return>", lambda event: previous_button.invoke())
            next_button.bind(
                "<Return>", lambda event: next_button.invoke())
            sales_print_window.focus_force()
            # next_button.focus()
            sales_print_window.mainloop()

        def open_statement_page():
            sales_print_window = tk.Tk()
            # Get the screen width and height
            screen_width = sales_print_window.winfo_screenwidth()
            screen_height = sales_print_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 900
            window_height = 600
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            # Set the window size and position
            sales_print_window.geometry(
                f"{window_width}x{window_height}+{x}+{y}")

            # Set the window background color to white
            sales_print_window.configure(bg="white")

            # Create the header label
            print_header_label = tk.Label(sales_print_window, text="CASH SALE STATEMENT",
                                          font=("Arial", 12, "bold"), bg="white", fg="black")
            print_header_label.pack(pady=10)
            current_date = datetime.now().strftime("%d-%m-%Y")
            date_label = tk.Label(sales_print_window, text=f"Date: {current_date}",
                                  font=("Arial", 12), bg="white", fg="black", borderwidth=1, relief="solid")
            date_label.pack(pady=10)

            cursor.execute('''
                        SELECT Users.username, MedicineSales.memo_id, Items.item_name,MedicineSales.quantity, Items.sell_rate , MedicineSales.amount FROM MedicineSales 
                        INNER JOIN Items ON MedicineSales.item_id = Items.id 
                        INNER JOIN Users ON MedicineSales.user_id= Users.id  
                        WHERE MedicineSales.date=?''', (current_date,))

            rows = cursor.fetchall()

            table_container1 = tk.Frame(sales_print_window, bg="white")
            table_container1.pack(padx=10, pady=10)
            rows_per_page = 13
            total_rows = len(rows)
            # Calculate total number of pages
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page

            current_page = 1
            start_index = 0
            end_index = rows_per_page

            def next_page():
                nonlocal current_page, start_index, end_index
                if current_page < total_pages:
                    current_page += 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    page_info.configure(
                        text=f"Page {current_page} of {total_pages}")
                    update_table()

            def previous_page():
                nonlocal current_page, start_index, end_index
                if current_page > 1:
                    current_page -= 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    page_info.configure(
                        text=f"Page {current_page} of {total_pages}")
                    update_table()

            def update_table():
                for widget in table_container1.grid_slaves():
                    widget.grid_forget()

                headers = ["Transaction By", "Memo ID",
                           "Item Particular", "Qty", "Rate", "Amount"]

                for col, header in enumerate(headers):
                    header_label = tk.Label(table_container1, text=header, font=(
                        "Arial", 10, "bold"), bg="white", borderwidth=1, relief="solid", padx=10, pady=5, width=13)
                    header_label.grid(row=0, column=col, sticky="nsew")

                previous_memo_id = None
                total = 0  # To store the total amount for each memo_id
                row = 1  # Start from row 1

                for sale in rows[start_index:end_index]:
                    memo_id = sale[1]
                    # Get the amount value from the last column
                    amount = sale[-1]
                    user_id = sale[0]

                    if memo_id != previous_memo_id:
                        if previous_memo_id is not None:
                            row += 1  # Move to the next row
                            total_label = tk.Label(table_container1, text=f"Total: {total}", font=(
                                "Arial", 10, "bold"), bg="white", padx=10, pady=5, width=13)
                            total_label.grid(row=row, column=len(
                                headers)-1, sticky="nsew")
                            total = 0  # Reset the total for the new memo_id
                            row += 1  # Move to the next row

                        trans_label = tk.Label(table_container1, text=user_id, font=(
                            "Arial", 10), bg="white", padx=10, pady=5, borderwidth=1, relief="solid", width=13)
                        trans_label.grid(row=row, column=0, sticky="nsew")

                        memo_id_label = tk.Label(table_container1, text=memo_id, font=(
                            "Arial", 10), bg="white", padx=10, pady=5, borderwidth=1, relief="solid", width=13)
                        memo_id_label.grid(row=row, column=1, sticky="nsew")
                        previous_memo_id = memo_id

                    total += amount  # Add the amount to the total for the current memo_id

                    for col, value in enumerate(sale[2:], start=1):
                        data_label = tk.Label(table_container1, text=value, font=(
                            "Arial", 10), bg="white", borderwidth=1, relief="solid", padx=10, pady=5, width=13)
                        data_label.grid(row=row, column=col+1, sticky="nsew")

                    row += 1  # Move to the next row

                # Add total for the last memo_id
                if previous_memo_id is not None:
                    row += 1  # Move to the next row
                    total_label = tk.Label(table_container1, text=f"Total: {total}", font=(
                        "Arial", 10, "bold"), bg="white", padx=10, pady=5, width=13)
                    total_label.grid(row=row, column=len(
                        headers)-1, sticky="nsew")

                # Configure row and column weights to make the table resizable
                for i in range(row + 1):
                    table_container1.grid_rowconfigure(i, weight=1)
                for i in range(len(headers)):
                    table_container1.grid_columnconfigure(i, weight=1)

            # Add pagination buttons
            pagination_frame = tk.Frame(sales_print_window, bg="white")
            pagination_frame.pack(pady=10)

            previous_button = tk.Button(
                pagination_frame, text="Previous", command=previous_page)
            previous_button.pack(side="left")

            page_info = tk.Label(pagination_frame, text=f"Page {current_page} of {total_pages}", font=(
                "Arial", 10), bg="white", fg="black")
            page_info.pack(side="left", padx=10)

            next_button = tk.Button(
                pagination_frame, text="Next", command=next_page)
            next_button.pack(side="left")

            # Create an Entry widget for the page number
            page_entry = ttk.Entry(pagination_frame, width=7)
            page_entry.pack(side="left")

            # Add a button to trigger the print dialog
            print_button = tk.Button(
                pagination_frame, text="Print", command=lambda: print_window_content(sales_print_window))
            print_button.pack(side="left")

            def print_window_content(sales_print_window):
                # Create a new top-level window
                new_window = tk.Toplevel(sales_print_window)

                # Set the window title
                new_window.title("Print Dialog")

                # Set the size of the window
                window_width = 400
                window_height = 300
                screen_width = sales_print_window.winfo_screenwidth()
                screen_height = sales_print_window.winfo_screenheight()

                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2

                new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

                # Create a range frame
                bmw_frame = tk.Frame(new_window)
                bmw_frame.grid(row=0, column=0, pady=10)

                # Add content to the new window
                label_name = tk.Label(bmw_frame, text="Printer Name:")
                label_name.grid(row=0, column=0, pady=10)

                # Fetch available printer names using win32print
                printer_names = [printer[2]
                                 for printer in win32print.EnumPrinters(2)]

                # Create a dropdown with available printer names
                selected_printer = tk.StringVar(bmw_frame)
                dropdown_printers = ttk.Combobox(
                    bmw_frame, textvariable=selected_printer, values=printer_names)
                dropdown_printers.grid(row=0, column=1, pady=10)

                # Set a default printer if available
                if printer_names:
                    selected_printer.set(printer_names[0])

                # Create a range frame
                range_frame = tk.Frame(new_window)
                range_frame.grid(row=1, column=0, pady=10)

                # Add "Print Range" label
                label_print_range = tk.Label(range_frame, text="Print Range:")
                label_print_range.grid(row=0, column=0, pady=5)

                # Add radio buttons for "All" and "Pages" in the same column but different rows
                print_range_var = tk.StringVar(
                    value="All")  # Set an initial value
                radio_all = tk.Radiobutton(
                    range_frame, text="All", variable=print_range_var, value="All")
                radio_all.grid(row=1, column=0, pady=5)

                radio_pages = tk.Radiobutton(
                    range_frame, text="Pages", variable=print_range_var, value="Pages")
                radio_pages.grid(row=1, column=1, pady=5)

                # Manually set the state of one radio button to selected
                radio_all.select()

                # Initially disable the entry widget
                rpe = tk.Entry(range_frame, state=tk.DISABLED)
                rpe.grid(row=1, column=2, pady=5)

                # Callback function to update the entry widget when radio buttons are selected
                def update_entry_widget(*args):
                    if print_range_var.get() == "Pages":
                        rpe.config(state=tk.NORMAL)
                    else:
                        rpe.delete(0, tk.END)
                        rpe.config(state=tk.DISABLED)

                # Bind the callback function to the StringVar
                print_range_var.trace_add('write', update_entry_widget)

                # Function to handle radio button selection
                def radio_button_selected(value):
                    print_range_var.set(value)

                # Attach the radio button selection function to the radio buttons
                radio_all.config(command=lambda: radio_button_selected("All"))
                radio_pages.config(
                    command=lambda: radio_button_selected("Pages"))

                # Create a copies frame
                copies_frame = tk.Frame(new_window)
                copies_frame.grid(row=2, column=0, pady=10)

                # Add content to the copies frame
                label_copies = tk.Label(copies_frame, text="Copies:")
                label_copies.grid(row=0, column=0, pady=5)

                label_num_copies = tk.Label(
                    copies_frame, text="Number of Copies:")
                label_num_copies.grid(row=1, column=0, pady=5)

                # Number entry field with increment and decrement options
                entry_num_copies = tk.Entry(copies_frame, width=5)
                entry_num_copies.grid(row=1, column=1, pady=5)

                entry_num_copies.insert(0, "1")

                btn_increment = tk.Button(
                    copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                btn_increment.grid(row=1, column=2, pady=5, padx=2)

                btn_decrement = tk.Button(
                    copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                # Create OK and Cancel buttons
                btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                    sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                btn_ok.grid(row=3, column=0, pady=10)

                btn_cancel = tk.Button(
                    new_window, text="Cancel", command=new_window.destroy)
                btn_cancel.grid(row=3, column=1, pady=10)

                def increment_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(current_value + 1))

                def decrement_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    new_value = max(1, current_value - 1)
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(new_value))

                def bmw_engine(window, print_range_var, page_range, enc):
                    if print_range_var == 'Pages':
                        try:
                            new_window.destroy()
                            time.sleep(1)
                            print('toredaaa')
                            print(print_range_var)
                            # page_range = page_entry.get()
                            pages_to_capture = []

                            # Parse the page range input
                            for part in page_range.split(','):
                                if '-' in part:
                                    start, end = map(int, part.split('-'))
                                    pages_to_capture.extend(
                                        range(start, end + 1))
                                else:
                                    pages_to_capture.append(int(part))

                            # Ensure all page numbers are within valid bounds
                            invalid_pages = [page for page in pages_to_capture if not (
                                1 <= page <= total_pages)]
                            if invalid_pages:
                                print(
                                    f"Invalid page numbers: {', '.join(map(str, invalid_pages))}. Please enter valid page numbers.")
                                return

                            # Iterate over the specified pages and take screenshots
                            for page_number in pages_to_capture:
                                # Update the current_page variable and update the table
                                nonlocal current_page, start_index, end_index
                                current_page = page_number
                                start_index = (
                                    current_page - 1) * rows_per_page
                                end_index = min(
                                    start_index + rows_per_page, total_rows)
                                update_table()

                                # Take a screenshot of the current page
                                window.update()
                                x = window.winfo_rootx()
                                y = window.winfo_rooty()
                                x1 = x + window.winfo_width()
                                y1 = y + window.winfo_height()

                                screenshot = ImageGrab.grab(
                                    bbox=(x, y, x1, y1))
                                screenshot.save(
                                    f"page_{page_number}_screenshot.png")
                                print(
                                    f"Screenshot of Page {page_number} saved successfully.")

                                img_file = f"page_{page_number}_screenshot.png"
                                for _ in range(enc):
                                    printer_name = selected_printer.get()
                                    print(printer_name, img_file)

                                    try:
                                        subprocess.Popen(
                                            ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                        time.sleep(1)
                                    except subprocess.CalledProcessError as e:
                                        print("Error:", e)
                                        time.sleep(1)
                                    time.sleep(1)

                                loop_completed = True  # Set loop completion flag

                                # Delete the image file after the loop
                                if loop_completed:
                                    delete_file(img_file)

                        except ValueError:
                            print(
                                "Invalid page range format. Please enter a valid page range.")

                    elif print_range_var == 'All':
                        new_window.destroy()
                        time.sleep(1)
                        for page_number in range(1, total_pages+1):
                            # Update the current_page variable and update the table
                            current_page = page_number
                            start_index = (current_page - 1) * rows_per_page
                            end_index = min(
                                start_index + rows_per_page, total_rows)
                            update_table()

                            # Take a screenshot of the current page
                            window.update()
                            x = window.winfo_rootx()
                            y = window.winfo_rooty()
                            x1 = x + window.winfo_width()
                            y1 = y + window.winfo_height()

                            screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
                            screenshot.save(
                                f"page_{page_number}_screenshot.png")

                            print(
                                f"Screenshot of Page {page_number} saved successfully.")

                            img_file = f"page_{page_number}_screenshot.png"

                            for _ in range(enc):
                                printer_name = selected_printer.get()
                                print(printer_name, img_file)
                                try:
                                    subprocess.Popen(
                                        ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                    time.sleep(1)
                                except subprocess.CalledProcessError as e:
                                    print("Error:", e)
                                    time.sleep(1)
                                time.sleep(1)

                            loop_completed = True  # Set loop completion flag

                            # Delete the image file after the loop
                            if loop_completed:
                                delete_file(img_file)

                new_window.focus_force()
                new_window.mainloop()

            def nav_page(page_no):
                if page_no < current_page:
                    for i in range(current_page-page_no):
                        previous_page()
                elif page_no > current_page:
                    for i in range(page_no - current_page):
                        next_page()
            # Bind the <Return> event to load the entered page
            page_entry.bind('<Return>', lambda event: nav_page(
                int(page_entry.get())))
            update_table()
            # main_app.bind("<Down>", focus_next_widget)
            sales_print_window.bind("<Right>", focus_next_widget)
            # main_app.bind("<Up>", focus_previous_widget)
            sales_print_window.bind("<Left>", focus_previous_widget)
            # main_app.bind("<Return>", click_selected_widget)
            previous_button.bind(
                "<Return>", lambda event: previous_button.invoke())
            next_button.bind(
                "<Return>", lambda event: next_button.invoke())
            sales_print_window.focus_force()
            sales_print_window.mainloop()

        def open_item_popup_reports(event):
            # Create a new window
            item = event.widget.get()
            item_entry = event.widget
            row_index = event.widget.grid_info()['row']
            print("haaaaaaaaaaaaaaaaaaaaaaaa", row_index)
            find_window = tk.Toplevel(main_app)
            find_window.title("Find")

            # Create the "Find" label
            find_label = tk.Label(
                find_window, text="Find:", font=("Arial", 10))
            find_label.grid(row=0, column=0, padx=10, pady=10)

            # Create the entry field
            find_entry = tk.Entry(find_window, font=("Arial", 10))
            find_entry.grid(row=0, column=1, padx=10, pady=10)

            # Give the main_app window focus
            find_window.focus_force()

            # Set the value of find_entry to the supplier name
            find_entry.insert(0, item)

            # Create or update the table container
            if hasattr(find_window, "table_container"):
                table_container = find_window.table_container
                # Clear existing data
                table_container.delete(*table_container.get_children())
            else:
                table_container = ttk.Treeview(find_window)
                table_container.grid(
                    row=1, column=0, columnspan=2, padx=10, pady=10)
                find_window.table_container = table_container

                column_names = ["Item Name", "Item ID"]

                # Configure the table container
                table_container["columns"] = column_names
                table_container["show"] = "headings"

                # Set the column properties
                for column in column_names:
                    table_container.heading(column, text=column)
                    table_container.column(column, width=100)

                # Bind arrow keys and Enter key
                table_container.bind('<Up>', lambda event: select_previous_value(
                    table_container, find_entry))
                table_container.bind(
                    '<Down>', lambda event: select_next_value(table_container))
                table_container.bind('<Return>', lambda event: select_item_from_table_reports(
                    table_container, find_window, item_entry, row_index))
                # Bind Enter key on find_entry to click on the first item
                find_entry.bind('<Down>', lambda event: click_first_item(
                    table_container, find_window))

            item_name = item_name_entry.get()

            # Execute the filtered database query
            # SELECT Categories.category_name, Items.id, Items.item_name, items.item_count,  Items.sell_rate
            cursor.execute(
                '''
                SELECT item_name,id FROM Items
                WHERE item_name LIKE ?
                ''',
                ('%' + item_name + '%',)
            )
            results = cursor.fetchall()

            # Insert the results into the table container
            insert_results_into_table(table_container, results)

            # Update results upon further querying
            find_entry.bind('<KeyRelease>', lambda event: update_item_results_reports(
                table_container, find_entry, item_entry, find_window, row_index))
            # Destroy window upon hitting esc
            find_window.bind('<Escape>', lambda event: destroy(find_window))
            find_entry.focus_force()

        def update_item_results_reports(table_container, find_entry, item_entry, find_window, row_index):
            # Get the new supplier name
            new_item = find_entry.get()
            # Generate new results
            cursor.execute(
                '''
                SELECT item_name,id FROM Items
                WHERE item_name LIKE ?
                ''',
                ('%' + new_item + '%',)
            )
            new_results = cursor.fetchall()

            # Update the table container with new results
            insert_results_into_table(table_container, new_results)
            # Bind Enter key on table_container to select the category
            table_container.bind('<Return>', lambda event: select_item_from_table_reports(
                table_container, find_window, item_entry))

        def select_item_from_table_reports(table_container, find_window, item_entry):
            selected_item = table_container.selection()
            if selected_item:
                item = table_container.item(selected_item)["values"][0]
                item_id = table_container.item(selected_item)["values"][1]
                select_item_reports(item, item_id, item_entry, find_window)

        def select_item_reports(item, item_id, item_entry, find_window):
            find_window.destroy()

            # Set the value of the item_entry
            item_entry.delete(0, tk.END)
            item_entry.insert(0, item)
            item_id_label.configure(text=item_id)

        def open_item_ledger():
            # Create a new window
            window = tk.Toplevel()

            # Set the window title
            window.title("Item Ledger")

            # Calculate the width and height of the window
            window_width = 1000
            window_height = 600
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))

            # Set the window size and position
            window.geometry(
                f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

            # Create the header label
            header_label = tk.Label(
                window, text="Item Ledger", font=("Arial", 14, "bold"))
            header_label.grid(row=0, column=0, pady=10)
            # Create a range frame
            body_frame = tk.Frame(window)
            body_frame.grid(row=1, column=0, pady=10)

            item_id = int(item_id_label.cget("text"))
            # Create the item ID label with border
            item_id_l_label = tk.Label(
                body_frame, text=f"Item ID: {item_id}", borderwidth=1, relief="solid", padx=10, pady=10)
            item_id_l_label.grid(row=1, column=0, padx=10, pady=10)

            item_name = item_name_entry.get()
            # Create the item name label with border
            item_name_l_label = tk.Label(
                body_frame, text=f"Item Name: {item_name}", borderwidth=1, relief="solid", padx=10, pady=10)
            item_name_l_label.grid(row=1, column=1, padx=10, pady=10)

            start_date = start_date_entry.get()
            end_date = end_date_entry.get()

            start_date_label = tk.Label(
                body_frame, text=f"{start_date} to {end_date}", borderwidth=1, relief="solid", padx=10, pady=10)
            start_date_label.grid(row=1, column=6, padx=10, pady=10)

            query = "SELECT ledger_id, date, opening, purchase, sale, return_sale, return_buy, issue, closing FROM ItemLedgers WHERE item_id=? AND date >= ? AND date <= ?"
            cursor.execute(query, (item_id, start_date, end_date))

            # Get the results from the cursor
            results = cursor.fetchall()
            print("BS: ", results)

            # Generate unique dates from the results
            result_list = []
            unique_dates = set()
            for row in results:
                row = list(row)
                date = row[1]

                result_list.append(row)
                unique_dates.add(date)

            # Sort the unique dates in ascending order
            sorted_dates = sorted(unique_dates)

            if len(sorted_dates) > 1:
                print(f"Ledger From {sorted_dates[0]} to {sorted_dates[-1]}")
            else:
                print(f"Ledger For {sorted_dates[0]}")

            main_ledger = []

            for date in sorted_dates:
                purchases, sales, return_sales, return_buys = 0, 0, 0, 0
                date_elements = []

                for row_data in result_list:
                    if row_data[1] == date:
                        date_elements.append(row_data)

                for i in range(0, len(date_elements)):
                    if i == 0:
                        date_opening = date_elements[i][2]
                    if i == len(date_elements)-1:
                        date_closing = date_elements[i][-1]

                    for col, col_data in enumerate(date_elements[i]):
                        if col == 3:
                            purchases += col_data
                        if col == 4:
                            sales += col_data
                        if col == 5:
                            return_sales += col_data
                        if col == 6:
                            return_buys += col_data

                results = (date, date_opening, purchases, sales,
                           return_sales, return_buys, 0, date_closing)
                main_ledger.append(results)

            total_p, total_s, total_rs, total_rb = 0, 0, 0, 0
            print("HERE ARE YOUR LEDGERS:::::: SIR")
            for date_wise_ledger in main_ledger:
                for col, data in enumerate(date_wise_ledger):
                    if col == 2:
                        total_p += data
                    elif col == 3:
                        total_s += data
                    elif col == 4:
                        total_rs += data
                    elif col == 5:
                        total_rb += data
                print(date_wise_ledger)

            # Define the number of rows to display per page
            rows_per_page = 6

            total_rows = len(main_ledger)
            # Calculate total number of pages
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page

            current_page = 1
            start_index = 0
            end_index = rows_per_page

            def next_page():
                nonlocal current_page, start_index, end_index
                if current_page < total_pages:
                    current_page += 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    current_page_label = tk.Label(
                        window, text=f"{current_page} of {total_pages}", font=("Arial", 12, "bold"))
                    current_page_label.grid(row=1, column=4, padx=10, pady=10)
                    update_table()

            def previous_page():
                nonlocal current_page, start_index, end_index
                if current_page > 1:
                    current_page -= 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    current_page_label = tk.Label(
                        window, text=f"{current_page} of {total_pages}", font=("Arial", 12, "bold"))
                    current_page_label.grid(row=1, column=4, padx=10, pady=10)
                    update_table()

            def update_table():
                for widget in window.grid_slaves():
                    widget.grid_forget()

                # Create the header label
                header_label = tk.Label(
                    window, text="Item Ledger", font=("Arial", 14, "bold"))
                header_label.grid(row=0, column=0, pady=10)
                # Create a range frame
                body_frame = tk.Frame(window)
                body_frame.grid(row=1, column=0, pady=10)
                item_id = int(item_id_label.cget("text"))
                # Create the item ID label with border
                item_id_l_label = tk.Label(
                    body_frame, text=f"Item ID: {item_id}", borderwidth=1, relief="solid", padx=10, pady=10)
                item_id_l_label.grid(row=1, column=0, padx=5, pady=5)

                item_name = item_name_entry.get()
                # Create the item name label with border
                item_name_l_label = tk.Label(
                    body_frame, text=f"Item Name: {item_name}", borderwidth=1, relief="solid", padx=10, pady=10)
                item_name_l_label.grid(row=1, column=1, padx=5, pady=5)

                start_date = start_date_entry.get()
                end_date = end_date_entry.get()

                start_date_label = tk.Label(
                    body_frame, text=f"{start_date} to {end_date}", borderwidth=1, relief="solid", padx=10, pady=10)
                start_date_label.grid(row=1, column=6, padx=5, pady=5)
                # Create a range frame
                data_frame = tk.Frame(window)
                data_frame.grid(row=2, column=0, padx=5, pady=10)
                item_id = int(item_id_label.cget("text"))
                # Create the table headers with fixed column widths
                headers = ["Date", "Opening", "Purchase", "Sale",
                           "Return Sell", "Return Buy", "Issue", "Closing"]
                for column, header in enumerate(headers):
                    label = tk.Label(data_frame, text=header, font=(
                        "Arial", 12, "bold"), borderwidth=1, relief="solid", padx=10, pady=10, width=8)
                    label.grid(row=2, column=column, padx=5, pady=5)

                # Display the main_ledger for the current page
                for row, data in enumerate(main_ledger[start_index:end_index], start=start_index):
                    for column, value in enumerate(data):
                        label = tk.Label(
                            data_frame, text=value, borderwidth=1, relief="solid", padx=10, pady=10, width=10)
                        label.grid(row=row + 3, column=column,
                                   padx=5, pady=5)

                # For dynamic navigation
                seperator_p_label = tk.Label(data_frame, text="----"*3)
                seperator_p_label.grid(
                    row=len(main_ledger)+4, column=2, padx=5, pady=5)

                total_p_label = tk.Label(
                    data_frame, text=total_p, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padx=10, pady=10,)
                total_p_label.grid(row=len(main_ledger)+5,
                                   column=2, padx=5, pady=5)

                seperator_s_label = tk.Label(data_frame, text="----"*3)
                seperator_s_label.grid(
                    row=len(main_ledger)+4, column=3, padx=5, pady=5)

                total_s_label = tk.Label(
                    data_frame, text=total_s, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padx=10, pady=10,)
                total_s_label.grid(row=len(main_ledger)+5,
                                   column=3, padx=5, pady=5)

                seperator_rs_label = tk.Label(data_frame, text="----"*3)
                seperator_rs_label.grid(
                    row=len(main_ledger)+4, column=4, padx=5, pady=5)

                total_rs_label = tk.Label(
                    data_frame, text=total_rs, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padx=10, pady=10,)
                total_rs_label.grid(row=len(main_ledger)+5,
                                    column=4, padx=5, pady=5)

                seperator_rb_label = tk.Label(data_frame, text="----"*3)
                seperator_rb_label.grid(
                    row=len(main_ledger)+4, column=5, padx=5, pady=5)

                total_rb_label = tk.Label(
                    data_frame, text=total_rb, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padx=10, pady=10,)
                total_rb_label.grid(row=len(main_ledger)+5,
                                    column=5, padx=5, pady=5)

                # Add a container frame for pagination buttons
                pagination_container = tk.Frame(window, bg="white")
                pagination_container.grid(
                    row=len(main_ledger) + 6, column=0, padx=5, pady=5)

                # Add pagination buttons
                previous_button = tk.Button(
                    pagination_container, text="Previous", command=previous_page)
                previous_button.pack(side="left", padx=5, pady=5)

                page_info = tk.Label(pagination_container, text=f"Page {current_page} of {total_pages}", font=(
                    "Arial", 10), bg="white", fg="black")
                page_info.pack(side="left", padx=5, pady=5)

                next_button = tk.Button(
                    pagination_container, text="Next", command=next_page)
                next_button.pack(side="left", padx=5, pady=5)

                # Create an Entry widget for the page number
                page_entry = ttk.Entry(pagination_container, width=10)
                page_entry.pack(side="left", padx=5, pady=5)

                # Add a button to trigger the print dialog
                print_button = tk.Button(
                    pagination_container, text="Print", command=lambda: print_window_content(window))
                print_button.pack(side="left")

                def print_window_content(sales_print_window):
                    # Create a new top-level window
                    new_window = tk.Toplevel(sales_print_window)

                    # Set the window title
                    new_window.title("Print Dialog")

                    # Set the size of the window
                    window_width = 400
                    window_height = 300
                    screen_width = sales_print_window.winfo_screenwidth()
                    screen_height = sales_print_window.winfo_screenheight()

                    x = (screen_width - window_width) // 2
                    y = (screen_height - window_height) // 2

                    new_window.geometry(
                        f"{window_width}x{window_height}+{x}+{y}")

                    # Create a range frame
                    bmw_frame = tk.Frame(new_window)
                    bmw_frame.grid(row=0, column=0, pady=10)

                    # Add content to the new window
                    label_name = tk.Label(bmw_frame, text="Printer Name:")
                    label_name.grid(row=0, column=0, pady=10)

                    # Fetch available printer names using win32print
                    printer_names = [printer[2]
                                     for printer in win32print.EnumPrinters(2)]

                    # Create a dropdown with available printer names
                    selected_printer = tk.StringVar(bmw_frame)
                    dropdown_printers = ttk.Combobox(
                        bmw_frame, textvariable=selected_printer, values=printer_names)
                    dropdown_printers.grid(row=0, column=1, pady=10)

                    # Set a default printer if available
                    if printer_names:
                        selected_printer.set(printer_names[0])

                    # Create a range frame
                    range_frame = tk.Frame(new_window)
                    range_frame.grid(row=1, column=0, pady=10)

                    # Add "Print Range" label
                    label_print_range = tk.Label(
                        range_frame, text="Print Range:")
                    label_print_range.grid(row=0, column=0, pady=5)

                    # Add radio buttons for "All" and "Pages" in the same column but different rows
                    print_range_var = tk.StringVar(
                        value="All")  # Set an initial value
                    radio_all = tk.Radiobutton(
                        range_frame, text="All", variable=print_range_var, value="All")
                    radio_all.grid(row=1, column=0, pady=5)

                    radio_pages = tk.Radiobutton(
                        range_frame, text="Pages", variable=print_range_var, value="Pages")
                    radio_pages.grid(row=1, column=1, pady=5)

                    # Manually set the state of one radio button to selected
                    radio_all.select()

                    # Initially disable the entry widget
                    rpe = tk.Entry(range_frame, state=tk.DISABLED)
                    rpe.grid(row=1, column=2, pady=5)

                    # Callback function to update the entry widget when radio buttons are selected
                    def update_entry_widget(*args):
                        if print_range_var.get() == "Pages":
                            rpe.config(state=tk.NORMAL)
                        else:
                            rpe.delete(0, tk.END)
                            rpe.config(state=tk.DISABLED)

                    # Bind the callback function to the StringVar
                    print_range_var.trace_add('write', update_entry_widget)

                    # Function to handle radio button selection
                    def radio_button_selected(value):
                        print_range_var.set(value)

                    # Attach the radio button selection function to the radio buttons
                    radio_all.config(
                        command=lambda: radio_button_selected("All"))
                    radio_pages.config(
                        command=lambda: radio_button_selected("Pages"))

                    # Create a copies frame
                    copies_frame = tk.Frame(new_window)
                    copies_frame.grid(row=2, column=0, pady=10)

                    # Add content to the copies frame
                    label_copies = tk.Label(copies_frame, text="Copies:")
                    label_copies.grid(row=0, column=0, pady=5)

                    label_num_copies = tk.Label(
                        copies_frame, text="Number of Copies:")
                    label_num_copies.grid(row=1, column=0, pady=5)

                    # Number entry field with increment and decrement options
                    entry_num_copies = tk.Entry(copies_frame, width=5)
                    entry_num_copies.grid(row=1, column=1, pady=5)

                    entry_num_copies.insert(0, "1")

                    btn_increment = tk.Button(
                        copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                    btn_increment.grid(row=1, column=2, pady=5, padx=2)

                    btn_decrement = tk.Button(
                        copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                    btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                    # Create OK and Cancel buttons
                    btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                        sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                    btn_ok.grid(row=3, column=0, pady=10)

                    btn_cancel = tk.Button(
                        new_window, text="Cancel", command=new_window.destroy)
                    btn_cancel.grid(row=3, column=1, pady=10)

                    def increment_num_copies(entry_num_copies):
                        current_value = int(entry_num_copies.get())
                        entry_num_copies.delete(0, tk.END)
                        entry_num_copies.insert(0, str(current_value + 1))

                    def decrement_num_copies(entry_num_copies):
                        current_value = int(entry_num_copies.get())
                        new_value = max(1, current_value - 1)
                        entry_num_copies.delete(0, tk.END)
                        entry_num_copies.insert(0, str(new_value))

                    def bmw_engine(window, print_range_var, page_range, enc):
                        if print_range_var == 'Pages':
                            try:
                                new_window.destroy()
                                time.sleep(1)
                                print('toredaaa')
                                print(print_range_var)
                                # page_range = page_entry.get()
                                pages_to_capture = []

                                # Parse the page range input
                                for part in page_range.split(','):
                                    if '-' in part:
                                        start, end = map(int, part.split('-'))
                                        pages_to_capture.extend(
                                            range(start, end + 1))
                                    else:
                                        pages_to_capture.append(int(part))

                                # Ensure all page numbers are within valid bounds
                                invalid_pages = [page for page in pages_to_capture if not (
                                    1 <= page <= total_pages)]
                                if invalid_pages:
                                    print(
                                        f"Invalid page numbers: {', '.join(map(str, invalid_pages))}. Please enter valid page numbers.")
                                    return

                                # Iterate over the specified pages and take screenshots
                                for page_number in pages_to_capture:
                                    # Update the current_page variable and update the table
                                    nonlocal current_page, start_index, end_index
                                    current_page = page_number
                                    start_index = (
                                        current_page - 1) * rows_per_page
                                    end_index = min(
                                        start_index + rows_per_page, total_rows)
                                    update_table()

                                    # Take a screenshot of the current page
                                    window.update()
                                    x = window.winfo_rootx()
                                    y = window.winfo_rooty()
                                    x1 = x + window.winfo_width()
                                    y1 = y + window.winfo_height()

                                    screenshot = ImageGrab.grab(
                                        bbox=(x, y, x1, y1))
                                    screenshot.save(
                                        f"page_{page_number}_screenshot.png")
                                    print(
                                        f"Screenshot of Page {page_number} saved successfully.")

                                    img_file = f"page_{page_number}_screenshot.png"
                                    for _ in range(enc):
                                        # print(enc, img_file)
                                        # print()
                                        printer_name = selected_printer.get()
                                        print(printer_name, img_file)

                                        try:
                                            subprocess.Popen(
                                                ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                            time.sleep(1)
                                        except subprocess.CalledProcessError as e:
                                            print("Error:", e)
                                            time.sleep(1)
                                        time.sleep(1)

                                    loop_completed = True  # Set loop completion flag

                                    # Delete the image file after the loop
                                    if loop_completed:
                                        delete_file(img_file)

                            except ValueError:
                                print(
                                    "Invalid page range format. Please enter a valid page range.")

                        elif print_range_var == 'All':
                            new_window.destroy()
                            time.sleep(1)
                            for page_number in range(1, total_pages+1):
                                # Update the current_page variable and update the table
                                current_page = page_number
                                start_index = (
                                    current_page - 1) * rows_per_page
                                end_index = min(
                                    start_index + rows_per_page, total_rows)
                                update_table()

                                # Take a screenshot of the current page
                                window.update()
                                x = window.winfo_rootx()
                                y = window.winfo_rooty()
                                x1 = x + window.winfo_width()
                                y1 = y + window.winfo_height()

                                screenshot = ImageGrab.grab(
                                    bbox=(x, y, x1, y1))
                                screenshot.save(
                                    f"page_{page_number}_screenshot.png")

                                print(
                                    f"Screenshot of Page {page_number} saved successfully.")

                                img_file = f"page_{page_number}_screenshot.png"

                                for _ in range(enc):
                                    printer_name = selected_printer.get()
                                    print(printer_name, img_file)
                                    try:
                                        subprocess.Popen(
                                            ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                        time.sleep(1)
                                    except subprocess.CalledProcessError as e:
                                        print("Error:", e)
                                        time.sleep(1)
                                    time.sleep(1)

                                loop_completed = True  # Set loop completion flag

                                # Delete the image file after the loop
                                if loop_completed:
                                    delete_file(img_file)

                    new_window.focus_force()
                    new_window.mainloop()

                def nav_page(page_no):
                    if page_no < current_page:
                        for i in range(current_page-page_no):
                            previous_page()
                    elif page_no > current_page:
                        for i in range(page_no - current_page):
                            next_page()

                # Bind the <Return> event to load the entered page
                page_entry.bind('<Return>', lambda event: nav_page(
                    int(page_entry.get())))
                previous_button.bind('<Return>', lambda event: previous_page())
                next_button.bind('<Return>', lambda event: next_page())

            update_table()

            window.bind("<Right>", focus_next_widget)
            window.bind("<Left>", focus_previous_widget)

            window.focus_force()
            window.mainloop()

        def open_monitor():

            sales_print_window = tk.Tk()

            # Get the screen width and height
            screen_width = sales_print_window.winfo_screenwidth()
            screen_height = sales_print_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 700
            window_height = 500
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            # Set the window size and position
            sales_print_window.geometry(
                f"{window_width}x{window_height}+{x}+{y}")

            # Set the window background color to white
            sales_print_window.configure(bg="white")

            # Create the header label
            print_header_label = tk.Label(sales_print_window, text="Monitor Employee",
                                          font=("Arial", 12, "bold"), bg="white", fg="black")
            print_header_label.pack(pady=10)
            # current_date = date_entry.get()
            # date_label = tk.Label(sales_print_window, text=f"Date: {current_date}",
            #                       font=("Arial", 12), bg="white", fg="black", borderwidth=1, relief="solid")
            # date_label.pack(pady=10)
            date_txt = date_entry.get()
            m, y = date_txt.split('-')[1], date_txt.split('-')[2]
            closing_month = f'{m}-{y}'
            cursor.execute('''
                SELECT Monitors.date, Users.username,Monitors.login_time, Monitors.logout_time
                FROM Monitors
                INNER JOIN Users ON Monitors.u_id = Users.id
                WHERE date LIKE ? 
                ''', ('%-' + closing_month,))

            rows = cursor.fetchall()
            table_container1 = tk.Frame(sales_print_window, bg="white")
            table_container1.pack(padx=10, pady=10)

            rows_per_page = 10
            total_rows = len(rows)
            # Calculate total number of pages
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page

            current_page = 1
            start_index = 0
            end_index = rows_per_page

            def print_window_content(sales_print_window):
                # Create a new top-level window
                new_window = tk.Toplevel(sales_print_window)

                # Set the window title
                new_window.title("Print Dialog")

                # Set the size of the window
                window_width = 400
                window_height = 300
                screen_width = sales_print_window.winfo_screenwidth()
                screen_height = sales_print_window.winfo_screenheight()

                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2

                new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

                # Create a range frame
                bmw_frame = tk.Frame(new_window)
                bmw_frame.grid(row=0, column=0, pady=10)

                # Add content to the new window
                label_name = tk.Label(bmw_frame, text="Printer Name:")
                label_name.grid(row=0, column=0, pady=10)

                # Fetch available printer names using win32print
                printer_names = [printer[2]
                                 for printer in win32print.EnumPrinters(2)]

                # Create a dropdown with available printer names
                selected_printer = tk.StringVar(bmw_frame)
                dropdown_printers = ttk.Combobox(
                    bmw_frame, textvariable=selected_printer, values=printer_names)
                dropdown_printers.grid(row=0, column=1, pady=10)

                # Set a default printer if available
                if printer_names:
                    selected_printer.set(printer_names[0])

                # Create a range frame
                range_frame = tk.Frame(new_window)
                range_frame.grid(row=1, column=0, pady=10)

                # Add "Print Range" label
                label_print_range = tk.Label(range_frame, text="Print Range:")
                label_print_range.grid(row=0, column=0, pady=5)

                # Add radio buttons for "All" and "Pages" in the same column but different rows
                print_range_var = tk.StringVar(
                    value="All")  # Set an initial value
                radio_all = tk.Radiobutton(
                    range_frame, text="All", variable=print_range_var, value="All")
                radio_all.grid(row=1, column=0, pady=5)

                radio_pages = tk.Radiobutton(
                    range_frame, text="Pages", variable=print_range_var, value="Pages")
                radio_pages.grid(row=1, column=1, pady=5)

                # Manually set the state of one radio button to selected
                radio_all.select()

                # Initially disable the entry widget
                rpe = tk.Entry(range_frame, state=tk.DISABLED)
                rpe.grid(row=1, column=2, pady=5)

                # Callback function to update the entry widget when radio buttons are selected
                def update_entry_widget(*args):
                    if print_range_var.get() == "Pages":
                        rpe.config(state=tk.NORMAL)
                    else:
                        rpe.delete(0, tk.END)
                        rpe.config(state=tk.DISABLED)

                # Bind the callback function to the StringVar
                print_range_var.trace_add('write', update_entry_widget)

                # Function to handle radio button selection
                def radio_button_selected(value):
                    print_range_var.set(value)

                # Attach the radio button selection function to the radio buttons
                radio_all.config(command=lambda: radio_button_selected("All"))
                radio_pages.config(
                    command=lambda: radio_button_selected("Pages"))

                # Create a copies frame
                copies_frame = tk.Frame(new_window)
                copies_frame.grid(row=2, column=0, pady=10)

                # Add content to the copies frame
                label_copies = tk.Label(copies_frame, text="Copies:")
                label_copies.grid(row=0, column=0, pady=5)

                label_num_copies = tk.Label(
                    copies_frame, text="Number of Copies:")
                label_num_copies.grid(row=1, column=0, pady=5)

                # Number entry field with increment and decrement options
                entry_num_copies = tk.Entry(copies_frame, width=5)
                entry_num_copies.grid(row=1, column=1, pady=5)

                entry_num_copies.insert(0, "1")

                btn_increment = tk.Button(
                    copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                btn_increment.grid(row=1, column=2, pady=5, padx=2)

                btn_decrement = tk.Button(
                    copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                # Create OK and Cancel buttons
                btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                    sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                btn_ok.grid(row=3, column=0, pady=10)

                btn_cancel = tk.Button(
                    new_window, text="Cancel", command=new_window.destroy)
                btn_cancel.grid(row=3, column=1, pady=10)

                def increment_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(current_value + 1))

                def decrement_num_copies(entry_num_copies):
                    current_value = int(entry_num_copies.get())
                    new_value = max(1, current_value - 1)
                    entry_num_copies.delete(0, tk.END)
                    entry_num_copies.insert(0, str(new_value))

                def bmw_engine(window, print_range_var, page_range, enc):
                    if print_range_var == 'Pages':
                        try:
                            new_window.destroy()
                            time.sleep(1)
                            print('toredaaa')
                            print(print_range_var)
                            # page_range = page_entry.get()
                            pages_to_capture = []

                            # Parse the page range input
                            for part in page_range.split(','):
                                if '-' in part:
                                    start, end = map(int, part.split('-'))
                                    pages_to_capture.extend(
                                        range(start, end + 1))
                                else:
                                    pages_to_capture.append(int(part))

                            # Ensure all page numbers are within valid bounds
                            invalid_pages = [page for page in pages_to_capture if not (
                                1 <= page <= total_pages)]
                            if invalid_pages:
                                print(
                                    f"Invalid page numbers: {', '.join(map(str, invalid_pages))}. Please enter valid page numbers.")
                                return

                            # Iterate over the specified pages and take screenshots
                            for page_number in pages_to_capture:
                                # Update the current_page variable and update the table
                                nonlocal current_page, start_index, end_index
                                current_page = page_number
                                start_index = (
                                    current_page - 1) * rows_per_page
                                end_index = min(
                                    start_index + rows_per_page, total_rows)
                                update_table()

                                # Take a screenshot of the current page
                                window.update()
                                x = window.winfo_rootx()
                                y = window.winfo_rooty()
                                x1 = x + window.winfo_width()
                                y1 = y + window.winfo_height()

                                screenshot = ImageGrab.grab(
                                    bbox=(x, y, x1, y1))
                                screenshot.save(
                                    f"page_{page_number}_screenshot.png")
                                print(
                                    f"Screenshot of Page {page_number} saved successfully.")

                                img_file = f"page_{page_number}_screenshot.png"
                                for _ in range(enc):

                                    printer_name = selected_printer.get()
                                    print(printer_name, img_file)

                                    try:
                                        subprocess.Popen(
                                            ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                        time.sleep(1)
                                    except subprocess.CalledProcessError as e:
                                        print("Error:", e)
                                        time.sleep(1)
                                    time.sleep(1)

                                loop_completed = True  # Set loop completion flag

                                # Delete the image file after the loop
                                if loop_completed:
                                    delete_file(img_file)

                        except ValueError:
                            print(
                                "Invalid page range format. Please enter a valid page range.")

                    elif print_range_var == 'All':
                        new_window.destroy()
                        time.sleep(1)
                        for page_number in range(1, total_pages+1):
                            # Update the current_page variable and update the table
                            current_page = page_number
                            start_index = (current_page - 1) * rows_per_page
                            end_index = min(
                                start_index + rows_per_page, total_rows)
                            update_table()

                            # Take a screenshot of the current page
                            window.update()
                            x = window.winfo_rootx()
                            y = window.winfo_rooty()
                            x1 = x + window.winfo_width()
                            y1 = y + window.winfo_height()

                            screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
                            screenshot.save(
                                f"page_{page_number}_screenshot.png")

                            print(
                                f"Screenshot of Page {page_number} saved successfully.")

                            img_file = f"page_{page_number}_screenshot.png"

                            for _ in range(enc):
                                printer_name = selected_printer.get()
                                print(printer_name, img_file)
                                try:
                                    subprocess.Popen(
                                        ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                    time.sleep(1)
                                except subprocess.CalledProcessError as e:
                                    print("Error:", e)
                                    time.sleep(1)
                                time.sleep(1)

                            loop_completed = True  # Set loop completion flag

                            # Delete the image file after the loop
                            if loop_completed:
                                delete_file(img_file)

                new_window.focus_force()
                new_window.mainloop()

            def next_page():
                nonlocal current_page, start_index, end_index
                if current_page < total_pages:
                    current_page += 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    page_info.configure(
                        text=f"Page {current_page} of {total_pages}")
                    update_table()

            def previous_page():
                nonlocal current_page, start_index, end_index
                if current_page > 1:
                    current_page -= 1
                    start_index = (current_page - 1) * rows_per_page
                    end_index = min(start_index + rows_per_page, total_rows)
                    page_info.configure(
                        text=f"Page {current_page} of {total_pages}")
                    update_table()

            def update_table():
                for widget in table_container1.grid_slaves():
                    widget.grid_forget()

                headers = ["Date", "User Name", "LogIn Time", "LogOut Time"]
                for col, header in enumerate(headers):
                    header_label = tk.Label(table_container1, text=header, font=(
                        "Arial", 10, "bold"), bg="white", borderwidth=1, width=15, relief="solid", padx=10, pady=5)
                    header_label.grid(row=0, column=col)

                start_index = (current_page - 1) * rows_per_page
                end_index = min(start_index + rows_per_page, total_rows)

                for row, data in enumerate(rows[start_index:end_index], start=1):
                    for col, col_data in enumerate(data):
                        m_label = tk.Label(table_container1, text=col_data, font=(
                            "Arial", 10), bg="white", borderwidth=1, width=15, relief="solid", padx=10, pady=5)
                        m_label.grid(row=row, column=col)

                page_info.configure(
                    text=f"Page {current_page} of {total_pages}")

            # Add pagination buttons
            pagination_frame = tk.Frame(sales_print_window, bg="white")
            pagination_frame.pack(pady=10)

            previous_button = tk.Button(
                pagination_frame, text="Previous", command=previous_page)
            previous_button.pack(side="left")
            previous_button.bind('<Return>', lambda event: previous_page())
            page_info = tk.Label(pagination_frame, text=f"Page {current_page} of {total_pages}", font=(
                "Arial", 10), bg="white", fg="black")
            page_info.pack(side="left", padx=10)

            next_button = tk.Button(
                pagination_frame, text="Next", command=next_page)
            next_button.pack(side="left")
            # Bind the <Return> event to load the entered page
            next_button.bind('<Return>', lambda event: next_page())
            # Create an Entry widget for the page number
            page_entry = ttk.Entry(pagination_frame, width=7)
            page_entry.pack(side="left")

            # Add a button to trigger the print dialog
            print_button = tk.Button(
                pagination_frame, text="Print", command=lambda: print_window_content(sales_print_window))
            print_button.pack(side="left")

            def nav_page(page_no):
                if page_no < current_page:
                    for i in range(current_page-page_no):
                        previous_page()
                elif page_no > current_page:
                    for i in range(page_no - current_page):
                        next_page()
            # Bind the <Return> event to load the entered page
            page_entry.bind('<Return>', lambda event: nav_page(
                int(page_entry.get())))

            update_table()

            sales_print_window.bind("<Right>", focus_next_widget)
            sales_print_window.bind("<Left>", focus_previous_widget)

            sales_print_window.focus_force()
            sales_print_window.mainloop()

        def open_closing_stock():

            date_txt = date_entry.get()
            m, y = date_txt.split('-')[1], date_txt.split('-')[2]
            closing_month = f'{m}-{y}'

            cursor.execute(
                '''
                SELECT Categories.id AS cid,
                    Categories.category_name AS category,
                    MedicineSales.date AS date,
                    Items.id AS item_id,
                    Items.item_name,
                    SUM(MedicineSales.quantity) AS quantity,
                    Items.sell_rate,
                    SUM(MedicineSales.amount) AS amount
                FROM MedicineSales
                INNER JOIN Categories ON MedicineSales.category_id = Categories.id
                INNER JOIN Items ON MedicineSales.item_id = Items.id
                WHERE  MedicineSales.date LIKE ?
                GROUP BY Categories.id, Categories.category_name, Items.id, Items.item_name, MedicineSales.date
                ''', ('%-' + closing_month,)
            )

            sales_data = cursor.fetchall()

            gs_total = 0
            for data in sales_data:
                amt = data[-1]
                gs_total += amt

            cursor.execute(
                '''
                SELECT Categories.id AS cid,
                    Categories.category_name AS category,
                    MedicinePurchases.date AS date,
                    Items.id AS item_id,
                    Items.item_name,
                    SUM(MedicinePurchases.quantity) AS quantity,
                    Items.buy_rate,
                    SUM(MedicinePurchases.amount) AS amount
                FROM MedicinePurchases
                INNER JOIN Categories ON MedicinePurchases.category_id = Categories.id
                INNER JOIN Items ON MedicinePurchases.item_id = Items.id
                WHERE  MedicinePurchases.date LIKE ?
                GROUP BY Categories.id, Categories.category_name, Items.id, Items.item_name, MedicinePurchases.date
                ''', ('%-' + closing_month,)
            )

            purchases_data = cursor.fetchall()

            gp_total = 0
            for data in purchases_data:
                amt = data[-1]
                gp_total += amt

            cursor.execute(
                '''
                SELECT e_id, date, type, amount
                FROM Expenses
                WHERE date LIKE ?
   
                ''', ('%-' + closing_month,)
            )

            expenses_data = cursor.fetchall()
            print("ed", expenses_data)
            ge_total = 0
            for data in expenses_data:
                amt = data[-1]
                ge_total += amt

            def show_profit():
                for widget in stock_window.winfo_children():
                    widget.destroy()  # Clear existing widgets

                # Add pagination buttons
                header_frame = tk.Frame(stock_window, bg="white")
                header_frame.pack(pady=10)
                header_label = tk.Label(
                    header_frame, text="Closing Stock Pharmacy-Profit", font=("Arial", 16, "bold"))
                header_label.grid(row=0, column=2, pady=10)

                button_frame = tk.Frame(stock_window, bg="white")
                button_frame.pack(pady=10)

                # Create the "Purchase Reports" button
                purchase_reports_button = tk.Button(
                    button_frame, text="Purchase Reports", width=15, font=("Arial", 8), command=lambda: closing_report("purchases"))
                purchase_reports_button.grid(row=1, column=0, padx=10, pady=10)
                purchase_reports_button.bind(
                    "<Return>", lambda event: purchase_reports_button.invoke())

                # Create the "Sale Reports" button
                sale_reports_button = tk.Button(
                    button_frame, text="Sale Reports", width=15, font=("Arial", 8), command=lambda: closing_report("sales"))
                sale_reports_button.grid(row=1, column=1, padx=10, pady=10)
                sale_reports_button.bind(
                    "<Return>", lambda event: sale_reports_button.invoke())

                if user_role == 'md':
                    expense_reports_button = tk.Button(
                        button_frame, text="Expense Reports", width=15, font=("Arial", 8), command=lambda: closing_report("expenses"))
                    expense_reports_button.grid(
                        row=1, column=2, padx=10, pady=10)
                    expense_reports_button.bind(
                        "<Return>", lambda event: expense_reports_button.invoke())

                    profit_button = tk.Button(
                        button_frame, text="Profit", width=15, font=("Arial", 8), command=lambda: show_profit())
                    profit_button.grid(row=1, column=3, padx=10, pady=10)
                    profit_button.bind(
                        "<Return>", lambda event: profit_button.invoke())

                date_label = ttk.Label(
                    button_frame, text=date_entry.get(), font=("Arial", 14))
                date_label.grid(row=1, column=4, padx=2, pady=2)

                body_frame = tk.Frame(stock_window, bg="white")
                body_frame.pack(pady=10)

                headers = ['Sale', 'Purchase', 'Expense', 'Profit']

                for i, header in enumerate(headers):
                    header_label = tk.Label(body_frame, text=header, font=(
                        'Arial', 10, 'bold'), bg="white", width=15, borderwidth=1, relief="solid", anchor="center")
                    header_label.grid(row=2, column=i, padx=5, pady=5)

                profit = gs_total - gp_total - ge_total
                body = [gs_total, gp_total, ge_total, profit]

                for i, info in enumerate(body):
                    data_label = tk.Label(
                        body_frame, text=info, font=('Arial', 10), width=15, bg="white", borderwidth=1, relief="solid", anchor="center")
                    data_label.grid(row=3, column=i, padx=5, pady=5)

                print_frame = tk.Frame(stock_window, bg="white")
                print_frame.pack(pady=10)

                # Add a button to trigger the print dialog
                print_button = tk.Button(
                    print_frame, text="Print", command=lambda: print_window_content(stock_window))
                print_button.pack(side="left")

                def print_window_content(sales_print_window):
                    # Create a new top-level window
                    new_window = tk.Toplevel(sales_print_window)

                    # Set the window title
                    new_window.title("Print Dialog")

                    # Set the size of the window
                    window_width = 400
                    window_height = 300
                    screen_width = sales_print_window.winfo_screenwidth()
                    screen_height = sales_print_window.winfo_screenheight()

                    x = (screen_width - window_width) // 2
                    y = (screen_height - window_height) // 2

                    new_window.geometry(
                        f"{window_width}x{window_height}+{x}+{y}")

                    # Create a range frame
                    bmw_frame = tk.Frame(new_window)
                    bmw_frame.grid(row=0, column=0, pady=10)

                    # Add content to the new window
                    label_name = tk.Label(bmw_frame, text="Printer Name:")
                    label_name.grid(row=0, column=0, pady=10)

                    # Fetch available printer names using win32print
                    printer_names = [printer[2]
                                     for printer in win32print.EnumPrinters(2)]

                    # Create a dropdown with available printer names
                    selected_printer = tk.StringVar(bmw_frame)
                    dropdown_printers = ttk.Combobox(
                        bmw_frame, textvariable=selected_printer, values=printer_names)
                    dropdown_printers.grid(row=0, column=1, pady=10)

                    # Set a default printer if available
                    if printer_names:
                        selected_printer.set(printer_names[0])

                    # Create a range frame
                    range_frame = tk.Frame(new_window)
                    range_frame.grid(row=1, column=0, pady=10)

                    # Add "Print Range" label
                    label_print_range = tk.Label(
                        range_frame, text="Print Range:")
                    label_print_range.grid(row=0, column=0, pady=5)

                    # Add radio buttons for "All" and "Pages" in the same column but different rows
                    print_range_var = tk.StringVar(
                        value="All")  # Set an initial value
                    radio_all = tk.Radiobutton(
                        range_frame, text="All", variable=print_range_var, value="All")
                    radio_all.grid(row=1, column=0, pady=5)

                    radio_pages = tk.Radiobutton(
                        range_frame, text="Pages", variable=print_range_var, value="Pages")
                    radio_pages.grid(row=1, column=1, pady=5)

                    # Manually set the state of one radio button to selected
                    radio_all.select()

                    # Initially disable the entry widget
                    rpe = tk.Entry(range_frame, state=tk.DISABLED)
                    rpe.grid(row=1, column=2, pady=5)

                    # Callback function to update the entry widget when radio buttons are selected
                    def update_entry_widget(*args):
                        if print_range_var.get() == "Pages":
                            rpe.config(state=tk.NORMAL)
                        else:
                            rpe.delete(0, tk.END)
                            rpe.config(state=tk.DISABLED)

                    # Bind the callback function to the StringVar
                    print_range_var.trace_add('write', update_entry_widget)

                    # Function to handle radio button selection
                    def radio_button_selected(value):
                        print_range_var.set(value)

                    # Attach the radio button selection function to the radio buttons
                    radio_all.config(
                        command=lambda: radio_button_selected("All"))
                    radio_pages.config(
                        command=lambda: radio_button_selected("Pages"))

                    # Create a copies frame
                    copies_frame = tk.Frame(new_window)
                    copies_frame.grid(row=2, column=0, pady=10)

                    # Add content to the copies frame
                    label_copies = tk.Label(copies_frame, text="Copies:")
                    label_copies.grid(row=0, column=0, pady=5)

                    label_num_copies = tk.Label(
                        copies_frame, text="Number of Copies:")
                    label_num_copies.grid(row=1, column=0, pady=5)

                    # Number entry field with increment and decrement options
                    entry_num_copies = tk.Entry(copies_frame, width=5)
                    entry_num_copies.grid(row=1, column=1, pady=5)

                    entry_num_copies.insert(0, "1")

                    btn_increment = tk.Button(
                        copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                    btn_increment.grid(row=1, column=2, pady=5, padx=2)

                    btn_decrement = tk.Button(
                        copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                    btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                    # Create OK and Cancel buttons
                    btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                        sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                    btn_ok.grid(row=3, column=0, pady=10)

                    btn_cancel = tk.Button(
                        new_window, text="Cancel", command=new_window.destroy)
                    btn_cancel.grid(row=3, column=1, pady=10)

                    def increment_num_copies(entry_num_copies):
                        current_value = int(entry_num_copies.get())
                        entry_num_copies.delete(0, tk.END)
                        entry_num_copies.insert(0, str(current_value + 1))

                    def decrement_num_copies(entry_num_copies):
                        current_value = int(entry_num_copies.get())
                        new_value = max(1, current_value - 1)
                        entry_num_copies.delete(0, tk.END)
                        entry_num_copies.insert(0, str(new_value))

                    def bmw_engine(window, print_range_var, page_range, enc):

                        new_window.destroy()
                        time.sleep(1)

                        # Take a screenshot of the current page
                        window.update()
                        x = window.winfo_rootx()
                        y = window.winfo_rooty()
                        x1 = x + window.winfo_width()
                        y1 = y + window.winfo_height()
                        screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
                        screenshot.save(
                            f"page_profit_screenshot.png")
                        print(
                            f"Screenshot of Page Profit saved successfully.")
                        img_file = f"page_profit_screenshot.png"
                        for _ in range(enc):
                            printer_name = selected_printer.get()
                            print(printer_name, img_file)
                            try:
                                subprocess.Popen(
                                    ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                time.sleep(1)
                            except subprocess.CalledProcessError as e:
                                print("Error:", e)
                                time.sleep(1)
                            time.sleep(1)

                        loop_completed = True  # Set loop completion flag

                        # Delete the image file after the loop
                        if loop_completed:
                            delete_file(img_file)

                    new_window.focus_force()
                    new_window.mainloop()

                profit_button.configure(background='cyan')
                profit_button.focus()

            def closing_report(closing_type):

                button_frame = tk.Frame(stock_window, bg="white")
                button_frame.pack(pady=10)

                body_frame = tk.Frame(stock_window, bg="white")
                body_frame.pack(pady=10)

                if closing_type == "purchases":
                    closing_data = purchases_data
                    print("closing_data", closing_data)

                    # Add headers
                    headers = ['Categories', 'Date',  'Item ID',
                               'Item Particular', 'Quantity', 'Rate', 'Amount']

                elif closing_type == "sales":
                    closing_data = sales_data
                    print("closing_data", closing_data)
                    headers = ['Categories', 'Date',  'Item ID',
                               'Item Particular', 'Quantity', 'Rate', 'Amount']

                elif closing_type == "expenses":
                    closing_data = expenses_data
                    print("closing_data", closing_data)
                    headers = ['Date', 'Expense Type', 'Amount']

                for i, header in enumerate(headers):
                    header_label = ttk.Label(
                        body_frame, text=header, font=('Arial', 10, 'bold'))
                    header_label.grid(row=0, column=i, padx=5, pady=5)

                date_label = ttk.Label(
                    button_frame, text=date_entry.get(), font=("Arial", 14))
                date_label.grid(row=0, column=4, padx=2, pady=2)

                # Add your code to display the sales report data below the headers
                total_rows = len(closing_data)
                rows_per_page = 9
                # Calculate the number of pages
                num_pages = -(-total_rows // rows_per_page)

                def show_closing_data(page_num):
                    for widget in stock_window.winfo_children():
                        widget.destroy()  # Clear existing widgets

                    header_frame = tk.Frame(stock_window, bg="white")
                    header_frame.pack(pady=10)

                    button_frame = tk.Frame(stock_window, bg="white")
                    button_frame.pack(pady=10)

                    body_frame = tk.Frame(stock_window, bg="white")
                    body_frame.pack(pady=10)

                    pagination_frame = tk.Frame(stock_window, bg="white")
                    pagination_frame.pack(pady=10)

                    if closing_type == "purchases":
                        header_label = tk.Label(
                            header_frame, text="Closing Stock Pharmacy-Purchases", font=("Arial", 16, "bold"))
                    elif closing_type == "sales":
                        header_label = tk.Label(
                            header_frame, text="Closing Stock Pharmacy-Sales", font=("Arial", 16, "bold"))
                    elif closing_type == "expenses":
                        header_label = tk.Label(
                            header_frame, text="Closing Stock Pharmacy-Expenses", font=("Arial", 16, "bold"))

                    header_label.grid(row=0, column=2, pady=10)

                    # Create the "Purchase Reports" button
                    purchase_reports_button = tk.Button(
                        button_frame, text="Purchase Reports", width=15, font=("Arial", 8), command=lambda: closing_report("purchases"))
                    purchase_reports_button.grid(
                        row=0, column=0, padx=10, pady=10)
                    purchase_reports_button.bind(
                        "<Return>", lambda event: purchase_reports_button.invoke())

                    # Create the "Sale Reports" button
                    sale_reports_button = tk.Button(
                        button_frame, text="Sale Reports", width=15, font=("Arial", 8), command=lambda: closing_report("sales"))
                    sale_reports_button.grid(row=0, column=1, padx=10, pady=10)
                    sale_reports_button.bind(
                        "<Return>", lambda event: sale_reports_button.invoke())

                    if user_role == 'md':
                        expense_reports_button = tk.Button(
                            button_frame, text="Expense Reports", width=15, font=("Arial", 8), command=lambda: closing_report("expenses"))
                        expense_reports_button.grid(
                            row=0, column=2, padx=10, pady=10)
                        expense_reports_button.bind(
                            "<Return>", lambda event: expense_reports_button.invoke())

                        profit_button = tk.Button(
                            button_frame, text="Profit", width=15, font=("Arial", 8), command=lambda: show_profit())
                        profit_button.grid(row=0, column=3, padx=10, pady=10)
                        profit_button.bind(
                            "<Return>", lambda event: profit_button.invoke())

                    date_label = ttk.Label(
                        button_frame, text=date_entry.get(), font=("Arial", 14))
                    date_label.grid(row=0, column=4, padx=2, pady=2)

                    # Re-add headers
                    for i, header in enumerate(headers):
                        if i == 0 or i == 1 or i == 3 or i == 6:
                            header_label = ttk.Label(
                                body_frame, text=header, font=('Arial', 10, 'bold'), width=14, borderwidth=1, relief="solid", background="white")
                        elif i == 2 or i == 4 or i == 5:
                            header_label = ttk.Label(
                                body_frame, text=header, font=('Arial', 10, 'bold'), width=7, borderwidth=1, relief="solid", background="white")

                        header_label.grid(row=0, column=i, padx=5, pady=5)

                    # Display data for the current page
                    start_index = (page_num - 1) * rows_per_page
                    end_index = min(page_num * rows_per_page, total_rows)
                    page_data = closing_data[start_index:end_index]

                    if closing_type == "purchases" or closing_type == "sales":
                        prev_category_id = None  # Variable to store the previous category id
                        category_total = 0  # Variable to store the total amount for the current category
                        row = 1  # Start row
                        for data in page_data:
                            # Get the current category id
                            category_id = data[0]

                            if category_id != prev_category_id:
                                # Add a row to display the category-wise total amount
                                if prev_category_id is not None:
                                    total_label = ttk.Label(
                                        body_frame, text=f"Category Total: {category_total}", borderwidth=1, relief="solid")
                                    total_label.grid(
                                        row=row + 1, column=6, padx=5, pady=5)
                                    row += 1
                                    category_total = 0  # Reset the category total

                                category_label = ttk.Label(
                                    body_frame, text=data[1], borderwidth=1, relief="solid")
                                category_label.grid(
                                    row=row + 1, column=0, padx=5, pady=5)

                                prev_category_id = category_id  # Update the previous category id

                            for col, value in enumerate(data):
                                if col > 1:
                                    value_label = ttk.Label(
                                        body_frame, text=value, font=('Arial', 10), borderwidth=1, relief="solid", background="white")
                                    value_label.grid(
                                        row=row + 1, column=col-1, padx=5, pady=5, sticky="nsew")

                            # Accumulate the amount for the current category
                            category_total += data[-1]

                            row += 1

                        # Add the category total for the last category
                        if prev_category_id is not None:
                            total_label = ttk.Label(
                                body_frame, text=f"Category Total: {category_total}", borderwidth=1, relief="solid")
                            total_label.grid(
                                row=row + 1, column=6, padx=5, pady=5)

                            if page_num == num_pages:
                                if closing_type == "purchases":
                                    # Add grand total
                                    gg_total_label = ttk.Label(
                                        body_frame, text=f"Grand Total: {gp_total}", borderwidth=1, relief="solid", font=('Arial', 10, 'bold'))
                                    gg_total_label.grid(
                                        row=row + 2, column=6, padx=5, pady=5)
                                elif closing_type == "sales":
                                    # Add grand total
                                    gg_total_label = ttk.Label(
                                        body_frame, text=f"Grand Total: {gs_total}", borderwidth=1, relief="solid", font=('Arial', 10, 'bold'))
                                    gg_total_label.grid(
                                        row=row + 2, column=6, padx=5, pady=5)

                        # Add pagination buttons
                        prev_button = ttk.Button(
                            pagination_frame, text="Previous", command=lambda: show_closing_data(page_num - 1),
                            state='disabled' if page_num == 1 else 'normal')
                        prev_button.grid(row=0, column=0, padx=5, pady=5)

                        current_label = ttk.Label(
                            pagination_frame, text=f"{page_num} of {num_pages}", font=("Arial", 14))
                        current_label.grid(row=0, column=1, padx=2, pady=2)

                        next_button = ttk.Button(
                            pagination_frame, text="Next", command=lambda: show_closing_data(page_num + 1),
                            state='disabled' if page_num == num_pages else 'normal')
                        next_button.grid(row=0, column=2, padx=5, pady=5)

                        # Create an Entry widget for the page number
                        page_entry = ttk.Entry(pagination_frame, width=7)
                        page_entry.grid(row=0, column=3, padx=2, pady=2)

                        # Add a button to trigger the print dialog
                        print_button = tk.Button(
                            pagination_frame, text="Print", command=lambda: print_window_content(stock_window))
                        print_button.grid(row=0, column=4, padx=2, pady=2)

                        # Focus on selected buttons or further modifications..
                        if closing_type == "purchases":
                            purchase_reports_button.configure(
                                background='cyan')
                            purchase_reports_button.focus()
                        elif closing_type == "sales":
                            sale_reports_button.configure(background='cyan')
                            sale_reports_button.focus()

                        # Bind the <Return> event to load the entered page
                        page_entry.bind('<Return>', lambda event: show_closing_data(
                            int(page_entry.get())))
                        prev_button.bind(
                            '<Return>', lambda event: show_closing_data(page_num - 1))
                        next_button.bind(
                            '<Return>', lambda event: show_closing_data(page_num + 1))

                    elif closing_type == "expenses":
                        curr_row = 0
                        for row, data in enumerate(page_data):
                            curr_row += 1
                            for col, value in enumerate(data):
                                if col > 0:
                                    value_label = ttk.Label(
                                        body_frame, text=value, font=('Arial', 10), width=13, borderwidth=1, relief="solid", background="white")
                                    value_label.grid(
                                        row=row + 1, column=col-1, padx=5, pady=5)

                        if page_num == num_pages:
                            # Add grand total
                            gg_total_label = ttk.Label(
                                body_frame, text=f"Grand Total: {ge_total}", borderwidth=1, relief="solid", font=('Arial', 10, 'bold'))
                            gg_total_label.grid(
                                row=row + 2, column=2, padx=5, pady=5)

                        # Add pagination buttons
                        prev_button = ttk.Button(
                            pagination_frame, text="Previous", command=lambda: show_closing_data(page_num - 1),
                            state='disabled' if page_num == 1 else 'normal')
                        prev_button.grid(row=0,
                                         column=0, padx=5, pady=5)

                        current_label = ttk.Label(
                            pagination_frame, text=f"{page_num} of {num_pages}", font=("Arial", 14))
                        current_label.grid(
                            row=0, column=1, padx=2, pady=2)

                        next_button = ttk.Button(
                            pagination_frame, text="Next", command=lambda: show_closing_data(page_num + 1),
                            state='disabled' if page_num == num_pages else 'normal')
                        next_button.grid(row=0,
                                         column=2, padx=5, pady=5)
                        # Create an Entry widget for the page number
                        page_entry = ttk.Entry(pagination_frame, width=7)
                        page_entry.grid(row=0, column=3, padx=2, pady=2)

                        # Add a button to trigger the print dialog
                        print_button = tk.Button(
                            pagination_frame, text="Print", command=lambda: print_window_content(stock_window))
                        print_button.grid(row=0, column=4, padx=2, pady=2)

                        # Focus selected button or further mod..
                        expense_reports_button.configure(background='cyan')
                        expense_reports_button.focus()

                        # Bind the <Return> event to load the entered page
                        page_entry.bind('<Return>', lambda event: show_closing_data(
                            int(page_entry.get())))

                        prev_button.bind(
                            '<Return>', lambda event: show_closing_data(page_num - 1))
                        next_button.bind(
                            '<Return>', lambda event: show_closing_data(page_num + 1))
                # Show the first page initially
                show_closing_data(1)

                def print_window_content(sales_print_window):
                    # Create a new top-level window
                    new_window = tk.Toplevel(sales_print_window)

                    # Set the window title
                    new_window.title("Print Dialog")

                    # Set the size of the window
                    window_width = 400
                    window_height = 300
                    screen_width = sales_print_window.winfo_screenwidth()
                    screen_height = sales_print_window.winfo_screenheight()

                    x = (screen_width - window_width) // 2
                    y = (screen_height - window_height) // 2

                    new_window.geometry(
                        f"{window_width}x{window_height}+{x}+{y}")

                    # Create a range frame
                    bmw_frame = tk.Frame(new_window)
                    bmw_frame.grid(row=0, column=0, pady=10)

                    # Add content to the new window
                    label_name = tk.Label(bmw_frame, text="Printer Name:")
                    label_name.grid(row=0, column=0, pady=10)

                    # Fetch available printer names using win32print
                    printer_names = [printer[2]
                                     for printer in win32print.EnumPrinters(2)]

                    # Create a dropdown with available printer names
                    selected_printer = tk.StringVar(bmw_frame)
                    dropdown_printers = ttk.Combobox(
                        bmw_frame, textvariable=selected_printer, values=printer_names)
                    dropdown_printers.grid(row=0, column=1, pady=10)

                    # Set a default printer if available
                    if printer_names:
                        selected_printer.set(printer_names[0])

                    # Create a range frame
                    range_frame = tk.Frame(new_window)
                    range_frame.grid(row=1, column=0, pady=10)

                    # Add "Print Range" label
                    label_print_range = tk.Label(
                        range_frame, text="Print Range:")
                    label_print_range.grid(row=0, column=0, pady=5)

                    # Add radio buttons for "All" and "Pages" in the same column but different rows
                    print_range_var = tk.StringVar(
                        value="All")  # Set an initial value
                    radio_all = tk.Radiobutton(
                        range_frame, text="All", variable=print_range_var, value="All")
                    radio_all.grid(row=1, column=0, pady=5)

                    radio_pages = tk.Radiobutton(
                        range_frame, text="Pages", variable=print_range_var, value="Pages")
                    radio_pages.grid(row=1, column=1, pady=5)

                    # Manually set the state of one radio button to selected
                    radio_all.select()

                    # Initially disable the entry widget
                    rpe = tk.Entry(range_frame, state=tk.DISABLED)
                    rpe.grid(row=1, column=2, pady=5)

                    # Callback function to update the entry widget when radio buttons are selected
                    def update_entry_widget(*args):
                        if print_range_var.get() == "Pages":
                            rpe.config(state=tk.NORMAL)
                        else:
                            rpe.delete(0, tk.END)
                            rpe.config(state=tk.DISABLED)

                    # Bind the callback function to the StringVar
                    print_range_var.trace_add('write', update_entry_widget)

                    # Function to handle radio button selection
                    def radio_button_selected(value):
                        print_range_var.set(value)

                    # Attach the radio button selection function to the radio buttons
                    radio_all.config(
                        command=lambda: radio_button_selected("All"))
                    radio_pages.config(
                        command=lambda: radio_button_selected("Pages"))

                    # Create a copies frame
                    copies_frame = tk.Frame(new_window)
                    copies_frame.grid(row=2, column=0, pady=10)

                    # Add content to the copies frame
                    label_copies = tk.Label(copies_frame, text="Copies:")
                    label_copies.grid(row=0, column=0, pady=5)

                    label_num_copies = tk.Label(
                        copies_frame, text="Number of Copies:")
                    label_num_copies.grid(row=1, column=0, pady=5)

                    # Number entry field with increment and decrement options
                    entry_num_copies = tk.Entry(copies_frame, width=5)
                    entry_num_copies.grid(row=1, column=1, pady=5)

                    entry_num_copies.insert(0, "1")

                    btn_increment = tk.Button(
                        copies_frame, text="▲", command=lambda: increment_num_copies(entry_num_copies))
                    btn_increment.grid(row=1, column=2, pady=5, padx=2)

                    btn_decrement = tk.Button(
                        copies_frame, text="▼", command=lambda: decrement_num_copies(entry_num_copies))
                    btn_decrement.grid(row=1, column=3, pady=5, padx=2)

                    # Create OK and Cancel buttons
                    btn_ok = tk.Button(new_window, text="OK", command=lambda: bmw_engine(
                        sales_print_window, print_range_var.get(), rpe.get(), int(entry_num_copies.get())))
                    btn_ok.grid(row=3, column=0, pady=10)

                    btn_cancel = tk.Button(
                        new_window, text="Cancel", command=new_window.destroy)
                    btn_cancel.grid(row=3, column=1, pady=10)

                    def increment_num_copies(entry_num_copies):
                        current_value = int(entry_num_copies.get())
                        entry_num_copies.delete(0, tk.END)
                        entry_num_copies.insert(0, str(current_value + 1))

                    def decrement_num_copies(entry_num_copies):
                        current_value = int(entry_num_copies.get())
                        new_value = max(1, current_value - 1)
                        entry_num_copies.delete(0, tk.END)
                        entry_num_copies.insert(0, str(new_value))

                    def bmw_engine(window, print_range_var, page_range, enc):
                        if print_range_var == 'Pages':
                            try:
                                new_window.destroy()
                                time.sleep(1)
                                print('toredaaa')
                                print(print_range_var)
                                # page_range = page_entry.get()
                                pages_to_capture = []

                                # Parse the page range input
                                for part in page_range.split(','):
                                    if '-' in part:
                                        start, end = map(int, part.split('-'))
                                        pages_to_capture.extend(
                                            range(start, end + 1))
                                    else:
                                        pages_to_capture.append(int(part))

                                # Ensure all page numbers are within valid bounds
                                invalid_pages = [page for page in pages_to_capture if not (
                                    1 <= page <= num_pages)]
                                if invalid_pages:
                                    print(
                                        f"Invalid page numbers: {', '.join(map(str, invalid_pages))}. Please enter valid page numbers.")
                                    return

                                # Iterate over the specified pages and take screenshots
                                for page_number in pages_to_capture:
                                    # Update the current_page variable and update the table
                                    # nonlocal current_page, start_index, end_index
                                    current_page = page_number
                                    start_index = (
                                        current_page - 1) * rows_per_page
                                    end_index = min(
                                        start_index + rows_per_page, total_rows)
                                    show_closing_data(current_page)

                                    # Take a screenshot of the current page
                                    window.update()
                                    x = window.winfo_rootx()
                                    y = window.winfo_rooty()
                                    x1 = x + window.winfo_width()
                                    y1 = y + window.winfo_height()

                                    screenshot = ImageGrab.grab(
                                        bbox=(x, y, x1, y1))
                                    screenshot.save(
                                        f"page_{page_number}_screenshot.png")
                                    print(
                                        f"Screenshot of Page {page_number} saved successfully.")

                                    img_file = f"page_{page_number}_screenshot.png"
                                    for _ in range(enc):
                                        printer_name = selected_printer.get()
                                        print(printer_name, img_file)

                                        try:
                                            subprocess.Popen(
                                                ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                            time.sleep(1)
                                        except subprocess.CalledProcessError as e:
                                            print("Error:", e)
                                            time.sleep(1)
                                        time.sleep(1)  # Delay after printing

                                    loop_completed = True  # Set loop completion flag

                                    # Delete the image file after the loop
                                    if loop_completed:
                                        delete_file(img_file)

                            except ValueError:
                                print(
                                    "Invalid page range format. Please enter a valid page range.")

                        elif print_range_var == 'All':
                            new_window.destroy()
                            time.sleep(1)
                            for page_number in range(1, num_pages+1):
                                # Update the current_page variable and update the table
                                current_page = page_number
                                start_index = (
                                    current_page - 1) * rows_per_page
                                end_index = min(
                                    start_index + rows_per_page, total_rows)
                                show_closing_data(current_page)

                                # Take a screenshot of the current page
                                window.update()
                                x = window.winfo_rootx()
                                y = window.winfo_rooty()
                                x1 = x + window.winfo_width()
                                y1 = y + window.winfo_height()

                                screenshot = ImageGrab.grab(
                                    bbox=(x, y, x1, y1))
                                screenshot.save(
                                    f"page_{page_number}_screenshot.png")

                                print(
                                    f"Screenshot of Page {page_number} saved successfully.")

                                img_file = f"page_{page_number}_screenshot.png"

                                for _ in range(enc):
                                    printer_name = selected_printer.get()
                                    print(printer_name, img_file)
                                    try:
                                        subprocess.Popen(
                                            ['start', 'mspaint', '/pt', img_file, printer_name], shell=True).communicate()
                                        time.sleep(1)
                                    except subprocess.CalledProcessError as e:
                                        print("Error:", e)
                                        time.sleep(1)
                                    time.sleep(1)  # Delay after printing

                                loop_completed = True  # Set loop completion flag

                                # Delete the image file after the loop
                                if loop_completed:
                                    delete_file(img_file)

                    new_window.focus_force()
                    new_window.mainloop()

            # Create a new Tkinter window
            stock_window = tk.Tk()
            stock_window.title("Closing Stock")

            # Get the screen width and height
            screen_width = stock_window.winfo_screenwidth()
            screen_height = stock_window.winfo_screenheight()

            # Calculate the window position to center it on the screen
            window_width = 1000
            window_height = 600
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            # Set the window size and position
            stock_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            header_frame = tk.Frame(stock_window, bg="white")
            header_frame.pack(pady=10)
            # Create a header label
            header_label = tk.Label(
                header_frame, text="Closing Stock Pharmacy", font=("Arial", 16, "bold"))
            header_label.grid(row=0, column=2, pady=10)
            button_frame = tk.Frame(stock_window, bg="white")
            button_frame.pack(pady=10)
            # Create the "Purchase Reports" button
            purchase_reports_button = tk.Button(
                button_frame, text="Purchase Reports", width=15, font=("Arial", 8), command=lambda: closing_report("purchases"))
            purchase_reports_button.grid(row=0, column=0, padx=10, pady=10)

            # Create the "Sale Reports" button
            sale_reports_button = tk.Button(
                button_frame, text="Sale Reports", width=15, font=("Arial", 8), command=lambda: closing_report(("sales")))
            sale_reports_button.grid(row=0, column=1, padx=10, pady=10)

            if user_role == 'md':
                # Create the "Sale Reports" button
                expense_reports_button = tk.Button(
                    button_frame, text="Expense Reports", width=15, font=("Arial", 8), command=lambda: closing_report(("expenses")))
                expense_reports_button.grid(row=0, column=2, padx=10, pady=10)
                # Create the "Sale Reports" button
                profit_button = tk.Button(
                    button_frame, text="Profit", width=15, font=("Arial", 8), command=lambda: show_profit())
                profit_button.grid(row=0, column=3, padx=10, pady=10)
                expense_reports_button.bind(
                    "<Return>", lambda event: expense_reports_button.invoke())
                profit_button.bind(
                    "<Return>", lambda event: profit_button.invoke())
            # # Bind keys
            # main_app.bind("<Down>", focus_next_widget)
            stock_window.bind("<Right>", focus_next_widget)
            # main_app.bind("<Up>", focus_previous_widget)
            stock_window.bind("<Left>", focus_previous_widget)
            # main_app.bind("<Return>", click_selected_widget)
            purchase_reports_button.bind(
                "<Return>", lambda event: purchase_reports_button.invoke())
            sale_reports_button.bind(
                "<Return>", lambda event: sale_reports_button.invoke())
            stock_window.focus_force()
            # Run the Tkinter event loop
            stock_window.mainloop()

        def convert_date(raw_date):
            # 01122024
            d, m, y = raw_date[:2], raw_date[2:4], raw_date[4:]
            actual_date = f'{d}-{m}-{y}'

            date_entry.delete(0, tk.END)
            date_entry.insert(0, actual_date)

        def convert_start_date(raw_date):
            # 01122024
            d, m, y = raw_date[:2], raw_date[2:4], raw_date[4:]
            actual_date = f'{d}-{m}-{y}'

            start_date_entry.delete(0, tk.END)
            start_date_entry.insert(0, actual_date)

        def convert_end_date(raw_date):
            # 01122024
            d, m, y = raw_date[:2], raw_date[2:4], raw_date[4:]
            actual_date = f'{d}-{m}-{y}'

            end_date_entry.delete(0, tk.END)
            end_date_entry.insert(0, actual_date)

        # Clear previous elements
        clear_frame(body_container)

        # Create the header label
        header_label = tk.Label(body_container, text="PHARMACY REPORT",
                                font=("Arial", 24, "bold"), borderwidth=1, relief='solid', bg="#F5F5DC", fg="black")
        header_label.pack(pady=(10, 20))

        # Create the info container
        rh_container = tk.Frame(body_container, bg="white")
        rh_container.pack(pady=20)

        # Create the "type" label
        type_expense_label = tk.Label(
            rh_container, text="Type:", font=("Arial", 10), bg="white")
        type_expense_label.grid(row=0, column=0, pady=5, sticky='w')

        # Create the dropdown with the "purchase" option
        transaction_type_selected = tk.StringVar()
        transaction_type_selected.set("Cash Sale")  # Set the default value
        transaction_type_dropdown = ttk.OptionMenu(
            rh_container, transaction_type_selected, "Cash Sale", "Cash Sale")
        transaction_type_dropdown.grid(row=0, column=1, padx=3, pady=5)

        # Create the "Date" label
        date_label = ttk.Label(
            rh_container, text="Date:", font=("Arial", 10), background="white")
        date_label.grid(row=0, column=2, padx=11, pady=5)

        # Get the current date
        current_date = datetime.now().strftime("%d-%m-%Y")

        # Create the label with the current date
        date_entry = ttk.Entry(
            rh_container, text=current_date, font=("Arial", 10))
        date_entry.grid(row=0, column=3, pady=5)

        date_entry.delete(0, tk.END)
        date_entry.insert(tk.END, current_date)

        date_entry.focus()
        date_entry.bind(
            '<Return>', lambda event: convert_date(date_entry.get()))

        item_name_label = tk.Label(
            rh_container, text="Item Name:", font=("Arial", 10), bg="white")
        item_name_label.grid(row=1, column=0, padx=2, pady=15)

        # Create the year entry field
        item_name_entry = ttk.Entry(rh_container, font=("Arial", 10))
        item_name_entry.grid(row=1, column=1, padx=2, pady=15)
        item_name_entry.bind('<Return>', open_item_popup_reports)

        item_id_label = tk.Label(
            rh_container, text="", font=("Arial", 10), bg="white")
        item_id_label.grid(row=1, column=2, padx=3, pady=15)

        # Create the report container
        report_container = tk.Frame(body_container, bg="white")
        report_container.pack()

        closing_stock_button = tk.Button(
            report_container, text="Closing Stock Pharmacy", width=20, font=button_font, command=open_closing_stock)
        closing_stock_button.grid(row=1, column=3, padx=2, pady=2)

        memo_sale_button = tk.Button(
            report_container, text="Memo Sale-Summarized", width=20, font=button_font, command=open_memo_summarized)
        memo_sale_button.grid(row=2, column=3, padx=2, pady=2)

        statement_button = tk.Button(
            report_container, text="Statement", width=20, font=button_font, command=open_statement_page)
        statement_button.grid(row=3, column=3, padx=2, pady=2)

        start_date_entry = ttk.Entry(report_container, font=("Arial", 14))
        start_date_entry.grid(row=6, column=2, padx=2, pady=2)
        start_date_entry.insert(tk.END, current_date)

        start_date_entry.bind(
            '<Return>', lambda event: convert_start_date(start_date_entry.get()))

        item_ledger = tk.Button(
            report_container, text="Item Ledger", width=20, font=button_font, command=open_item_ledger)
        item_ledger.grid(row=5, column=3, padx=2, pady=2)

        # Create the "to" label
        to_label = ttk.Label(report_container, text="to",
                             font=("Arial", 14), background="white")
        to_label.grid(row=6, column=3, padx=2, pady=2)

        end_date_entry = ttk.Entry(report_container, font=("Arial", 14))
        end_date_entry.grid(row=6, column=4, padx=2, pady=2)
        end_date_entry.insert(tk.END, current_date)

        end_date_entry.bind(
            '<Return>', lambda event: convert_end_date(end_date_entry.get()))

        if user_role == 'md':
            monitor = tk.Button(
                report_container, text="Monitor", width=20, font=button_font, command=open_monitor)
            monitor.grid(row=7, column=3, padx=2, pady=2)

    # *****************************************************#                    # *****************************************************#
    # ********** Report Page End **************************#                    # ********** Report Page End **************************#
    # *****************************************************#                    # *****************************************************#

    # *****************************************************#                    # *****************************************************#
    # ********** Expense Page    **************************#                    # ********** Expense Page    **************************#
    # *****************************************************#                    # *****************************************************#

    def open_expense_window():
        transactions = {}

        def show_confirmation(event, table_frame):

            global get_new_qty, return_event

            # def get_new_qty():
            #     return row_index, int(new_qty)

            def return_event():
                return event

            entry = event.widget
            new_amt = entry.get()
            row_index = entry.grid_info()["row"]

            # Filter only the entry fields for the current row
            row_entries = [widget for widget in table_frame.grid_slaves(
                row=row_index) if isinstance(widget, tk.Entry)]

            # Retrieve the values from the entry fields
            row_data = [entry.get() for entry in row_entries]

            # Reverse the elements of the row_data list
            row_data_reversed = list(reversed(row_data))
            # row_data_reversed[5:]
            row_data_reversed = [
                item for item in row_data_reversed if item != '']
            # del row_data_reversed[-1]
            row_data_reversed[1] = float(row_data_reversed[1])
            print("toe_DATA",  row_data_reversed)

            transactions[row_index] = row_data_reversed

            print(transactions)

            total_purchase_amt = 0

            current_last_row = table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row+1):
                # Clear the text in the columns of the current row
                for col in range(2):  # Assuming there are 2 columns
                    if col == 1:
                        widget = table_container.grid_slaves(
                            row=row, column=col)[0]
                        current_amt = widget.get()
                        print("tpa", current_amt)
                        if current_amt:
                            total_purchase_amt += float(current_amt)
                        else:
                            current_amt = 0

            total_amt.configure(text=total_purchase_amt)

            global dialog
            if 'dialog' in globals():
                dialog.destroy()
            dialog = CustomDialog(row_values=transactions)
            dialog.bind('<Escape>', lambda event: destroy(dialog))
            dialog.show()

        class CustomDialog(tk.Toplevel):
            def __init__(self, row_values):
                super().__init__()
                self.row_values = row_values
                self.result = None
                self.title("Confirmation")

                # Create and layout the dialog widgets
                message_label = tk.Label(self, text="Transactions: ")
                message_label.pack()

                global receive_message_label

                def receive_message_label():
                    return message_label

                row_values_text = tk.Text(self, height=10, width=30)
                row_values_text.pack()

                # Iterate over the keys of the dictionary and format the values
                for key, values in self.row_values.items():
                    formatted_values = ' '.join(str(value) for value in values)
                    row_values_text.insert(
                        tk.END, f"Expense: {key}\n{formatted_values}\n")

                next_type_btn = tk.Button(
                    self, text="Next Item", command=self.handle_next_type)
                next_type_btn.pack(side=tk.LEFT, padx=10)

                confirm_btn = tk.Button(
                    self, text="Confirm", command=self.handle_confirm)
                confirm_btn.pack(side=tk.LEFT, padx=10)

                self.focus_force()

                confirm_btn.focus()

                # Get the screen width and height
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()

                # Calculate the x and y coordinates for the window to be centered
                x = int(screen_width / 2 - self.winfo_width() / 2)
                y = int(screen_height / 2 - self.winfo_height() / 2)

                # Set the window's position
                self.geometry(f"+{x}+{y}")
                # Bind left and right arrow keys
                self.bind("<Left>", lambda event: self.focus_previous_button())
                self.bind("<Right>", lambda event: self.focus_next_button())
                # Bind Enter key press to button commands

                next_type_btn.bind(
                    "<Return>", lambda event: next_type_btn.invoke())
                confirm_btn.bind(
                    "<Return>", lambda event: confirm_btn.invoke())

            def focus_previous_button(self):
                current_focus = self.focus_get()
                buttons = self.get_buttons()

                if current_focus in buttons:
                    current_index = buttons.index(current_focus)
                    previous_index = (current_index - 1) % len(buttons)
                    buttons[previous_index].focus()

            def focus_next_button(self):
                current_focus = self.focus_get()
                buttons = self.get_buttons()

                if current_focus in buttons:
                    current_index = buttons.index(current_focus)
                    next_index = (current_index + 1) % len(buttons)
                    buttons[next_index].focus()

            def get_buttons(self):
                return [widget for widget in self.children.values() if isinstance(widget, tk.Button)]

            def handle_next_type(self):
                self.result = 'Next Type'
                self.destroy()
                # Get the currently focused widget
                event = return_event()
                current_widget = event.widget

                # Get the grid info of the currently focused widget
                current_widget_grid_info = current_widget.grid_info()

                # Get the row index of the currently focused widget
                row_idx = current_widget_grid_info['row']

                last_row_entry = table_container.grid_slaves(
                    row=row_idx, column=1)[0]

                current_last_row = table_container.grid_size()[1] - 1
                if row_idx == current_last_row:
                    if last_row_entry.get() != "":
                        # Generate new rows in the table
                        num_rows = 8  # Specify the number of rows to add
                        for i in range(num_rows):
                            new_row = row_idx + i + 1
                            expense_type = tk.Entry(
                                table_container, font=("Arial", 10), width=column_width)
                            expense_type.grid(
                                row=new_row, column=0, padx=10, pady=5)

                            # Amount label
                            amount_label = tk.Entry(
                                table_container, font=("Arial", 10), width=column_width)
                            amount_label.grid(
                                row=new_row, column=1, padx=10, pady=5)
                            amount_label.bind(
                                '<Return>', lambda event: show_confirmation(event, table_container))
                        scroll_down()

                next_type_entry = table_container.grid_slaves(
                    row=row_idx+1, column=0)[0]
                next_type_entry.focus()

            def handle_confirm(self):
                self.result = 'Confirm'
                e_id = int(invoice_number_entry.get())
                date = current_date
                form_type = selected_type.get()
                if form_type == "expense":
                    # Create a list of tuples for insertion
                    expenses = []
                    print("Hola ! transactions", transactions)

                    for row in transactions.keys():
                        fixed_entries = [e_id, date]
                        for col in transactions[row]:
                            fixed_entries.append(col)
                        expenses.append(tuple(fixed_entries))
                        print("mssssssssssssssssssssssss", expenses)

                    cursor.executemany(
                        "INSERT INTO Expenses (e_id, date, type, amount) VALUES (?, ?, ?, ?)",
                        expenses
                    )

                    message_label = receive_message_label()
                    message_label.configure(
                        text="Data inserted successfully")
                    conn.commit()
                    self.destroy()
                    open_expense_window()

                if form_type == "expense-search":
                    print("expense-search")

                    # Retrieve the document from the table based on the invoice number
                    cursor.execute(
                        "SELECT * FROM Expenses WHERE e_id=?", (e_id,))
                    rows = cursor.fetchall()

                    for row_idx, row in enumerate(rows):
                        p_id = row[0]
                        for key in transactions.keys():
                            if row_idx+1 == key:
                                updated_type = transactions[key][0]
                                updated_amt = transactions[key][1]

                                cursor.execute("UPDATE Expenses SET type=?, amount=? WHERE id=?",
                                               (updated_type, updated_amt, p_id))

                    conn.commit()

                    message_label = receive_message_label()
                    message_label.configure(
                        text="Data updated successfully")
                    self.destroy()
                    search()

            def show(self):
                self.wait_window(self)
                return self.result

        def delete():

            current_last_row = table_container.grid_size()[1] - 1
            e_id = int(invoice_number_entry.get())
            form_type = selected_type.get()
            cursor.execute(
                "SELECT * FROM Expenses WHERE e_id=?", (e_id,))
            expenses = cursor.fetchall()

            confirmation = messagebox.askyesno(
                "Confirmation", "Are you sure you want to delete this row?")
            if confirmation:
                if form_type == "expense":
                    # Find the focused entry field and clear the text in its row
                    row_index = None  # Initialize the row_index variable
                    for row in range(1, current_last_row + 1):
                        for col in range(2):  # Assuming there are 2 columns
                            widget = table_container.grid_slaves(
                                row=row, column=col)[0]
                            if isinstance(widget, tk.Entry) and widget == main_app.focus_get():
                                row_index = row  # Store the current row index
                                # Clear the text in the columns of the corresponding row
                                for clear_col in range(2):
                                    clear_widget = table_container.grid_slaves(
                                        row=row, column=clear_col)[0]
                                    if isinstance(clear_widget, tk.Entry):
                                        clear_widget.delete(0, tk.END)
                                    elif isinstance(clear_widget, tk.Label):
                                        clear_widget.configure(text="")
                                break  # Break the inner loop once the focused entry widget is found
                        else:
                            continue  # Continue to the next row if the focused entry widget is not found
                        break  # Break the outer loop once the row is cleared

                    # Use the row_index variable for further operations if needed
                    if row_index is not None:
                        if row_index in transactions:
                            del transactions[row_index]
                            print(transactions)
                            # Update the remaining row indices in the transactions dictionary
                            for idx in range(row_index + 1, current_last_row + 1):
                                if idx in transactions:
                                    transactions[idx -
                                                 1] = transactions.pop(idx)
                            # Call the update_amount() function to recalculate the total amoun
                            total_purchase_amt = 0

                            current_last_row = table_container.grid_size()[
                                1] - 1
                            # Iterate through each row in the table container
                            for row in range(1, current_last_row+1):
                                # Clear the text in the columns of the current row
                                for col in range(2):  # Assuming there are 2 columns
                                    if col == 1:
                                        widget = table_container.grid_slaves(
                                            row=row, column=col)[0]
                                        current_amt = widget.get()
                                        print("tqa", current_amt)
                                        if current_amt:
                                            total_purchase_amt += float(
                                                current_amt)
                                        else:
                                            current_amt = 0

                            total_amt.configure(text=total_purchase_amt)
                        else:
                            print("Row index not found in transactions dictionary.")

                    else:
                        print("No focused entry widget found.")

                if form_type == "expense-search":
                    #         # Find the focused entry field and clear the text in its row
                    row_index = None  # Initialize the row_index variable
                    for row in range(1, current_last_row + 1):
                        for col in range(2):  # Assuming there are 5 columns
                            widget = table_container.grid_slaves(
                                row=row, column=col)[0]
                            if isinstance(widget, tk.Entry) and widget == main_app.focus_get():
                                row_index = row
                                deleting_row = expenses[row-1]
                                deleting_row_p_id = deleting_row[0]

                                cursor.execute(
                                    "DELETE FROM Expenses WHERE id=?", (deleting_row_p_id,))

                                conn.commit()
                                search()

        def refresh():
            current_last_row = table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row + 1):
                # Clear the text in the columns of the current row
                for col in range(2):  # Assuming there are 5 columns
                    widget = table_container.grid_slaves(
                        row=row, column=col)[0]
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)

            # Clear the transactions dictionary
            transactions.clear()
            # Call the update_amount() function to reset the total amount
            total_amt.configure(text="")

        def hard_refresh():
            form_type = selected_type.get()
            e_id = int(invoice_number_entry.get())
            current_last_row = table_container.grid_size()[1] - 1
            # Iterate through each row in the table container
            for row in range(1, current_last_row + 1):
                # Clear the text in the columns of the current row
                for col in range(2):  # Assuming there are 5 columns
                    widget = table_container.grid_slaves(
                        row=row, column=col)[0]
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)

            # Clear the transactions dictionary
            transactions.clear()

            # Call the update_amount() function to reset the total amount
            total_amt.configure(text="")
            invoice_number_entry.delete(0, tk.END)
            invoice_number_entry.insert(0, e_id)

            if form_type == 'expense-search':
                search()

        def search():
            refresh()
            selected_type.set("expense-search")
            e_id = int(invoice_number_entry.get())
            cursor.execute(
                "SELECT * FROM Expenses WHERE e_id=?", (e_id,))
            expenses = cursor.fetchall()
            print("EXPPPDPPDPDPD:::", expenses)
            current_date_pls = expenses[0][2]

            current_date_label.configure(text=current_date_pls)
            for widget in table_container.winfo_children():
                widget.destroy()

            # Create the table headers
            headers = ["Type", "Amount"]
            num_columns = len(headers)

            # Adjust the percentage as needed
            table_width = round(window_width * 0.69 * 0.1)
            column_width = round(table_width / num_columns)
            for col, header in enumerate(headers):
                header_label = tk.Label(table_container, text=header, font=(
                    "Arial", 10, "bold"), bg="white", borderwidth=1, relief="solid", width=column_width, padx=10, pady=5)
                header_label.grid(row=0, column=col)

            # Create rows in the table
            total_amount = 0
            for row_index, row_data in enumerate(expenses):
                row_data = list(row_data)
                for col_index, value in enumerate(row_data):
                    if col_index == 3 or col_index == 4:
                        entry = tk.Entry(table_container, font=(
                            "Arial", 10), relief="solid", width=column_width, bg="white")
                        entry.insert(0, value)
                        entry.grid(row=row_index + 1,
                                   column=col_index-3, sticky="nsew")
                        if col_index == 4:
                            entry.bind('<Return>', lambda event: show_confirmation(
                                event, table_container))
                            total_amount += float(value)

            total_amt.configure(text=total_amount)

        global total_purchase_amt
        # total_purchase_amt = 0

        def update_total_amount(total_amount):
            # Update the amount value
            total_amt.config(text=total_amount)

        # Clear previous elements
        clear_frame(body_container)

        # Create the header label
        header_label = tk.Label(body_container, text="Expenses",
                                font=("Arial", 24, "bold"), borderwidth=1, relief='solid', bg="#F5F5DC", fg="black")
        header_label.pack(pady=(10, 20))

        # Create the info container
        btn_container = tk.Frame(body_container, bg="white")
        btn_container.pack()
        delete_button = tk.Button(
            btn_container, text="Delete", width=5, font=2, bg='#C41E3A', fg='white', command=delete)
        delete_button.grid(row=0, column=1, pady=2)

        Refresh_button = tk.Button(
            btn_container, text="Refresh", width=6, font=2, bg='#50C878', fg='white', command=hard_refresh)
        Refresh_button.grid(row=0, column=2, pady=2)

        Search_button = tk.Button(
            btn_container, text="Search", width=6, font=2, bg='#4169E1', fg='white', command=search)
        Search_button.grid(row=0, column=3, pady=2)

        # Create the info container
        expense_container = tk.Frame(body_container, bg="white")
        expense_container.pack()

        # Create the "type" label
        type_expense_label = tk.Label(
            expense_container, text="Type:", font=("Arial", 10), bg="white")
        type_expense_label.grid(row=1, column=0, padx=10, pady=5)

        # Create the dropdown with the "purchase" option
        selected_type = tk.StringVar()
        selected_type.set("expense")  # Set the default value
        type_expense_dropdown = ttk.OptionMenu(
            expense_container, selected_type, "expense", "expense", "expense-search")
        type_expense_dropdown.grid(row=1, column=1, padx=2, pady=5)

        # Create the "Date" label
        date_label = ttk.Label(
            expense_container, text="Date:", font=("Arial", 10), background="white")
        date_label.grid(row=1, column=2, padx=10, pady=5)

        # Get the current date
        current_date = datetime.now().strftime("%d-%m-%Y")

        # Create the label with the current date
        current_date_label = ttk.Label(
            expense_container, text=current_date, font=("Arial", 10), background="white", borderwidth=1, relief="solid")
        current_date_label.grid(row=1, column=3, padx=10, pady=5)

        # Create the "Invoice No." label
        invoice_label = tk.Label(
            expense_container, text="Expense ID:", font=("Arial", 10), bg="white")
        invoice_label.grid(row=1, column=4, padx=10, pady=5)

        # Execute the query to fetch all rows from "MedicinePurchases" table
        cursor.execute("SELECT MAX(e_id) FROM Expenses")

        # Fetch the result
        result = cursor.fetchone()

        # Get the largest invoice ID
        largest_invoice_id = result[0] if result[0] is not None else 0

        # Generate invoice number by adding 1 to the largest invoice ID
        invoice_number = largest_invoice_id + 1

        # Create the entry field for the invoice number
        invoice_number_entry = ttk.Entry(
            expense_container, font=("Arial", 10), width=10)
        invoice_number_entry.insert(0, invoice_number)
        invoice_number_entry.grid(row=1, column=5, padx=10, pady=5)

        table_container = make_table_frame()
        # Create the table headers
        headers = ["Expense Type", "Amount"]
        num_columns = len(headers)
        # Adjust the percentage as needed
        table_width = round(window_width * 0.69 * 0.1)
        column_width = round(table_width / num_columns)
        print(column_width)
        for col, header in enumerate(headers):
            header_label = tk.Label(table_container, text=header, font=(
                "Arial", 10, "bold"), bg="white", padx=10, pady=5, relief="solid", width=column_width)
            header_label.grid(row=0, column=col, sticky="nsew")

        # Create the rows
        num_rows = 8  # Specify the number of rows in the table
        for row in range(1, num_rows + 1):
            # Category entry field
            expense_type = tk.Entry(table_container, font=(
                "Arial", 10), width=column_width)
            expense_type.grid(row=row, column=0, padx=10, pady=5)
            expense_type.bind(
                '<Return>', focus_next_widget)
            # Set focus to the first row input field
            if row == 1:
                expense_type.focus_set()
            # Amount label
            amount_label = tk.Entry(
                table_container, font=("Arial", 10), width=column_width)
            amount_label.grid(row=row, column=1, padx=10, pady=5)
            amount_label.bind(
                '<Return>', lambda event: show_confirmation(event, table_container))

         # Create a separate frame outside the scrollable frame for fixed elements
        fixed_frame = tk.Frame(body_container, bg="white")
        fixed_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.95)

        # Create a gap of 7 columns on the left side
        gap_label = tk.Label(fixed_frame, text="", bg="white", width=82)
        gap_label.grid(row=0, column=0)

        total_label = tk.Label(
            fixed_frame, text="Total:", font=("Arial", 12), bg="white", width=10, borderwidth=1, relief="solid")
        total_label.grid(row=0, column=1, padx=10, pady=10)

        total_amt = tk.Label(fixed_frame, font=(
            "Arial", 12), borderwidth=1, relief="solid", width=10)
        total_amt.grid(row=0, column=2, padx=10, pady=10)

        delete_button.bind_all("<Control-d>", lambda event: delete())
        Refresh_button.bind_all("<Control-r>", lambda event: hard_refresh())
        Search_button.bind_all("<Control-s>", lambda event: search())
        invoice_number_entry.bind("<Return>", lambda event: search())

    # *****************************************************#                    # *****************************************************#
    # ********** Expense Page End *************************#                    # ********** Expense Page End *************************#
    # *****************************************************#                    # *****************************************************#

    # Destroy the login window
    window.destroy()

    # Create the main application window
    global main_app
    main_app = tk.Tk()
    main_app.title("Pharmacy Management System")

    # Get the screen width and height
    screen_width = main_app.winfo_screenwidth()
    screen_height = main_app.winfo_screenheight()

    # Set the main_app size to fill the screen
    main_app.geometry(f"{screen_width}x{screen_height}")
    main_app.configure(bg="#145DA0")
    main_header_label = tk.Label(main_app, text="AL-Amin Pharmacy",
                                 font=("Arial", 24, "bold"), bg="#145DA0", fg="white")
    main_header_label.pack(pady=(10, 10))

    # Create a frame as a container for the buttons
    button_container = tk.Frame(main_app, bg="white")
    button_container.pack(fill="both")

    # Create buttons for different pages
    button_width = 15  # Adjust the width of the buttons
    button_font = ("Arial", 8, "bold")  # Adjust the font size and style

    sales_button = tk.Button(
        button_container, text="Medicine Sale", width=button_width, font=button_font, command=open_sales_page)
    sales_button.grid(row=0, column=0, padx=2)

    purchase_button = tk.Button(
        button_container, text="Medicine Purchase", width=button_width, font=button_font, command=open_purchase_page)
    purchase_button.grid(row=0, column=1, padx=2)

    info_button = tk.Button(
        button_container, text="Medicine Info", width=button_width, font=button_font, command=open_info_page)
    info_button.grid(row=0, column=2, padx=2)

    report_button = tk.Button(
        button_container, text="Reports", width=button_width, font=button_font, command=open_report_page)
    report_button.grid(row=0, column=3, padx=2)

    user_role = user[3]
    if user_role == 'md':

        md_button = tk.Button(
            button_container, text="Expenses", width=button_width, font=button_font, command=open_expense_window)
        md_button.grid(row=0, column=4, padx=2)

    logout_button = tk.Button(
        button_container, text=f"Logout - {user[1]}", width=button_width, font=button_font, command=logout)

    # Place the logout button in the top-right corner
    logout_button.grid(row=0, column=5, padx=(
        120, 0), pady=(0, 0), sticky="ne")

    # Create a container for body elements
    # body_container = tk.Frame(main_app, bg="#145DA0")
    body_container = tk.Frame(main_app, bg="#F5F5DC")
    body_container.pack(fill="both", expand=True)

    # Load the logo image
    logo_image = Image.open("images/logo.jpg")
    # Resize the image to be slightly smaller
    new_width = int(logo_image.width * 0.9)
    new_height = int(logo_image.height * 0.9)
    logo_image = logo_image.resize(
        (new_width, new_height), resample=Image.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)

    # Create a Label widget for the logo background
    logo_label = tk.Label(body_container, image=logo_photo)
    logo_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Bind keys
    main_app.bind("<Down>", focus_next_widget)
    main_app.bind("<Right>", focus_next_widget)
    main_app.bind("<Up>", focus_previous_widget)
    main_app.bind("<Left>", focus_previous_widget)
    main_app.bind("<Return>", click_selected_widget)

    # set focus
    sales_button.focus_set()

    # Give the main_app window and Sale Button focus
    main_app.focus_force()
    sales_button.focus_force()

    def handle_ms(event):
        if event.keysym == "1" and (event.state & 4) != 0:  # Ctrl key
            open_sales_page()

    def handle_mp(event):
        if event.keysym == "2" and (event.state & 4) != 0:  # Ctrl key
            open_purchase_page()

    def handle_i(event):
        if event.keysym == "3" and (event.state & 4) != 0:  # Ctrl key
            open_info_page()

    def handle_r(event):
        if event.keysym == "4" and (event.state & 4) != 0:  # Ctrl key
            open_report_page()

    def handle_e(event):
        if event.keysym == "5" and (event.state & 4) != 0:  # Ctrl key
            open_expense_window()

    sales_button.bind_all("<Control-KeyPress-1>", handle_ms)
    purchase_button.bind_all("<Control-KeyPress-2>", handle_mp)
    info_button.bind_all("<Control-KeyPress-3>", handle_i)
    report_button.bind_all("<Control-KeyPress-4>", handle_r)
    md_button.bind_all("<Control-KeyPress-5>", handle_e)
    logout_button.bind_all("<Control-l>", lambda event: logout())
    # Run the Tkinter event loop for the main application window
    main_app.mainloop()

# *****************************************************#                    # *****************************************************#
# ********** Pharmacy Application End *****************#                    # ********** Pharmacy Application End *****************#
# *****************************************************#                    # *****************************************************#


# *****************************************************#                    # *****************************************************#
# ********** Login Window *****************************#                    # ********** Login Window *****************************#
# *****************************************************#                    # *****************************************************#

# Create the login window
# Create the login window
window = tk.Tk()
window.title("Login Form")

# Create a canvas as the background with the desired color
canvas = tk.Canvas(window, bg="#145DA0")
canvas.pack(fill="both", expand=True)

# Get the screen width and height
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# Set the window size to fill the screen
window.geometry(f"{screen_width}x{screen_height}")

# Load the logo image
logo_image = Image.open("images/logo.jpg")
# Resize the image to be slightly smaller
new_width = int(logo_image.width * 0.6)
new_height = int(logo_image.height * 0.6)
logo_image = logo_image.resize((new_width, new_height), resample=Image.LANCZOS)
logo_photo = ImageTk.PhotoImage(logo_image)

# Create a Label widget for the logo background
logo_label = tk.Label(canvas, image=logo_photo, bg="#145DA0")
logo_label.place(x=0, y=0, relwidth=1, relheight=1)

# Create the header label
header_label = tk.Label(canvas, text="AL-Amin Pharmacy Login",
                        font=("Arial", 24, "bold"), bg="#145DA0", fg="white")
header_label.pack(pady=(10, 20))

# Center the window on the screen
window.update_idletasks()
window_width = window.winfo_width()
window_height = window.winfo_height()
position_right = int(window.winfo_screenwidth() / 2 - window_width / 2)
position_down = int(window.winfo_screenheight() / 2 - window_height / 2)
window.geometry("+{}+{}".format(position_right, position_down))

# Create a frame as a container
# Set the background color of the container
container = tk.Frame(canvas, bg="#FFFFFF")
container.pack(fill="both", expand=True, padx=100, pady=100)


# Create a canvas with a transparent background
canvas = tk.Canvas(container, bg="white", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Set the container frame as the parent of the canvas
container.update()

# Get the dimensions of the canvas
canvas_width = canvas.winfo_width()
canvas_height = canvas.winfo_height()


# Calculate the position to place the image slightly below the center
image_x = (canvas_width - logo_image.width) // 2
image_y = (canvas_height - logo_image.height) // 2
# Adjust the position down by 5% of the canvas height
image_x += int(canvas_height * 0.015)
# Adjust the position down by 5% of the canvas height
image_y += int(canvas_height * 0.10)

# Place the logo image on the canvas
canvas.create_image(image_x, image_y, anchor="nw", image=logo_photo)

# Create the username label and input field
username_label = tk.Label(canvas, text="Username:", bg="white", font=16)
username_label.pack()

username_entry = tk.Entry(canvas, bg="white", width=30, font=16)
username_entry.pack()
username_entry.focus_force()

# Create the password label and input field
password_label = tk.Label(canvas, text="Password:", bg="white", font=16)
password_label.pack()

password_entry = tk.Entry(canvas, show="*", bg="white", width=30, font=16)
password_entry.pack(pady=10)

login_btn_container = tk.Frame(canvas, bg="white")
login_btn_container.pack()

# Create the login button
login_button = tk.Button(login_btn_container, text="Login",
                         command=login, font=10, bg="#18A558", fg='white')
# login_button.pack()
login_button.grid(row=0, column=0, padx=3)

# Create the login button
update_button = tk.Button(login_btn_container, text="Update Info",
                          command=update_user_info, font=10, bg='#75E6DA')
# update_button.pack()
update_button.grid(row=0, column=1)

# Create the login status label
login_label = tk.Label(canvas, text="", fg="red", bg="white")
login_label.pack(pady=10)

# Bind arrow keys to move between input fields
window.bind("<Down>", focus_next_widget)
window.bind("<Up>", focus_previous_widget)
username_entry.bind("<Down>", focus_next_widget)
password_entry.bind("<Down>", focus_next_widget)
password_entry.bind("<Up>", focus_previous_widget)
login_button.bind("<Up>", focus_previous_widget)

# Bind Enter key to click the currently selected input field or button
username_entry.bind("<Return>", focus_next_widget)
password_entry.bind("<Return>", lambda event: login())
login_button.bind("<Return>", click_selected_widget)

window.configure(bg="#145DA0")

# Run the Tkinter event loop for the login window
window.mainloop()

# *****************************************************#                    # *****************************************************#
# ********** Login Window End *************************#                    # ********** Login Window End *************************#
# *****************************************************#                    # *****************************************************#
