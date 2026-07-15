import streamlit as st
import sqlite3

# Connect to database and enforce foreign keys (CRITICAL FOR INTEGRITY CONSTRAINTS)
conn = sqlite3.connect('cinema.db', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON;")
c = conn.cursor()

st.set_page_config(page_title="BookMyShow Clone", layout="wide")

# --- SESSION STATE INITIALIZATION ---
# Track role (Admin/Customer) and UserID for the session
if 'role' not in st.session_state:
    st.session_state.role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

def set_role(role, user_id=None):
    st.session_state.role = role
    st.session_state.user_id = user_id

# ==========================================
# 1. LANDING PAGE (LOGIN / SIGN UP)
# ==========================================
if st.session_state.role is None:
    st.title("🍿 Welcome to BookMyShow")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to your account")
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        
        if st.button("Login", use_container_width=True):
            user = c.execute("SELECT UserID, Role FROM Users WHERE Username = ? AND Password = ?", (log_user, log_pass)).fetchone()
            
            if user:
                set_role(user[1], user[0]) # user[1] is Role, user[0] is UserID
                st.rerun()
            else:
                st.error("Invalid Username or Password!")
                
    with tab2:
        st.subheader("Create a new Customer account")
        new_user = st.text_input("Choose a Username", key="new_user")
        new_pass = st.text_input("Choose a Password", type="password", key="new_pass")
        
        if st.button("Sign Up", use_container_width=True):
            if new_user and new_pass:
                try:
                    c.execute("INSERT INTO Users (Username, Password, Role) VALUES (?, ?, 'Customer')", (new_user, new_pass))
                    conn.commit()
                    st.success("Account created successfully! You can now log in.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists. Please choose a different one.")
            else:
                st.warning("Please fill out both fields.")

# ==========================================
# 2. CUSTOMER INTERFACE
# ==========================================
elif st.session_state.role == "Customer":
    st.sidebar.title("🍿 BookMyShow")
    st.sidebar.write("Logged in as: **Customer**")
    
    if st.sidebar.button("🚪 Logout"):
        set_role(None)
        st.rerun()
        
    menu = ["🎟️ Book Tickets", "👤 My Bookings"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🎟️ Book Tickets":
        st.title("🎟️ Book Tickets")
        cities = c.execute("SELECT DISTINCT Location FROM Theaters").fetchall()
        city_names = [city[0] for city in cities]
        
        if not city_names:
            st.info("No theaters available right now. Please check back later!")
        else:
            selected_city = st.selectbox("📍 Select Your City", city_names)

            if selected_city:
                movie_query = """
                    SELECT DISTINCT m.MovieID, m.Title 
                    FROM Movies m
                    JOIN Shows s ON m.MovieID = s.MovieID
                    JOIN Theaters t ON s.TheaterID = t.TheaterID
                    WHERE t.Location = ?
                """
                movies = c.execute(movie_query, (selected_city,)).fetchall()
                movie_dict = {m[1]: m[0] for m in movies}
                
                selected_movie_name = st.selectbox("🎬 Select Movie", ["-- Select --"] + list(movie_dict.keys()))
                
                if selected_movie_name != "-- Select --":
                    movie_id = movie_dict[selected_movie_name]
                    
                    show_query = """
                        SELECT s.ShowID, t.Name, s.ShowTime, s.Price 
                        FROM Shows s
                        JOIN Theaters t ON s.TheaterID = t.TheaterID
                        WHERE s.MovieID = ? AND t.Location = ?
                    """
                    shows = c.execute(show_query, (movie_id, selected_city)).fetchall()
                    
                    st.write("### 🏢 Available Shows")
                    for show in shows:
                        show_id, theater_name, show_time, price = show
                        with st.expander(f"{theater_name} | {show_time} | ₹{price} per seat"):
                            
                            booked_data = c.execute("SELECT Selected_Seats FROM Bookings WHERE ShowID = ?", (show_id,)).fetchall()
                            booked_seats = []
                            for row in booked_data:
                                seats = [s.strip() for s in row[0].split(",")]
                                booked_seats.extend(seats)
                            
                            st.write("#### Screen This Way 📺")
                            st.write("---")
                            
                            rows, cols_count = ["A", "B", "C"], 5
                            selected_seats = []
                            
                            for row_letter in rows:
                                cols = st.columns(cols_count)
                                for col_num in range(1, cols_count + 1):
                                    seat_name = f"{row_letter}{col_num}"
                                    is_booked = seat_name in booked_seats
                                    
                                    with cols[col_num - 1]:
                                        if st.checkbox(seat_name, key=f"{show_id}_{seat_name}", disabled=is_booked, value=is_booked):
                                            if not is_booked: 
                                                selected_seats.append(seat_name)
                            st.write("---")
                            
                            if selected_seats:
                                total_amount = len(selected_seats) * price
                                st.info(f"**Selected:** {', '.join(selected_seats)} | **Total:** ₹{total_amount}")
                                
                                if st.button("💳 Pay & Book", key=f"pay_{show_id}"):
                                    seat_str = ", ".join(selected_seats)
                                    try:
                                        c.execute("INSERT INTO Bookings (UserID, ShowID, Selected_Seats, TotalAmount) VALUES (?, ?, ?, ?)", 
                                                  (st.session_state.user_id, show_id, seat_str, total_amount))
                                        conn.commit()
                                        st.success("🎉 Booking Confirmed! Enjoy the movie.")
                                        st.rerun()
                                    except sqlite3.Error as e:
                                        # This catches the Trigger constraint gracefully!
                                        st.error(f"Booking Failed: {e}")

    elif choice == "👤 My Bookings":
        st.title("👤 My Profile & Bookings")
        
        my_bookings_query = """
            SELECT b.BookingID, m.Title, t.Name, s.ShowTime, b.Selected_Seats, b.TotalAmount
            FROM Bookings b
            JOIN Shows s ON b.ShowID = s.ShowID
            JOIN Movies m ON s.MovieID = m.MovieID
            JOIN Theaters t ON s.TheaterID = t.TheaterID
            WHERE b.UserID = ?
        """
        records = c.execute(my_bookings_query, (st.session_state.user_id,)).fetchall()
        
        if records:
            for rec in records:
                b_id, m_title, t_name, s_time, seats, total = rec
                st.write(f"**🎟️ Ticket #{b_id}**: {m_title} at {t_name}")
                st.write(f"🗓️ {s_time} | 🪑 Seats: {seats} | 💰 ₹{total}")
                
                if st.button(f"Cancel Ticket #{b_id}", key=f"cancel_{b_id}"):
                    c.execute("DELETE FROM Bookings WHERE BookingID = ?", (b_id,))
                    conn.commit()
                    st.warning("Booking Cancelled.")
                    st.rerun()
                st.write("---")
        else:
            st.info("You have no bookings yet. Go book a movie!")

# ==========================================
# 3. ADMIN INTERFACE
# ==========================================
elif st.session_state.role == "Admin":
    st.sidebar.title("🔐 Admin Panel")
    st.sidebar.write("Logged in as: **Administrator**")
    
    if st.sidebar.button("🚪 Logout"):
        set_role(None)
        st.rerun()
        
    st.title("🔐 Admin Dashboard")
    
    admin_menu = st.radio("What would you like to do?", ["Add Movie", "Update Movie", "Add Theater", "Add Show", "Delete Show", "View Reports"], horizontal=True)
    st.write("---")
    
    if admin_menu == "Add Movie":
        st.write("### Add a New Movie")
        m_title = st.text_input("Movie Title")
        m_genre = st.text_input("Genre")
        m_duration = st.number_input("Duration (in minutes)", min_value=1)
        
        if st.button("➕ Add Movie"):
            c.execute("INSERT INTO Movies (Title, Genre, Duration) VALUES (?, ?, ?)", (m_title, m_genre, m_duration))
            conn.commit()
            st.success(f"Added Movie: {m_title}")
            
    elif admin_menu == "Update Movie":
        st.write("### Update Existing Movie Details")
        
        movie_list = c.execute("SELECT MovieID, Title, Genre, Duration FROM Movies").fetchall()
        
        if not movie_list:
            st.warning("No movies available to update. Please add a movie first.")
        else:
            movie_dict = {f"{m[1]} (ID:{m[0]})": m for m in movie_list}
            sel_movie = st.selectbox("Select Movie to Update", list(movie_dict.keys()))
            
            if sel_movie:
                movie_id, current_title, current_genre, current_duration = movie_dict[sel_movie]
                
                new_title = st.text_input("Update Title", value=current_title)
                new_genre = st.text_input("Update Genre", value=current_genre)
                new_duration = st.number_input("Update Duration (in minutes)", min_value=1, value=int(current_duration))
                
                if st.button("💾 Save Changes"):
                    c.execute('''
                        UPDATE Movies 
                        SET Title = ?, Genre = ?, Duration = ? 
                        WHERE MovieID = ?
                    ''', (new_title, new_genre, new_duration, movie_id))
                    conn.commit()
                    st.success(f"Successfully updated '{new_title}'!")

    elif admin_menu == "Add Theater":
        st.write("### Add a New Theater")
        t_name = st.text_input("Theater Name (e.g., PVR, INOX)")
        t_location = st.text_input("Location / City")
        
        if st.button("➕ Add Theater"):
            try:
                c.execute("INSERT INTO Theaters (Name, Location) VALUES (?, ?)", (t_name, t_location))
                conn.commit()
                st.success(f"Added Theater: {t_name} in {t_location}")
            except sqlite3.IntegrityError:
                # Catches the UNIQUE constraint
                st.error("This Theater already exists in this location!")
            
    elif admin_menu == "Add Show":
        st.write("### Schedule a New Show")
        
        movie_list = c.execute("SELECT MovieID, Title FROM Movies").fetchall()
        theater_list = c.execute("SELECT TheaterID, Name, Location FROM Theaters").fetchall()
        
        if not movie_list or not theater_list:
            st.warning("You must add at least one Movie and one Theater first!")
        else:
            movie_dict = {f"{m[1]} (ID:{m[0]})": m[0] for m in movie_list}
            theater_dict = {f"{t[1]}, {t[2]} (ID:{t[0]})": t[0] for t in theater_list}
            
            sel_movie = st.selectbox("Select Movie", list(movie_dict.keys()))
            sel_theater = st.selectbox("Select Theater", list(theater_dict.keys()))
            
            s_time = st.text_input("Show Time (e.g., 2026-03-05 18:00)")
            s_price = st.number_input("Ticket Price (₹)", min_value=1.0, value=200.0)
            
            if st.button("➕ Schedule Show"):
                c.execute("INSERT INTO Shows (MovieID, TheaterID, ShowTime, Price) VALUES (?, ?, ?, ?)", 
                          (movie_dict[sel_movie], theater_dict[sel_theater], s_time, s_price))
                conn.commit()
                st.success("Show scheduled successfully!")

    elif admin_menu == "Delete Show":
        st.write("### Delete a Show")
        st.warning("⚠️ Deleting a show will also remove all associated bookings.")
        
        shows = c.execute("""
            SELECT s.ShowID, m.Title, t.Name, t.Location, s.ShowTime 
            FROM Shows s 
            JOIN Movies m ON s.MovieID = m.MovieID 
            JOIN Theaters t ON s.TheaterID = t.TheaterID
        """).fetchall()
        
        if not shows:
            st.info("No shows available to delete.")
        else:
            show_dict = {f"{s[1]} at {s[2]}, {s[3]} | {s[4]} (ID:{s[0]})": s[0] for s in shows}
            sel_show = st.selectbox("Select Show to Delete", list(show_dict.keys()))
            
            if st.button("🗑️ Delete Show"):
                show_id_to_delete = show_dict[sel_show]
                # Delete associated bookings first (referential integrity)
                c.execute("DELETE FROM Bookings WHERE ShowID = ?", (show_id_to_delete,))
                c.execute("DELETE FROM Shows WHERE ShowID = ?", (show_id_to_delete,))
                conn.commit()
                st.success("Show and all associated bookings have been deleted.")
                st.rerun()

    elif admin_menu == "View Reports":
        st.write("### 📊 Show-wise Booking Report")
        st.caption("This report uses the View_ShowDetails database view.")
        
        report = c.execute("""
            SELECT v.ShowID, v.Movie_Name, v.Theater_Name, v.ShowTime, v.Price,
                   COUNT(b.BookingID) AS Total_Bookings,
                   IFNULL(SUM(b.TotalAmount), 0) AS Revenue
            FROM View_ShowDetails v
            LEFT JOIN Bookings b ON v.ShowID = b.ShowID
            GROUP BY v.ShowID
            ORDER BY v.ShowTime
        """).fetchall()
        
        if not report:
            st.info("No shows found. Add some shows first.")
        else:
            total_revenue = 0
            for row in report:
                show_id, movie, theater, showtime, price, bookings, revenue = row
                total_revenue += revenue
                with st.expander(f"🎬 {movie} | {theater} | {showtime}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Price per Seat", f"₹{price}")
                    col2.metric("Total Bookings", bookings)
                    col3.metric("Revenue", f"₹{revenue}")
            
            st.write("---")
            st.success(f"💰 **Total Revenue Across All Shows: ₹{total_revenue}**")