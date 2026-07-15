# 🍿 BookMyShow Clone — Cinema Ticket Booking System

A simplified clone of BookMyShow built as a Database Management Systems course project. Users can browse movies playing in their city, pick seats from an interactive seat map, and confirm a booking in seconds. Admins get a full dashboard to manage movies, theaters, shows, and view revenue reports.

Built with **Python + Streamlit** for the UI and **SQLite3** for the database. Business rules — like preventing double bookings or overselling seats — are enforced directly in the database using constraints and triggers, not just application-level checks.

> Course: CSF212 — Database Management Systems (Project 1) · Group 36

## Team

- Ekansh Gupta — 2024A7PS0043H
- Vaishnav Gadamsetty — 2024A7PS0026H
- Zakir Inaganti — 2024A7IS2428H
- Putha Mokshith Reddy — 2024A7IS2430H
- T Rithik Reddy — 2024A7PS0038H
- Mutyala Satya Ajay Chakravarthy — 2024A7PS0078H

## Features

- 🔐 User registration and login with role-based access (Customer / Admin)
- 🎬 City and movie-based show browsing
- 🪑 Interactive seat map with real-time availability (3×5 grid, 15 seats/show)
- 🎟️ Booking confirmation and cancellation
- 🛠️ Admin CRUD for Movies, Theaters, and Shows
- 📊 Revenue reporting via a dedicated database view
- ✅ Database-level enforcement of business rules via triggers (no double-booking, no overselling)

## Entity-Relationship Diagram

![ER Diagram](assets/er_diagram.jpg)

**Core tables:** `Users`, `Movies`, `Theaters`, `Shows`, `Bookings`

- A `Show` links a `Movie` to a `Theater` at a given time/price and can't exist without both.
- A `Booking` belongs to a `User` and a `Show`, and stores the selected seats and total amount.

## Database Design Highlights

| Object | Type | Purpose |
|---|---|---|
| `View_ShowDetails` | View | Denormalised join of Shows, Movies, Theaters for reporting |
| `Check_Capacity_Before_Booking` | Trigger | Rejects a booking if it would exceed a show's 15-seat capacity |
| `Check_Duplicate_Seats` | Trigger | Rejects a booking if any requested seat is already taken |
| `CHECK(Role IN ('Customer','Admin'))` | Constraint | Restricts Users.Role to valid values |
| `CHECK(Price > 0)` | Constraint | Prevents free/negative-price shows |
| `UNIQUE(Name, Location)` | Constraint | Prevents duplicate theaters in the same city |

Foreign keys are enforced explicitly at connection time with `PRAGMA foreign_keys = ON`, since SQLite has them off by default.

## Project Structure

```
.
├── APP CODE.py          # Main Streamlit application
├── schema.sql            # Database schema: tables, constraints, triggers, view, seed data
├── DOCUMENTATION.docx    # Full project report (problem statement, ER design, constraints, UI)
└── assets/
    └── er_diagram.jpg    # Entity-Relationship diagram
```

> Note: the archive also contains a duplicate copy of the app (`APP (1).py`). Only one copy is needed — feel free to delete the duplicate and rename `APP CODE.py` to `app.py`.

## Getting Started

### Prerequisites

- Python 3.8+
- `sqlite3` CLI (usually preinstalled on macOS/Linux; on Windows it ships with Python)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Install dependencies

```bash
pip install streamlit
```

### 3. Initialize the database

This creates `cinema.db` with the schema, triggers, view, and seed data (two sample movies, theaters, and shows):

```bash
sqlite3 cinema.db < schema.sql
```

### 4. Run the app

```bash
streamlit run "APP CODE.py"
```

The app will open at `http://localhost:8501`.

## Default Login

A single admin account is seeded on database initialisation:

| Username | Password |
|---|---|
| `admin` | `admin123` |

Customers can self-register from the Sign Up tab on the login page.

## Usage

**As a Customer:**
1. Sign up or log in.
2. Select your city and a movie to see available shows.
3. Pick free seats on the interactive grid and confirm your booking.
4. View or cancel bookings from the "My Bookings" page.

**As an Admin:**
1. Log in with the seeded admin credentials.
2. Use the dashboard to add/update movies, add theaters, schedule or delete shows.
3. Check the "View Reports" tab for a per-show booking count and revenue breakdown.

## Notes / Assumptions

- Passwords are stored in plain text — this is an academic project and not intended for production use.
- Each show has a fixed capacity of 15 seats (rows A–C, seats 1–5).
- Deleting a show also deletes all bookings associated with it.
- Show times are stored as ISO-8601 text (`YYYY-MM-DD HH:MM`).

## Documentation

See [`DOCUMENTATION.docx`](./DOCUMENTATION.docx) for the full project report, including the complete ER diagram, relational schema, constraint specifications, and UI walkthrough.

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Database:** SQLite3
- **Language:** Python
