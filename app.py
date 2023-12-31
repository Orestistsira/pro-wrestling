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
        RIGHT JOIN prowresdb.event ON avg.event_id = prowresdb.event.event_id
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
        FROM wrestler w
        LEFT JOIN user_reviews_wrestler urw ON w.wrestler_id = urw.wrestler_id
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
        FROM promotion p
        LEFT JOIN user_reviews_promotion urp ON p.promotion_id = urp.promotion_id
        GROUP BY p.promotion_id
        ORDER BY rating DESC;
    """
    cursor.execute(query)
    promotions = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of matches
    return render_template('promotions.html', title='Promotions', promotions=promotions)


@app.route('/titles')
def titles():
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestling titles from the database
    query = """
        SELECT t.title_id, t.title_name
        FROM title t
    """
    cursor.execute(query)
    titles = cursor.fetchall()

    cursor.close()

    # Render the HTML template with the list of titles
    return render_template('titles.html', title='Titles', titles=titles)


@app.route('/match/<int:event_id>/<int:match_id>')
def match_detail(event_id, match_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch match details based on both event_id and match_id
    match_query = """
        SELECT m.event_id, m.match_id, m.type, m.title_id, t.title_name, e.event_name, AVG(urm.rating) AS rating
        FROM `match` m
        JOIN event e ON m.event_id = e.event_id
        LEFT JOIN user_reviews_match urm ON m.event_id = urm.event_id AND m.match_id = urm.match_id
        LEFT JOIN title t on t.title_id = m.title_id
        WHERE m.event_id = %s AND m.match_id = %s
    """
    cursor.execute(match_query, (event_id, match_id))
    match = cursor.fetchone()

    # Fetch reviews for the match
    review_query = """SELECT * 
                    FROM user_reviews_match
                    JOIN `user` ON `user`.user_id = user_reviews_match.user_id 
                    WHERE event_id = %s AND match_id = %s """
    cursor.execute(review_query, (event_id, match_id))
    reviews = cursor.fetchall()

    # Fetch wrestlers for the match
    wrestlers_query = """
                    SELECT
                        w.wrestler_id,
                        w.wrestler_name,
                        m.match_id,
                        m.event_id,
                        mw.winner,
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
    SELECT * 
    FROM (
    SELECT event.event_id, event_name, stadium_id, rating, date, attendance
    FROM (SELECT prowresdb.`review-event`.event_id, AVG(rating) AS rating
    FROM prowresdb.`review-event`
    GROUP BY prowresdb.`review-event`.event_id) AS avg
    RIGHT JOIN prowresdb.event ON avg.event_id = prowresdb.event.event_id) as ev_rating 
    JOIN stadium ON ev_rating.stadium_id = stadium.stadium_id WHERE ev_rating.event_id = %s
    """
    cursor.execute(query, (event_id,))
    event = cursor.fetchone()

    # Fetch matches for the event
    match_query = "SELECT * FROM `match-event` JOIN `match` ON `match-event`.event_id = `match`.event_id AND " \
                  "`match-event`.match_id = `match`.match_id WHERE `match-event`.event_id = %s "
    cursor.execute(match_query, (event_id,))
    matches = cursor.fetchall()

    # Fetch matches for the event
    promotions_query = """
        SELECT
            p.promotion_id,
            p.promotion_name,
            AVG(urp.rating) AS rating
        FROM
            promotion p
        JOIN
            promotion_has_event phe ON p.promotion_id = phe.promotion_id
        LEFT JOIN
            user_reviews_promotion urp ON p.promotion_id = urp.promotion_id
        WHERE phe.event_id = %s
        GROUP BY
            p.promotion_id;
    """
    cursor.execute(promotions_query, (event_id,))
    promotions = cursor.fetchall()

    cursor.close()

    # Render the HTML template with event details and matches
    return render_template('event_detail.html', title='Event Details', event=event, matches=matches, promotions=promotions)


@app.route('/wrestler/<int:wrestler_id>')
def wrestler_detail(wrestler_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch wrestler details based on wrestler_id
    wrestler_query = """
        SELECT w.wrestler_id, w.wrestler_name, avg(urw.rating) as rating, w.date_of_birth, w.date_of_death
        , w.weight_class, w.gender
        FROM wrestler w
        LEFT JOIN user_reviews_wrestler urw ON w.wrestler_id = urw.wrestler_id
        WHERE w.wrestler_id = %s
    """
    cursor.execute(wrestler_query, (wrestler_id,))
    wrestler = cursor.fetchone()

    # Fetch reviews for the wrestler
    review_query = """
            SELECT * 
            FROM user_reviews_wrestler urw
            JOIN `user` ON `user`.user_id = urw.user_id 
            WHERE urw.wrestler_id = %s """
    cursor.execute(review_query, (wrestler_id,))
    reviews = cursor.fetchall()

    cursor.close()

    # Render the HTML template with wrestler details
    return render_template('wrestler_detail.html', title='Wrestler Details', wrestler=wrestler, reviews=reviews)


@app.route('/promotion/<int:promotion_id>')
def promotion_detail(promotion_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch promotion details based on promotion_id
    promotion_query = """
        SELECT p.promotion_id, p.promotion_name, avg(urp.rating) as rating, p.date_found, p.owner, p.location
        FROM promotion p
        LEFT JOIN user_reviews_promotion urp ON p.promotion_id = urp.promotion_id
        WHERE p.promotion_id = %s
    """
    cursor.execute(promotion_query, (promotion_id,))
    promotion = cursor.fetchone()

    # Fetch reviews for the match
    review_query = """
            SELECT * 
            FROM user_reviews_promotion urp
            JOIN `user` ON `user`.user_id = urp.user_id 
            WHERE urp.promotion_id = %s """
    cursor.execute(review_query, (promotion_id,))
    reviews = cursor.fetchall()

    cursor.close()

    # Render the HTML template with promotion details
    return render_template('promotion_detail.html', title='Promotion Details', promotion=promotion, reviews=reviews)


@app.route('/title/<int:title_id>')
def title_detail(title_id):
    cursor = conn.cursor(dictionary=True)

    # Fetch title details based on title_id
    title_query = """
        SELECT *
        FROM title t
        WHERE t.title_id = %s
    """
    cursor.execute(title_query, (title_id,))
    t = cursor.fetchone()

    title_holder_query = """
            SELECT th.wrestler_id, th.match_id, th.event_id, th.event_name, th.date, w.wrestler_name, m.type
            FROM (SELECT *,
                ROW_NUMBER() OVER (PARTITION BY prowresdb.`title-wrestler`.title_id ORDER BY prowresdb.`title-wrestler`.date DESC) AS rn
              FROM
                prowresdb.`title-wrestler`
              WHERE winner = true and title_id = %s
            ) AS th
            JOIN wrestler w ON w.wrestler_id = th.wrestler_id
            JOIN `match` m ON m.match_id = th.match_id and m.event_id = th.event_id
            WHERE rn=1
        """
    cursor.execute(title_holder_query, (title_id,))
    title_holder = cursor.fetchone()

    cursor.close()

    # Render the HTML template with title details
    return render_template('title_detail.html', title='Title Details', t=t, title_holder=title_holder)


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
