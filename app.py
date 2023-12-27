import random
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__, static_url_path='/static')

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '85|uvdZOq9{M',
    'database': 'prowresdb',
}

# Connect to MySQL
conn = mysql.connector.connect(**db_config)


@app.route('/')
def index():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling events from the database
    query = "SELECT * FROM event"
    cursor.execute(query)
    events = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of events
    return render_template('index.html', title='Wrestling Events', data=events)


@app.route('/matches')
def matches():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling matches from the database
    query = "SELECT * FROM `match`"
    cursor.execute(query)
    matches = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of matches
    return render_template('matches.html', title='Wrestling Matches', data=matches)


@app.route('/match/<int:event_id>/<int:match_id>')
def match_detail(event_id, match_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch match details based on both event_id and match_id
    match_query = """
        SELECT * from `match` where `match`.event_id = %s AND `match`.match_id = %s
    """
    cursor.execute(match_query, (event_id, match_id))
    match = cursor.fetchone()

    # Fetch reviews for the match
    review_query = """SELECT * 
                    FROM user_reviews_match
                    join `user` on `user`.user_id = user_reviews_match.user_id 
                    where event_id = %s and match_id = %s """
    cursor.execute(review_query, (event_id, match_id))
    reviews = cursor.fetchall()

    cursor.close()

    # Render the HTML template with match details
    return render_template('match_detail.html', title='Match Details', match=match, reviews=reviews)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch event details based on event_id
    query = "SELECT * FROM event join stadium on event.stadium_id = stadium.stadium_id WHERE event_id = %s"
    cursor.execute(query, (event_id,))
    event = cursor.fetchone()

    # Fetch matches for the event
    match_query = "select * from `match-event` join `match` on `match-event`.event_id = `match`.event_id and " \
                  "`match-event`.match_id = `match`.match_id WHERE `match-event`.event_id = %s "
    cursor.execute(match_query, (event_id,))
    matches = cursor.fetchall()

    cursor.close()

    # Render the HTML template with event details and matches
    return render_template('event_detail.html', title='Event Details', event=event, matches=matches)


@app.route('/submit_match_review/<int:event_id>/<int:match_id>', methods=['POST'])
def submit_match_review(event_id, match_id):
    cursor = conn.cursor()

    # Get review details from the form
    review_id = random.randint(1, 9999)  # Should change tables' primary keys to AUTO_INCREMENT
    print(review_id)
    user_id = 123
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rating = request.form.get('rating')
    text = request.form.get('text')

    # Insert the review into the database
    review_query = "INSERT INTO user_reviews_match (review_id, event_id, match_id, user_id, rating, text, " \
                   "date) VALUES (%s, %s, %s, %s, %s, %s, %s) "
    cursor.execute(review_query, (review_id, event_id, match_id, user_id, rating, text, current_date))
    conn.commit()

    cursor.close()

    # Redirect back to the event detail page
    return redirect(url_for('match_detail', event_id=event_id, match_id=match_id))


if __name__ == '__main__':
    app.run(debug=True)
