import os
import random
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__, static_url_path='/static')

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.environ.get('DB_PASSWORD'),
    'database': 'prowresdb',
}

# Connect to MySQL
conn = mysql.connector.connect(**db_config)


@app.route('/')
def events():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling events from the database
    query = """
        SELECT event.event_id, event_name, rating
        FROM (SELECT prowresdb.`review-event`.event_id, AVG(rating) AS rating
        FROM prowresdb.`review-event`
        GROUP BY prowresdb.`review-event`.event_id) AS avg
        right JOIN prowresdb.event ON avg.event_id = prowresdb.event.event_id
        ORDER BY rating DESC
        """
    cursor.execute(query)
    events = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of events
    return render_template('events.html', title='Wrestling Events', data=events)


@app.route('/matches')
def matches():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling matches from the database
    query = """
        SELECT m.event_id, m.match_id, m.type, e.event_name, AVG(urm.rating) AS rating
        FROM `match` m
        JOIN event e ON m.event_id = e.event_id
        LEFT JOIN user_reviews_match urm ON m.event_id = urm.event_id AND m.match_id = urm.match_id
        GROUP BY m.event_id, m.match_id, e.event_name
        ORDER BY rating DESC;

    """
    cursor.execute(query)
    matches = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of matches
    return render_template('matches.html', title='Wrestling Matches', matches=matches)


@app.route('/wrestlers')
def wrestlers():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling matches from the database
    query = """
        SELECT w.wrestler_id, w.wrestler_name, avg(urw.rating) as rating
        from wrestler w
        left join user_reviews_wrestler urw on w.wrestler_id = urw.wrestler_id
        GROUP BY w.wrestler_id
        ORDER BY rating DESC;
    """
    cursor.execute(query)
    wrestlers = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of matches
    return render_template('wrestlers.html', title='Wrestlers', wrestlers=wrestlers)


@app.route('/promotions')
def promotions():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling matches from the database
    query = """
        SELECT p.promotion_id, p.promotion_name, avg(urp.rating) as rating
        from promotion p
        left join user_reviews_promotion urp on p.promotion_id = urp.promotion_id
        GROUP BY p.promotion_id
        ORDER BY rating DESC;
    """
    cursor.execute(query)
    promotions = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of matches
    return render_template('promotions.html', title='Promotions', promotions=promotions)


@app.route('/match/<int:event_id>/<int:match_id>')
def match_detail(event_id, match_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch match details based on both event_id and match_id
    match_query = """
        SELECT m.event_id, m.match_id, m.type, e.event_name, AVG(urm.rating) AS rating
        from `match` m
        join event e ON m.event_id = e.event_id
        LEFT JOIN user_reviews_match urm ON m.event_id = urm.event_id AND m.match_id = urm.match_id
        where m.event_id = %s and m.match_id = %s
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

    # Fetch wrestlers for the match
    wrestlers_query = """
                    SELECT
                        w.wrestler_id,
                        w.wrestler_name,
                        m.match_id,
                        m.event_id,
                        AVG(wr.rating) AS rating
                    FROM
                        wrestler w
                    JOIN
                        match_has_wrestler mw ON w.wrestler_id = mw.wrestler_id
                    JOIN
                        `match` m ON mw.match_id = m.match_id and mw.event_id = m.event_id
                    LEFT JOIN
                        user_reviews_wrestler wr ON w.wrestler_id = wr.wrestler_id
                    WHERE mw.event_id = %s and mw.match_id = %s
                    GROUP BY
                        w.wrestler_id;
                    """
    cursor.execute(wrestlers_query, (event_id, match_id))
    wrestlers = cursor.fetchall()

    cursor.close()

    # Render the HTML template with match details
    return render_template('match_detail.html', title='Match Details', match=match, reviews=reviews, wrestlers=wrestlers)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch event details based on event_id
    query = """
    select * 
    from (
    SELECT event.event_id, event_name, stadium_id, rating, date, attendance
    FROM (SELECT prowresdb.`review-event`.event_id, AVG(rating) AS rating
    FROM prowresdb.`review-event`
    GROUP BY prowresdb.`review-event`.event_id) AS avg
    right JOIN prowresdb.event ON avg.event_id = prowresdb.event.event_id) as ev_rating 
    join stadium on ev_rating.stadium_id = stadium.stadium_id WHERE ev_rating.event_id = %s
    """
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


@app.route('/wrestler/<int:wrestler_id>')
def wrestler_detail(wrestler_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestler details based on wrestler_id
    wrestler_query = """
        SELECT w.wrestler_id, w.wrestler_name, avg(urw.rating) as rating, w.date_of_birth, w.date_of_death
        , w.weight_class, w.gender
        from wrestler w
        left join user_reviews_wrestler urw on w.wrestler_id = urw.wrestler_id
        where w.wrestler_id = %s
    """
    cursor.execute(wrestler_query, (wrestler_id,))
    wrestler = cursor.fetchone()

    # Fetch reviews for the match
    review_query = """
            SELECT * 
            FROM user_reviews_wrestler urw
            join `user` on `user`.user_id = urw.user_id 
            where urw.wrestler_id = %s """
    cursor.execute(review_query, (wrestler_id,))
    reviews = cursor.fetchall()

    cursor.close()

    # Render the HTML template with match details
    return render_template('wrestler_detail.html', title='Wrestler Details', wrestler=wrestler, reviews=reviews)


@app.route('/promotion/<int:promotion_id>')
def promotion_detail(promotion_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestler details based on wrestler_id
    promotion_query = """
        SELECT p.promotion_id, p.promotion_name, avg(urp.rating) as rating, p.date_found, p.owner, p.location
        from promotion p
        left join user_reviews_promotion urp on p.promotion_id = urp.promotion_id
        where p.promotion_id = %s
    """
    cursor.execute(promotion_query, (promotion_id,))
    promotion = cursor.fetchone()

    # Fetch reviews for the match
    review_query = """
            SELECT * 
            FROM user_reviews_promotion urp
            join `user` on `user`.user_id = urp.user_id 
            where urp.promotion_id = %s """
    cursor.execute(review_query, (promotion_id,))
    reviews = cursor.fetchall()

    cursor.close()

    # Render the HTML template with match details
    return render_template('promotion_detail.html', title='Promotion Details', promotion=promotion, reviews=reviews)


@app.route('/submit_match_review/<int:event_id>/<int:match_id>', methods=['POST'])
def submit_match_review(event_id, match_id):
    cursor = conn.cursor()

    # Get review details from the form
    review_id = random.randint(1, 9999)  # Should change tables' primary keys to AUTO_INCREMENT
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


@app.route('/submit_wrestler_review/<int:wrestler_id>', methods=['POST'])
def submit_wrestler_review(wrestler_id):
    cursor = conn.cursor()

    # Get review details from the form
    review_id = random.randint(1, 9999)  # Should change tables' primary keys to AUTO_INCREMENT
    user_id = 123
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rating = request.form.get('rating')
    text = request.form.get('text')

    # Insert the review into the database
    review_query = "INSERT INTO user_reviews_wrestler (review_id, wrestler_id, user_id, rating, text, " \
                   "date) VALUES (%s, %s, %s, %s, %s, %s) "
    cursor.execute(review_query, (review_id, wrestler_id, user_id, rating, text, current_date))
    conn.commit()

    cursor.close()

    # Redirect back to the event detail page
    return redirect(url_for('wrestler_detail', wrestler_id=wrestler_id))


@app.route('/submit_promotion_review/<int:promotion_id>', methods=['POST'])
def submit_promotion_review(promotion_id):
    cursor = conn.cursor()

    # Get review details from the form
    review_id = random.randint(1, 9999)  # Should change tables' primary keys to AUTO_INCREMENT
    user_id = 123
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rating = request.form.get('rating')
    text = request.form.get('text')

    # Insert the review into the database
    review_query = "INSERT INTO user_reviews_promotion (review_id, promotion_id, user_id, rating, text, " \
                   "date) VALUES (%s, %s, %s, %s, %s, %s) "
    cursor.execute(review_query, (review_id, promotion_id, user_id, rating, text, current_date))
    conn.commit()

    cursor.close()

    # Redirect back to the event detail page
    return redirect(url_for('promotion_detail', promotion_id=promotion_id))


if __name__ == '__main__':
    app.run(debug=True)
