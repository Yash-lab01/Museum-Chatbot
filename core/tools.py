import difflib
from datetime import datetime
from langchain_core.tools import tool
from core.db import get_db_connection

def fuzzy_match(query, choices, threshold=0.6):
    """Helper to find close string matches or substring matches."""
    q = query.lower()
    # 1. First try simple substring matching (highly accurate)
    substring_matches = [c for c in choices if q in c.lower()]
    if substring_matches:
        return substring_matches
        
    # 2. Fall back to fuzzy matching (stricter threshold)
    matches = difflib.get_close_matches(q, [c.lower() for c in choices], n=5, cutoff=threshold)
    return [c for c in choices if c.lower() in matches]

@tool
def search_museums_tool(query: str = None, needs_wheelchair: bool = False) -> str:
    """
    Search for museums by name, city, or state/region. Uses fuzzy matching.
    Pass needs_wheelchair as True if accessibility is required.
    Always use this tool first to find the exact Museum Name and City before booking or getting details.
    Examples: query="Kolkata", query="Rajasthan", query="Indian Museum", query="science"
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT Name, City, State_UT, Timings, Overview FROM museum_data WHERE 1=1"
        if needs_wheelchair:
            sql += " AND Wheelchair = 1"
            
        cursor.execute(sql)
        all_museums = cursor.fetchall()
        
        if not all_museums:
            return "No museums found in the database."

        if not query:
            results = all_museums[:5]
        else:
            names = list(set([m['Name'] for m in all_museums]))
            cities = list(set([m['City'] for m in all_museums]))
            states = list(set([m['State_UT'] for m in all_museums if m.get('State_UT')]))
            
            matched_names = fuzzy_match(query, names)
            matched_cities = fuzzy_match(query, cities)
            matched_states = fuzzy_match(query, states)
            
            results = [m for m in all_museums 
                       if m['Name'] in matched_names 
                       or m['City'] in matched_cities 
                       or m.get('State_UT', '') in matched_states]

        if not results:
            return f"Could not find any museums matching '{query}'. Please ask the user to clarify."
        
        # Cap results to avoid flooding context
        total_found = len(results)
        display_results = results[:10]
            
        response = f"Found {total_found} matching museums"
        if total_found > 10:
            response += f" (showing first 10)"
        response += ":\n"
        for row in display_results:
            response += f"- **{row['Name']}** in **{row['City']}**, {row.get('State_UT', '')} (Open: {row['Timings']})\n"
        
        response += "\nIMPORTANT: If the user wants to book or get details, make sure you know both the EXACT Name and EXACT City from the list above. If there are multiple museums with the same name, ask the user to clarify which city they mean."
        return response
    finally:
        conn.close()

@tool
def get_museum_details_tool(museum_name: str, city: str) -> str:
    """
    Get detailed information about a specific museum.
    Requires exact museum_name and city from the search_museums_tool.
    Returns address, facilities, pricing, etc.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM museum_data WHERE Name = %s AND City = %s", (museum_name, city))
        record = cursor.fetchone()
        
        if not record:
            return f"Could not find exact match for {museum_name} in {city}. Please search again."
            
        details = f"Details for {record['Name']} ({record['City']}):\n"
        details += f"Address: {record['Address']}, {record['State_UT']}\n"
        details += f"Theme: {record['Theme']} (Est. {record['Year_of_Establishment']})\n"
        details += f"Facilities: {record['Facilities']}\n"
        details += f"Admission Rules: {record['Admission']}\n"
        details += f"Adult Price: ₹{record['Adult_Price']} | Child Price: ₹{record['Child_Price']}\n"
        details += f"Timings: {record['Timings']} (Closed on {record['Closed_Days']})\n"
        details += f"Overview: {record['Overview']}\n"
        return details
    finally:
        conn.close()

@tool
def book_ticket_tool(museum_name: str, city: str, booking_date: str, adult_count: int, child_count: int) -> str:
    """
    Book tickets. Requires EXACT museum_name and city, booking_date (YYYY-MM-DD), and counts.
    """
    try:
        b_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        if b_date < datetime.today().date():
            return "Error: Cannot book tickets for a date in the past."
    except ValueError:
        return "Error: Invalid date format. Use YYYY-MM-DD."

    total_requested = adult_count + child_count
    if total_requested <= 0:
        return "Error: Must book at least 1 ticket."

    conn = get_db_connection()
    try:
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        
        # Get pricing
        cursor.execute("SELECT Adult_Price, Child_Price FROM museum_data WHERE Name = %s AND City = %s", (museum_name, city))
        museum = cursor.fetchone()
        
        if not museum:
            return f"Error: Museum '{museum_name}' in '{city}' not found."
            
        adult_price = float(museum['Adult_Price'] or 0)
        child_price = float(museum['Child_Price'] or 0)
        total_price = (adult_count * adult_price) + (child_count * child_price)
        
        combined_name = f"{museum_name} ({city})"
        
        # Lock the rows for this museum and date
        cursor.execute("SELECT SUM(adults + children) as booked FROM bookings WHERE museum_name = %s AND booking_date = %s FOR UPDATE", (combined_name, booking_date))
        booked_record = cursor.fetchone()
        tickets_booked = int(booked_record['booked'] or 0) if booked_record and booked_record['booked'] else 0
        
        max_capacity = 50
        available_tickets = max_capacity - tickets_booked
        
        if total_requested > available_tickets:
            conn.rollback()
            return f"Booking failed. Only {available_tickets} tickets left for {combined_name} on {booking_date}."
            
        # Insert booking
        cursor.execute(
            "INSERT INTO bookings (museum_name, booking_date, adults, children, total_price) VALUES (%s, %s, %s, %s, %s)",
            (combined_name, booking_date, adult_count, child_count, total_price)
        )
        
        conn.commit()
        return f"Success! Booked {adult_count} Adults and {child_count} Children for {combined_name} on {booking_date}. Total Price: ₹{total_price}."
        
    except Exception as e:
        conn.rollback()
        return f"Database error during booking: {e}"
    finally:
        conn.close()