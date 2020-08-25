#!/usr/bin/env python\r\n
# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort,
    jsonify,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, desc
import logging
from logging import Formatter, FileHandler
from flask_migrate import Migrate
from datetime import datetime
import time
from forms import ArtistForm, VenueForm, ShowForm, SearchForm
import sys


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database [Done]

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = "show"
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)
    artist_id = db.Column(
        db.Integer, db.ForeignKey("artist.id"), nullable=False
    )
    start_time = db.Column(db.DateTime(), nullable=False)
    artist = db.relationship("Artist", back_populates="parents")
    venue = db.relationship("Venue", back_populates="children")

    def __repr__(self):
        return f"<venue {self.venue_id} {self.artist_id} {self.start_time}>"


class Venue(db.Model):
    __tablename__ = "venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean(), default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    children = db.relationship("Show", back_populates="venue")

    def __repr__(self):
        return f"<venue {self.id} {self.name}>"

    # TODO: implement any missing fields, as a database migration using Flask-Migrate [Done]


class Artist(db.Model):
    __tablename__ = "artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    website = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_venue = db.Column(db.Boolean(), default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    parents = db.relationship("Show", back_populates="artist")

    def __repr__(self):
        return f"<artist {self.id} {self.name}>"

    # TODO: implement any missing fields, as a database migration using Flask-Migrate [Done]


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration. [Done]

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEE MM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en_US")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    recent_artists = Artist.query.order_by(desc(Artist.id)).limit(10).all()
    recent_venues = Venue.query.order_by(desc(Venue.id)).limit(10).all()
    return render_template(
        "pages/home.html", artists=recent_artists, venues=recent_venues
    )


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: replace with real venues data. [done]
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    form = SearchForm()
    data = []
    citys = (
        Venue.query.distinct(Venue.city, Venue.state)
        .with_entities(Venue.city, Venue.state)
        .order_by(Venue.state, Venue.city)
        .all()
    )
    for city in citys:
        city_data = {}
        city_data["city"] = city.city
        city_data["state"] = city.state
        venues = Venue.query.filter(
            and_(Venue.city == city.city, Venue.state == city.state)
        ).all()
        city_data["venues"] = []
        for venue in venues:
            venue_data = {}
            venue_data["id"] = venue.id
            venue_data["name"] = venue.name
            city_data["venues"].append(venue_data)
        data.append(city_data)
    return render_template("pages/venues.html", areas=data, form=form)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # [done] TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_form = request.form
    if "search_term" in search_form:
        search_term = search_form.get("search_term", "")
        if search_term:
            search_term = "%{}%".format(search_term)
            res = (
                Venue.query.filter(Venue.name.like(search_term))
                .order_by(Venue.id)
                .all()
            )
            response = {}
            response["count"] = len(res)
            response["data"] = []
            for r in res:
                r_data = {
                    "id": r.id,
                    "name": r.name,
                }
                response["data"].append(r_data)

            return render_template(
                "pages/search_venues.html",
                results=response,
                search_term=search_form["search_term"],
            )
    if "city" in search_form:
        city = search_form["city"]
        state = search_form["state"]
        res = (
            Venue.query.filter(and_(Venue.city == city, Venue.state == state))
            .order_by(Venue.id)
            .all()
        )
        response = {}
        response["count"] = len(res)
        response["data"] = []
        for r in res:
            r_data = {
                "id": r.id,
                "name": r.name,
            }
            response["data"].append(r_data)

        return render_template(
            "pages/search_venues.html",
            results=response,
            search_term="{} {}".format(city, state),
        )

    return redirect(url_for("venues"))


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # [done] TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    genres_list = venue.genres[1:-1].split(",")
    venue_data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [genre.strip('"') for genre in genres_list],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    now = datetime.today()
    past_shows_data = Show.query.filter(
        and_(Show.start_time <= now, Show.venue_id == venue_id)
    ).all()
    past_shows = []
    for data in past_shows_data:
        artist = Artist.query.get(data.artist_id)
        past_show = {
            "artint_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(data.start_time),
        }
        past_shows.append(past_show)
    venue_data["past_shows"] = past_shows
    venue_data["past_shows_count"] = len(past_shows)

    upcoming_shows_data = Show.query.filter(
        and_(Show.start_time > now, Show.venue_id == venue_id)
    ).all()
    upcoming_shows = []
    for data in upcoming_shows_data:
        artist = Artist.query.get(data.artist_id)
        upcoming_show = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(data.start_time),
        }
        upcoming_shows.append(upcoming_show)
    venue_data["upcoming_shows"] = upcoming_shows
    venue_data["upcoming_shows_count"] = len(upcoming_shows)
    return render_template("pages/show_venue.html", venue=venue_data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # [done] TODO: insert form data as a new Venue record in the db, instead
    # [done] TODO: modify data to be the data object returned from db insertion
    error = False
    venue_info = request.form
    venue_info = venue_info.to_dict(flat=False)
    try:
        venue = Venue(
            name=venue_info["name"][0],
            image_link=venue_info["image_link"][0],
            city=venue_info["city"][0],
            state=venue_info["state"][0],
            address=venue_info["address"][0],
            phone=venue_info["phone"][0],
            genres=venue_info["genres"],
            website=venue_info["website"][0],
            facebook_link=venue_info["facebook_link"][0],
            seeking_talent=True if "seeking_talent" in venue_info else False,
            seeking_description=venue_info["seeking_description"][0],
        )
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash("Venue " + venue_info["name"][0] + " was successfully listed!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue "
            + venue_info["name"]
            + " could not be listed."
        )
    finally:
        db.session.close()

    # [done] TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        name = venue.name
        for show in venue.children:
            db.session.delete(show)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        flash(name + " is deleted successfully.")
        return jsonify({"success": True})
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # [done] TODO: replace with real data returned from querying the database
    form = SearchForm()
    data = []
    artists = Artist.query.order_by("name").all()
    for artist in artists:
        artist_data = {"id": artist.id, "name": artist.name}
        data.append(artist_data)

    return render_template("pages/artists.html", artists=data, form=form)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # [done]TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_form = request.form
    if "search_term" in search_form:
        search_term = search_form.get("search_term", "")
        if search_term:
            search_term = "%{}%".format(search_term)
            res = (
                Artist.query.filter(Artist.name.like(search_term))
                .order_by(Artist.id)
                .all()
            )
            response = {}
            response["count"] = len(res)
            response["data"] = []
            for r in res:
                r_data = {
                    "id": r.id,
                    "name": r.name,
                }
                response["data"].append(r_data)

            return render_template(
                "pages/search_artists.html",
                results=response,
                search_term=search_form["search_term"],
            )
    if "city" in search_form:
        city = search_form["city"]
        state = search_form["state"]
        res = (
            Artist.query.filter(
                and_(Artist.city == city, Artist.state == state)
            )
            .order_by(Artist.id)
            .all()
        )
        response = {}
        response["count"] = len(res)
        response["data"] = []
        for r in res:
            r_data = {
                "id": r.id,
                "name": r.name,
            }
            response["data"].append(r_data)

        return render_template(
            "pages/search_artists.html",
            results=response,
            search_term="{} {}".format(city, state),
        )

    return redirect(url_for("artists"))


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # [Done] TODO: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.get(artist_id)
    genres_list = artist.genres[1:-1].split(",")
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [genre.strip('"') for genre in genres_list],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }
    now = datetime.today()
    past_shows_data = Show.query.filter(
        and_(Show.start_time <= now, Show.artist_id == artist_id)
    ).all()
    past_shows = []
    for data in past_shows_data:
        venue = Venue.query.get(data.venue_id)
        past_show = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(data.start_time),
        }
        past_shows.append(past_show)
    artist_data["past_shows"] = past_shows
    artist_data["past_shows_count"] = len(past_shows)

    upcoming_shows_data = Show.query.filter(
        and_(Show.start_time > now, Show.artist_id == artist_id)
    ).all()
    upcoming_shows = []
    for data in upcoming_shows_data:
        venue = Venue.query.get(data.venue_id)
        upcoming_show = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(data.start_time),
        }
        upcoming_shows.append(upcoming_show)
    artist_data["upcoming_shows"] = upcoming_shows
    artist_data["upcoming_shows_count"] = len(upcoming_shows)

    return render_template("pages/show_artist.html", artist=artist_data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    genres_list = artist.genres[1:-1].split(",")
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [genre.strip('"') for genre in genres_list],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }
    form = ArtistForm(data=artist_data)
    # TODO:[done] populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # [done] TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    artist_info = request.form
    artist_info = artist_info.to_dict(flat=False)
    artist.name = artist_info["name"][0]
    artist.image_link = artist_info["image_link"][0]
    artist.city = artist_info["city"][0]
    artist.state = artist_info["state"][0]
    artist.website = artist_info["website"][0]
    artist.phone = artist_info["phone"][0]
    artist.genres = artist_info["genres"]
    artist.facebook_link = artist_info["facebook_link"][0]
    artist.seeking_venue = True if "seeking_venue" in artist_info else False
    artist.seeking_description = artist_info["seeking_description"][0]
    db.session.commit()
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    genres_list = venue.genres[1:-1].split(",")
    venue_data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [genre.strip('"') for genre in genres_list],
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    form = VenueForm(data=venue_data)

    # [done] TODO: populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # [done] TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    venue_info = request.form
    venue_info = venue_info.to_dict(flat=False)
    venue.name = venue_info["name"][0]
    venue.image_link = venue_info["image_link"][0]
    venue.city = venue_info["city"][0]
    venue.state = venue_info["state"][0]
    venue.address = venue_info["address"][0]
    venue.website = venue_info["website"][0]
    venue.phone = venue_info["phone"][0]
    venue.genres = venue_info["genres"]
    venue.facebook_link = venue_info["facebook_link"][0]
    venue.seeking_talent = True if "seeking_talent" in venue_info else False
    venue.seeking_description = venue_info["seeking_description"][0]
    db.session.commit()
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Artist record in the db, instead [Done]
    # TODO: modify data to be the data object returned from db insertion
    error = False
    artist_info = request.form
    artist_info = artist_info.to_dict(flat=False)
    print(artist_info)
    try:
        artist = Artist(
            name=artist_info["name"][0],
            image_link=artist_info["image_link"][0],
            city=artist_info["city"][0],
            state=artist_info["state"][0],
            website=artist_info["website"][0],
            phone=artist_info["phone"][0],
            genres=artist_info["genres"],
            facebook_link=artist_info["facebook_link"][0],
            seeking_venue=True if "seeking_venue" in artist_info else False,
            seeking_description=artist_info["seeking_description"][0],
        )
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash("Artist " + artist_info["name"][0] + " was successfully listed!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Artist "
            + artist_info["name"]
            + " could not be listed."
        )
    finally:
        db.session.close()
    # [done] TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # [done] TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    now = datetime.today()
    shows = (
        Show.query.filter(Show.start_time > now).order_by(Show.venue_id).all()
    )
    data = []
    for show in shows:
        venue = Venue.query.get(show.venue_id)
        artist = Artist.query.get(show.artist_id)
        show_data = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }
        data.append(show_data)

    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # [done] TODO: insert form data as a new Show record in the db, instead [Done]
    error = False
    show_info = request.form
    show_info.to_dict(flat=False)
    now = datetime.today()
    artist = Artist.query.get(show_info["artist_id"])
    venue = Venue.query.get(show_info["venue_id"])
    artist_booked_time = [
        show.start_time for show in artist.parents if show.start_time > now
    ]
    start_time = show_info["start_time"]
    for booked_time in artist_booked_time:
        if (
            time.mktime(booked_time.timetuple()) - 3600 * 3
            <= time.mktime(dateutil.parser.parse(start_time).timetuple())
            <= time.mktime(booked_time.timetuple()) + 3600 * 3
        ):
            flash("This time was booked. Please reselect.")
            return redirect(url_for("create_shows"))
    try:
        show = Show(start_time=start_time)
        show.artist = artist
        show.venue = venue
        db.session.commit()
        # on successful db insert, flash success
        flash("Show was successfully listed!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
    # on successful db insert, flash success
    # [done] TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
