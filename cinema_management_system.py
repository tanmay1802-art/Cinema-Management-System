#!/usr/bin/env python3
# Combined Cinema Ticket Booking & Management System (with Customer Menu)
# Non-OOP, text-file storage, modular menus
# Roles: Cinema Manager, Ticketing Clerk, Technician, Customer
# Auth: Register/Login
# Storage: ./data (csv/txt), receipts in ./receipts
# --------------------------------------------------

import os, re
from datetime import datetime

# ---- Paths ----
BASE_ROOT = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
BASE_DIR = os.path.join(BASE_ROOT, "data")
RECEIPT_DIR = os.path.join(BASE_ROOT, "receipts")
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(RECEIPT_DIR, exist_ok=True)

USERS_FILE = os.path.join(BASE_DIR, "users.txt")                   # username,password
MOV_FILE   = os.path.join(BASE_DIR, "movies.csv")                  # movie_id,title,rating,duration,language,status
AUD_FILE   = os.path.join(BASE_DIR, "auditoriums.csv")             # aud_id,name
SHOW_FILE  = os.path.join(BASE_DIR, "showtimes.csv")               # show_id,movie_id,aud_id,date,time,seats,base_price
EQP_FILE   = os.path.join(BASE_DIR, "equipment.csv")               # aud_id,status,last_update,note
ISS_FILE   = os.path.join(BASE_DIR, "issues.csv")                  # issue_id,aud_id,issue_type,details,status,created_at,resolved_at,resolved_by
BOOK_FILE  = os.path.join(BASE_DIR, "bookings.csv")                # booking_id,customer_name,show_id,seats,status

# ---- Constants ----
DT_FMT = "%Y-%m-%d %H:%M"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
EQ_READY = "READY"
EQ_MAINT = "MAINTENANCE"
STATUS_OPEN = "OPEN"
STATUS_RESOLVED = "RESOLVED"
ISSUE_TYPES = ["projector", "sound", "aircon", "seat", "power", "network"]

# ---- Bootstrap ----
def _write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")

def ensure_files():
    if not os.path.exists(USERS_FILE):
        _write_lines(USERS_FILE, ["username,password"])
    if not os.path.exists(MOV_FILE):
        _write_lines(MOV_FILE, ["movie_id,title,rating,duration,language,status"])
    if not os.path.exists(AUD_FILE):
        _write_lines(AUD_FILE, ["aud_id,name"])
    if not os.path.exists(SHOW_FILE):
        _write_lines(SHOW_FILE, ["show_id,movie_id,aud_id,date,time,seats,base_price"])
    if not os.path.exists(EQP_FILE):
        _write_lines(EQP_FILE, ["aud_id,status,last_update,note"])
    if not os.path.exists(ISS_FILE):
        _write_lines(ISS_FILE, ["issue_id,aud_id,issue_type,details,status,created_at,resolved_at,resolved_by"])
    if not os.path.exists(BOOK_FILE):
        _write_lines(BOOK_FILE, ["booking_id,customer_name,show_id,seats,status"])

# ---- CSV helpers ----
def _read_rows(path):
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f.readlines()]
        if not lines:
            return rows
        for ln in lines[1:]:
            if ln.strip() == "":
                continue
            rows.append(ln.split(","))
        return rows
    except FileNotFoundError:
        ensure_files()
        return []
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return []

def _read_header(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except Exception:
        return ""

def _append_line(path, line):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return True
    except Exception as e:
        print(f"Error appending to {path}: {e}")
        return False

def _write_all(path, header, rows):
    lines = [header] + [",".join(r) for r in rows]
    _write_lines(path, lines)

def _next_id_from(path):
    rows = _read_rows(path)
    max_id = 0
    for r in rows:
        try:
            max_id = max(max_id, int(r[0]))
        except:
            pass
    return str(max_id + 1)

def _is_nonempty_no_comma(s):
    return isinstance(s, str) and s.strip() != "" and ("," not in s)

def _valid_datetime(dt_str):
    try:
        datetime.strptime(dt_str, DT_FMT)
        return True
    except:
        return False

def _now_str():
    return datetime.now().strftime(DT_FMT)

# ---- Lookups ----
def load_movies_map():
    return {r[0]: r[1] for r in _read_rows(MOV_FILE) if len(r) >= 2}

def load_aud_map():
    return {r[0]: r[1] for r in _read_rows(AUD_FILE) if len(r) >= 2}

def load_eqp_map():
    out = {}
    for r in _read_rows(EQP_FILE):
        if len(r) >= 4:
            out[r[0]] = (r[1], r[2], r[3])
    return out

# ---- Auth ----
def register_user():
    print("\n===== Register New Account =====")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    if not _is_nonempty_no_comma(username) or not _is_nonempty_no_comma(password):
        print("Invalid. Empty or contains comma.")
        return
    for u in _read_rows(USERS_FILE):
        if u[0] == username:
            print("Username already exists.")
            return
    _append_line(USERS_FILE, f"{username},{password}")
    print("Registration successful.")

def login_user():
    print("\n===== User Login =====")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    for u in _read_rows(USERS_FILE):
        if len(u) >= 2 and u[0] == username and u[1] == password:
            print(f"Welcome, {username}!")
            return True
    print("Invalid credentials.")
    return False

# ---- Cinema Manager ----
def add_auditorium():
    aud_id = input("Auditorium ID (e.g., AUD1): ").strip()
    name = input("Auditorium name: ").strip()
    if not _is_nonempty_no_comma(aud_id) or not _is_nonempty_no_comma(name):
        print("Invalid auditorium data."); return
    rows = _read_rows(AUD_FILE)
    for r in rows:
        if r[0] == aud_id:
            print("Auditorium ID exists."); return
    header = _read_header(AUD_FILE)
    rows.append([aud_id, name])
    _write_all(AUD_FILE, header, rows)
    print("Auditorium added.")

def view_auditoriums():
    rows = _read_rows(AUD_FILE)
    if not rows:
        print("No auditoriums."); return
    print("\nAuditoriums:")
    for r in rows:
        print(f"{r[0]} | {r[1]}")

def add_movie():
    t  = input("Title: ").strip()
    rt = input("Rating: ").strip()
    d  = input("Duration(min): ").strip()
    lg = input("Language: ").strip()
    st = input("Status(Active/Inactive): ").strip()
    if not t or not d.isdigit() or st not in ("Active","Inactive"):
        print("Invalid movie data."); return
    mid = _next_id_from(MOV_FILE)
    _append_line(MOV_FILE, ",".join((mid, t, rt, d, lg, st)))
    print("Movie added. ID:", mid)

def upd_movie():
    mid = input("MovieID: ").strip()
    rows = _read_rows(MOV_FILE)
    idx = -1
    for i, r in enumerate(rows):
        if r[0] == mid:
            idx = i; break
    if idx == -1:
        print("Not found."); return
    t  = input("Title: ").strip()
    rt = input("Rating: ").strip()
    d  = input("Duration(min): ").strip()
    lg = input("Language: ").strip()
    st = input("Status(Active/Inactive): ").strip()
    if not t or not d.isdigit() or st not in ("Active","Inactive"):
        print("Invalid."); return
    rows[idx] = [mid, t, rt, d, lg, st]
    _write_all(MOV_FILE, _read_header(MOV_FILE), rows)
    print("Updated.")

def del_movie():
    mid = input("MovieID: ").strip()
    for s in _read_rows(SHOW_FILE):
        if s[1] == mid:
            print("Movie has showtimes; cannot delete."); return
    rows = _read_rows(MOV_FILE)
    out = [r for r in rows if r[0] != mid]
    if len(out) == len(rows):
        print("Not found."); return
    _write_all(MOV_FILE, _read_header(MOV_FILE), out)
    print("Removed.")

def view_movies():
    rows = _read_rows(MOV_FILE)
    if not rows:
        print("No movies."); return
    print("\nMovies:")
    for r in rows:
        print(" | ".join(r))

def _validate_date_time(date, time):
    if not DATE_RE.match(date) or not TIME_RE.match(time):
        return False
    try:
        datetime.strptime(f"{date} {time}", DT_FMT)
        return True
    except:
        return False

def add_show():
    mid = input("MovieID: ").strip()
    aid = input("Auditorium ID: ").strip()
    date = input("Date (YYYY-MM-DD): ").strip()
    time = input("Time (HH:MM): ").strip()
    seats = input("Total seats for this show: ").strip()
    bp   = input("Base price: ").strip()
    try:
        seats_i = int(seats); float(bp)
    except:
        print("Invalid seats or base price."); return
    if not _validate_date_time(date, time):
        print("Invalid date/time format."); return
    ok_movie = False
    for m in _read_rows(MOV_FILE):
        if m[0] == mid and m[5] == "Active":
            ok_movie = True; break
    if not ok_movie:
        print("Movie invalid or inactive."); return
    if aid not in load_aud_map():
        print("Auditorium not found."); return
    for s in _read_rows(SHOW_FILE):
        if s[2] == aid and s[3] == date and s[4] == time:
            print("Showtime overlap in same auditorium."); return
    sid = _next_id_from(SHOW_FILE)
    _append_line(SHOW_FILE, ",".join((sid, mid, aid, date, time, str(seats_i), str(bp))))
    print("Show added. ID:", sid)

def upd_show():
    sid = input("ShowID: ").strip()
    rows = _read_rows(SHOW_FILE)
    idx = -1
    for i, r in enumerate(rows):
        if r[0] == sid:
            idx = i; break
    if idx == -1:
        print("Show not found."); return
    mid = input("MovieID: ").strip()
    aid = input("Auditorium ID: ").strip()
    date = input("Date (YYYY-MM-DD): ").strip()
    time = input("Time (HH:MM): ").strip()
    seats = input("Seats available: ").strip()
    bp   = input("Base price: ").strip()
    try:
        seats_i = int(seats); float(bp)
    except:
        print("Invalid numeric fields."); return
    if not _validate_date_time(date, time):
        print("Invalid date/time format."); return
    for k, s in enumerate(rows):
        if k == idx: continue
        if s[2] == aid and s[3] == date and s[4] == time:
            print("Overlap."); return
    rows[idx] = [sid, mid, aid, date, time, str(seats_i), str(bp)]
    _write_all(SHOW_FILE, _read_header(SHOW_FILE), rows)
    print("Show updated.")

def del_show():
    sid = input("ShowID: ").strip()
    for b in _read_rows(BOOK_FILE):
        if b[2] == sid:
            print("Has bookings; cannot delete."); return
    rows = _read_rows(SHOW_FILE)
    out = [r for r in rows if r[0] != sid]
    if len(out) == len(rows):
        print("Not found."); return
    _write_all(SHOW_FILE, _read_header(SHOW_FILE), out)
    print("Show removed.")

def view_shows():
    movies = load_movies_map()
    auds = load_aud_map()
    rows = _read_rows(SHOW_FILE)
    if not rows:
        print("No shows."); return
    print("\nShows:")
    for r in rows:
        mid = r[1]; aid = r[2]
        print(f"{r[0]} | {movies.get(mid, mid)} | {auds.get(aid, aid)} | {r[3]} {r[4]} | seats={r[5]} | price={r[6]}")

# ---- Ticketing Clerk ----
def _ensure_positive_int(s):
    return s.isdigit() and int(s) > 0

def view_seats():
    view_shows()

def generate_receipt(booking_id, customer_name, movie_name, date, time, num_seats):
    filename = os.path.join(RECEIPT_DIR, f"receipt_{booking_id}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("===== CINEMA BOOKING RECEIPT =====\n")
        f.write(f"Booking ID : {booking_id}\n")
        f.write(f"Customer    : {customer_name}\n")
        f.write(f"Movie       : {movie_name}\n")
        f.write(f"Date        : {date}\n")
        f.write(f"Time        : {time}\n")
        f.write(f"Seats Booked: {num_seats}\n")
        f.write(f"Status      : PAID\n")
        f.write("===============================\n")
        f.write("Thank you for booking with us!\nEnjoy your movie!\n")
    print(f"Receipt saved: {filename}")

def book_ticket():
    view_shows()
    sid = input("Enter ShowID to book: ").strip()
    cname = input("Customer name: ").strip()
    return _book_ticket_common(sid, cname)

def _book_ticket_common(sid, cname, nseats_input=None):
    nseats = nseats_input or input("Number of seats: ").strip()
    if not _ensure_positive_int(nseats):
        print("Invalid seat number.")
        return
    nseats = int(nseats)
    shows = _read_rows(SHOW_FILE)
    idx = -1
    for i, s in enumerate(shows):
        if s[0] == sid:
            idx = i
            break
    if idx == -1:
        print("Show not found.")
        return
    avail = int(shows[idx][5])
    if avail < nseats:
        print("Not enough seats available.")
        return

    # ---- Payment Section ----
    print("\n===== PAYMENT SECTION =====")
    print("1) Pay by Cash")
    print("2) Pay by Card")
    pay_choice = input("Select payment method (1/2): ").strip()

    if pay_choice == "1":
        payment_mode = "Cash"
    elif pay_choice == "2":
        payment_mode = "Card"
        while True:
            card_num = input("Enter card number (XXXX-XXXX-XXXX-XXXX): ").strip()
            if re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", card_num):
                break
            else:
                print("Invalid card format! Please try again.")
    else:
        print("Invalid payment option. Booking cancelled.")
        return

    # ---- Update seat count ----
    shows[idx][5] = str(avail - nseats)
    _write_all(SHOW_FILE, _read_header(SHOW_FILE), shows)

    # ---- Save booking ----
    bid = _next_id_from(BOOK_FILE)
    _append_line(BOOK_FILE, ",".join((bid, cname, sid, str(nseats), "PAID")))

    # ---- Receipt generation ----
    movies = load_movies_map()
    movie_name = movies.get(shows[idx][1], shows[idx][1])
    generate_receipt(bid, cname, movie_name, shows[idx][3], shows[idx][4], nseats)

    print(f"Payment successful ({payment_mode}).")
    print(f"Booking successful. ID={bid}")


def view_bookings():
    rows = _read_rows(BOOK_FILE)
    if not rows:
        print("No bookings."); return
    print("\nBookings:")
    for r in rows:
        print(" | ".join(r))

def cancel_or_modify_booking():
    view_bookings()
    bid = input("Enter Booking ID to cancel/modify: ").strip()
    return _cancel_or_modify_common(bid)

def _cancel_or_modify_common(bid, owner_name=None):
    books = _read_rows(BOOK_FILE)
    shows = _read_rows(SHOW_FILE)
    bidx = -1
    for i, b in enumerate(books):
        if b[0] == bid:
            bidx = i; break
    if bidx == -1:
        print("Booking not found."); return
    if owner_name is not None and books[bidx][1].lower() != owner_name.lower():
        print("You can only manage your own bookings."); return
    choice = input("Enter M to modify or C to cancel: ").strip().upper()
    sid = books[bidx][2]
    sidx = -1
    for i, s in enumerate(shows):
        if s[0] == sid:
            sidx = i; break
    if choice == "C":
        if sidx != -1:
            shows[sidx][5] = str(int(shows[sidx][5]) + int(books[bidx][3]))
            _write_all(SHOW_FILE, _read_header(SHOW_FILE), shows)
        books.pop(bidx)
        _write_all(BOOK_FILE, _read_header(BOOK_FILE), books)
        print("Booking cancelled.")
        return
    if choice == "M":
        new_seats = input("Enter new number of seats: ").strip()
        if not _ensure_positive_int(new_seats):
            print("Invalid seats."); return
        new_seats = int(new_seats)
        old_seats = int(books[bidx][3])
        diff = new_seats - old_seats
        if sidx == -1:
            print("Related show not found."); return
        avail = int(shows[sidx][5])
        if avail - diff < 0:
            print("Not enough seats to modify."); return
        shows[sidx][5] = str(avail - diff)
        _write_all(SHOW_FILE, _read_header(SHOW_FILE), shows)
        books[bidx][3] = str(new_seats)
        _write_all(BOOK_FILE, _read_header(BOOK_FILE), books)
        print("Booking modified.")
        return
    print("Invalid choice.")

# ---- Technician ----
def tech_view_upcoming_schedules():
    rows = _read_rows(SHOW_FILE)
    if not rows:
        print("\nNo showtimes found."); return
    def _key(r):
        dt = f"{r[3]} {r[4]}"
        return datetime.strptime(dt, DT_FMT) if _valid_datetime(dt) else datetime.max
    rows.sort(key=_key)
    movies = load_movies_map()
    auds = load_aud_map()
    eqp = load_eqp_map()
    print("\n-- Upcoming Schedules --")
    print("show_id | movie_title | auditorium | datetime | auditorium_status")
    for r in rows:
        dt = f"{r[3]} {r[4]}"
        print(f"{r[0]} | {movies.get(r[1], r[1])} | {auds.get(r[2], r[2])} | {dt} | {eqp.get(r[2], (EQ_READY,'',''))[0]}")

def tech_report_issue():
    auds = load_aud_map()
    if not auds:
        print("No auditoriums found. Add auditoriums first."); return
    aud_id = input("Auditorium ID: ").strip()
    if aud_id not in auds:
        print("Invalid auditorium ID."); return
    print("Issue types:", ", ".join(ISSUE_TYPES))
    issue_type = input("Enter issue type: ").strip().lower()
    if issue_type not in ISSUE_TYPES:
        print("Invalid issue type."); return
    details = input("Describe the issue (no commas): ").strip()
    if not _is_nonempty_no_comma(details):
        print("Invalid details."); return
    issue_id = "ISS" + f"{len(_read_rows(ISS_FILE))+1:04d}"
    created = _now_str()
    _append_line(ISS_FILE, ",".join([issue_id, aud_id, issue_type, details, STATUS_OPEN, created, "", ""]))
    print("Issue logged with ID:", issue_id)

def tech_view_issues():
    rows = _read_rows(ISS_FILE)
    if not rows:
        print("No issues logged."); return
    print("\n-- OPEN Issues --")
    for r in rows:
        if r[4] == STATUS_OPEN:
            print(f"{r[0]} | AUD={r[1]} | {r[2]} | {r[3]} | Created={r[5]}")
    print("\n-- RESOLVED Issues --")
    for r in rows:
        if r[4] == STATUS_RESOLVED:
            print(f"{r[0]} | AUD={r[1]} | {r[2]} | {r[3]} | Resolved={r[6]} by {r[7]}")

def tech_resolve_issue():
    rows = _read_rows(ISS_FILE)
    if not rows:
        print("No issues to resolve."); return
    issue_id = input("Enter issue ID to resolve: ").strip()
    resolved_by = input("Resolved by (technician name): ").strip()
    if not _is_nonempty_no_comma(resolved_by):
        print("Invalid name."); return
    header = _read_header(ISS_FILE)
    changed = False
    out = []
    for r in rows:
        if r[0] == issue_id and r[4] == STATUS_OPEN:
            r[4] = STATUS_RESOLVED
            r[6] = _now_str()
            r[7] = resolved_by
            changed = True
        out.append(r)
    _write_all(ISS_FILE, header, out)
    print("Issue resolved." if changed else "Issue not found or already resolved.")

def tech_mark_auditorium_status():
    auds = load_aud_map()
    if not auds:
        print("No auditoriums found."); return
    aud_id = input("Auditorium ID: ").strip()
    if aud_id not in auds:
        print("Invalid auditorium ID."); return
    status = input("Enter status (READY/MAINTENANCE): ").strip().upper()
    if status not in (EQ_READY, EQ_MAINT):
        print("Invalid status."); return
    note = input("Note (no commas, optional): ").strip()
    if "," in note:
        print("Note cannot contain comma."); return
    now = _now_str()
    header = _read_header(EQP_FILE)
    rows = _read_rows(EQP_FILE)
    found = False
    for r in rows:
        if r[0] == aud_id:
            r[1] = status; r[2] = now; r[3] = note; found = True
            break
    if not found:
        rows.append([aud_id, status, now, note])
    _write_all(EQP_FILE, header, rows)
    print(f"Auditorium {aud_id} status set to {status}.")

def tech_show_readiness_check():
    shows = _read_rows(SHOW_FILE)
    if not shows:
        print("No showtimes found."); return
    show_id = input("Enter show ID to check readiness: ").strip()
    sel = None
    for r in shows:
        if r[0] == show_id:
            sel = r; break
    if sel is None:
        print("Show ID not found."); return
    aud_id = sel[2]
    aud_status = load_eqp_map().get(aud_id, (EQ_READY,"",""))[0]
    print("\n-- Readiness Checklist (y/n) --")
    p = input("Projector OK? (y/n): ").strip().lower()
    s = input("Sound OK? (y/n): ").strip().lower()
    a = input("Air conditioner OK? (y/n): ").strip().lower()
    all_ok = (p == "y" and s == "y" and a == "y")
    if aud_status != EQ_READY:
        print(f"Auditorium status is {aud_status}. Not ready."); return
    print("Show is READY to start." if all_ok else "Show is NOT ready. Please log issues or set maintenance.")

# ---- Customer (Self-service) ----
def _print_shows(rows):
    movies = load_movies_map()
    auds = load_aud_map()
    for r in rows:
        mid = r[1]; aid = r[2]
        print(f"{r[0]} | {movies.get(mid, mid)} | {auds.get(aid, aid)} | {r[3]} {r[4]} | seats={r[5]} | price={r[6]}")

def customer_search_by_date(date):
    if not DATE_RE.match(date):
        print("Invalid date format. Use YYYY-MM-DD."); return
    rows = [r for r in _read_rows(SHOW_FILE) if r[3] == date]
    if not rows:
        print("No shows on that date."); return
    _print_shows(rows)

def customer_search_by_movie(keyword):
    kw = keyword.strip().lower()
    if not kw:
        print("Enter a movie keyword."); return
    movies = load_movies_map()
    ids = [mid for mid, title in movies.items() if kw in title.lower()]
    rows = [r for r in _read_rows(SHOW_FILE) if r[1] in ids]
    if not rows:
        print("No shows for that movie keyword."); return
    _print_shows(rows)

def customer_view_bookings(name):
    rows = _read_rows(BOOK_FILE)
    mine = [r for r in rows if r[1].lower() == name.lower()]
    if not mine:
        print("You have no bookings."); return
    print("\nYour Bookings:")
    for r in mine:
        print(" | ".join(r))

def customer_book_ticket(name):
    view_shows()
    sid = input("Enter ShowID to book: ").strip()
    return _book_ticket_common(sid, name)

def customer_cancel_or_modify(name):
    customer_view_bookings(name)
    bid = input("Enter your Booking ID to cancel/modify: ").strip()
    return _cancel_or_modify_common(bid, owner_name=name)

def customer_menu():
    name = input("\nEnter your name (for booking records): ").strip()
    if not _is_nonempty_no_comma(name):
        print("Invalid name."); return
    while True:
        print("\n===== Customer Menu =====")
        print("1) View Movies")
        print("2) View All Shows")
        print("3) Search Shows by Date")
        print("4) Search Shows by Movie Title")
        print("5) Book Ticket")
        print("6) View My Bookings")
        print("7) Cancel/Modify My Booking")
        print("0) Exit")
        c = input("Choice: ").strip()
        if c == "1": view_movies()
        elif c == "2": view_shows()
        elif c == "3":
            d = input("Enter date (YYYY-MM-DD): ").strip()
            customer_search_by_date(d)
        elif c == "4":
            kw = input("Enter movie keyword: ").strip()
            customer_search_by_movie(kw)
        elif c == "5":
            customer_book_ticket(name)
        elif c == "6":
            customer_view_bookings(name)
        elif c == "7":
            customer_cancel_or_modify(name)
        elif c == "0":
            break
        else:
            print("Invalid choice.")

# ---- Menus ----
def manager_menu():
    while True:
        print("\n===== Cinema Manager Menu =====")
        print("1) Add Auditorium")
        print("2) View Auditoriums")
        print("3) Add Movie")
        print("4) Update Movie")
        print("5) Remove Movie")
        print("6) View Movies")
        print("7) Add Show")
        print("8) Update Show")
        print("9) Remove Show")
        print("10) View Shows")
        print("0) Exit")
        c = input("Choice: ").strip()
        if c == "1": add_auditorium()
        elif c == "2": view_auditoriums()
        elif c == "3": add_movie()
        elif c == "4": upd_movie()
        elif c == "5": del_movie()
        elif c == "6": view_movies()
        elif c == "7": add_show()
        elif c == "8": upd_show()
        elif c == "9": del_show()
        elif c == "10": view_shows()
        elif c == "0": break
        else: print("Invalid choice.")

def clerk_menu():
    while True:
        print("\n===== Ticketing Clerk Menu =====")
        print("1) View Shows")
        print("2) View Seat Availability")
        print("3) Book Ticket")
        print("4) View Bookings")
        print("5) Cancel/Modify Booking")
        print("0) Exit")
        c = input("Choice: ").strip()
        if c == "1": view_shows()
        elif c == "2": view_seats()
        elif c == "3": book_ticket()
        elif c == "4": view_bookings()
        elif c == "5": cancel_or_modify_booking()
        elif c == "0": break
        else: print("Invalid choice.Try again")

def technician_menu():
    while True:
        print("\n=== TECHNICIAN MENU ===")
        print("1) View upcoming schedules")
        print("2) Report technical issue")
        print("3) View issue board")
        print("4) Resolve an issue")
        print("5) Mark auditorium READY/MAINTENANCE")
        print("6) Readiness checklist for a show")
        print("0) Exit")
        choice = input("Select option: ").strip()
        if choice == "1": tech_view_upcoming_schedules()
        elif choice == "2": tech_report_issue()
        elif choice == "3": tech_view_issues()
        elif choice == "4": tech_resolve_issue()
        elif choice == "5": tech_mark_auditorium_status()
        elif choice == "6": tech_show_readiness_check()
        elif choice == "0": break
        else: print("Invalid option. Try again.")

def role_menu_after_login():
    while True:
        print("\n===== Select Role =====")
        print("1) Cinema Manager")
        print("2) Ticketing Clerk")
        print("3) Technician")
        print("4) Customer (Self-service)")
        print("0) Logout")
        r = input("Choice: ").strip()
        if r == "1": manager_menu()
        elif r == "2": clerk_menu()
        elif r == "3": technician_menu()
        elif r == "4": customer_menu()
        elif r == "0": break
        else: print("Invalid choice.")

def start_program():
    ensure_files()
    while True:
        print("\n===== Cinema Ticketing System =====")
        print("1) Register")
        print("2) Login")
        print("0) Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            register_user()
        elif choice == "2":
            if login_user():
                role_menu_after_login()
        elif choice == "0":
            print("Goodbye!"); break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    start_program()
