-- 1. Drop existing tables to start fresh
DROP VIEW IF EXISTS View_ShowDetails;
DROP TRIGGER IF EXISTS Check_Capacity_Before_Booking;
DROP TABLE IF EXISTS Bookings;
DROP TABLE IF EXISTS Shows;
DROP TABLE IF EXISTS Theaters;
DROP TABLE IF EXISTS Movies;
DROP TABLE IF EXISTS Users;

-- 2. Create Users Table
CREATE TABLE Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Role TEXT CHECK(Role IN ('Customer', 'Admin')) NOT NULL DEFAULT 'Customer'
);

-- 3. Insert a default Admin account
INSERT INTO Users (Username, Password, Role) VALUES ('admin', 'admin123', 'Admin');

-- 4. Create Movies Table
CREATE TABLE Movies (
    MovieID INTEGER PRIMARY KEY AUTOINCREMENT, 
    Title TEXT NOT NULL,         
    Genre TEXT,
    Duration INTEGER
);

-- 5. Create Theaters Table
CREATE TABLE Theaters (
    TheaterID INTEGER PRIMARY KEY AUTOINCREMENT, 
    Name TEXT NOT NULL,
    Location TEXT NOT NULL,
    UNIQUE(Name, Location)
);

-- 6. Create Shows Table 
CREATE TABLE Shows (
    ShowID INTEGER PRIMARY KEY AUTOINCREMENT, 
    MovieID INTEGER,
    TheaterID INTEGER,
    ShowTime TEXT NOT NULL,
    Price REAL CHECK (Price > 0), 
    Total_Capacity INTEGER DEFAULT 15,
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID), 
    FOREIGN KEY (TheaterID) REFERENCES Theaters(TheaterID)
);

-- 7. Create Bookings Table 
CREATE TABLE Bookings (
    BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    ShowID INTEGER,
    Selected_Seats TEXT, 
    TotalAmount REAL,    
    Booking_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (ShowID) REFERENCES Shows(ShowID)
);

-- 8. Create View for Reports
CREATE VIEW View_ShowDetails AS
SELECT 
    s.ShowID, 
    m.Title AS Movie_Name, 
    t.Name AS Theater_Name, 
    s.ShowTime, 
    s.Price
FROM Shows s
JOIN Movies m ON s.MovieID = m.MovieID
JOIN Theaters t ON s.TheaterID = t.TheaterID;

-- 9. Populate Initial Sample Data
INSERT INTO Movies (Title, Genre, Duration) VALUES ('Inception', 'Sci-Fi', 148);
INSERT INTO Movies (Title, Genre, Duration) VALUES ('The Lion King', 'Animation', 118);

INSERT INTO Theaters (Name, Location) VALUES ('PVR Cinemas', 'Mumbai');
INSERT INTO Theaters (Name, Location) VALUES ('Cinepolis', 'Delhi');

INSERT INTO Shows (MovieID, TheaterID, ShowTime, Price) VALUES (1, 1, '2026-03-05 18:00', 250.0);
INSERT INTO Shows (MovieID, TheaterID, ShowTime, Price) VALUES (2, 2, '2026-03-05 20:30', 180.0);

-- 10. Trigger for Semantic Constraints
CREATE TRIGGER Check_Capacity_Before_Booking
BEFORE INSERT ON Bookings
BEGIN
    SELECT RAISE(ABORT, 'Semantic Constraint Violated: Not enough seats available.')
    WHERE (
        (LENGTH(NEW.Selected_Seats) - LENGTH(REPLACE(NEW.Selected_Seats, ',', '')) + 1) 
        + 
        (SELECT IFNULL(SUM(LENGTH(Selected_Seats) - LENGTH(REPLACE(Selected_Seats, ',', '')) + 1), 0) 
         FROM Bookings 
         WHERE ShowID = NEW.ShowID)
    ) > (SELECT Total_Capacity FROM Shows WHERE ShowID = NEW.ShowID);
END;

-- 11. Trigger to prevent double-booking the same seat
CREATE TRIGGER Check_Duplicate_Seats
BEFORE INSERT ON Bookings
BEGIN
    SELECT RAISE(ABORT, 'Semantic Constraint Violated: One or more selected seats are already booked for this show.')
    WHERE EXISTS (
        SELECT 1 FROM Bookings
        WHERE ShowID = NEW.ShowID
          AND Selected_Seats LIKE '%' || SUBSTR(NEW.Selected_Seats, 1, INSTR(NEW.Selected_Seats || ',', ',') - 1) || '%'
    );
END;