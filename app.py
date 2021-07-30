# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import sys, os
from datetime import datetime
from collections import defaultdict

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *


# Debugging Functions
def error_line_number():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return print(exc_type, fname, exc_tb.tb_lineno)


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String(120)), nullable=False)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    artist = db.relationship('Artist', backref=db.backref('shows', lazy=True, cascade="all, delete-orphan"))
    venue = db.relationship('Venue', backref=db.backref('shows', lazy=True, cascade="all, delete-orphan"))


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    error = False
    data = []
    # Dictionary mapping venue_id to num_upcoming_shows
    upcoming_shows = defaultdict(int)
    current_datetime = datetime.now()
    try:
        # Retrieve a list of all the Venues
        venues_list = Venue().query.all()

        # Define a list of location tuples
        locations = []
        for venue in venues_list:
            locations.append((venue.city, venue.state))
        # Make the list hold only unique values
        locations = list(dict.fromkeys(locations))

        # Determine the number of upcoming shows per venue
        upcoming_shows_list = Show().query.filter(Show.start_time > current_datetime)
        for show in upcoming_shows_list:
            upcoming_shows[show.venue_id] += 1

        # Add all of the locations to data
        for location in locations:
            data.append(
                {
                    "city": location[0],
                    "state": location[1],
                    "venues": list(defaultdict())
                }
            )

        # Iterate through venues to match them to their locations
        for venue in venues_list:
            for i, location in enumerate(locations):
                # If the location matches, add venue data to that location record
                if data[i]['city'] == venue.city and data[i]['state'] == venue.state:
                    data[i]['venues'].append(
                        {
                            'id': venue.id,
                            'name': venue.name,
                            'num_upcoming_shows': upcoming_shows[venue.id]
                        }
                    )
    except:
        error = True
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        "count": 1,
        "data": [{
            "id": 2,
            "name": "The Dueling Pianos Bar",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    error = False
    response = {}
    current_datetime = datetime.now()
    past_shows = []
    past_shows_count = 0
    upcoming_shows = []
    upcoming_shows_count = 0
    try:
        # Get the information about the Venue
        venue = Venue().query.get(venue_id)

        # Determine the number of upcoming shows for the venue_id
        upcoming_shows_list = Show().query.filter(
            Show.venue_id == venue_id,
            Show.start_time > current_datetime
        )

        # Determine the number of past shows for the venue_id
        past_shows_list = Show().query.filter(
            Show.venue_id == venue_id,
            Show.start_time < current_datetime
        )

        # Build the Artist info for the upcoming shows at this venue_id
        for show in upcoming_shows_list:
            artist = Artist().query.get(show.artist_id)
            upcoming_shows.append(
                {
                    "artist_id": artist.id,
                    "artist_name": artist.name,
                    "artist_image_link": artist.image_link,
                    "start_time": show.start_time
                }
            )
            upcoming_shows_count += 1

        # Build the Artist info for the past shows at this venue_id
        for show in past_shows_list:
            artist = Artist().query.get(show.artist_id)
            past_shows.append(
                {
                    "artist_id": artist.id,
                    "artist_name": artist.name,
                    "artist_image_link": artist.image_link,
                    "start_time": show.start_time
                }
            )
            past_shows_count += 1

        # Build the data object of the venue
        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows_count": upcoming_shows_count
        }

        response['venue_id'] = venue.id
        response['venue_name'] = venue.name
    except:
        error = True
        error_line_number()
        flash(f'Something went wrong! Could not find Venue with id: {venue_id}...')
    if error:
        abort(500)
    else:
        print(response)
        return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm(meta={"csrf": False})
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    response = {}
    form = VenueForm(meta={"csrf": False})
    if form.validate():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
                genres=form.genres.data
            )
            response['venue_name'] = venue.name
            response['venue_city'] = venue.city
            response['venue_state'] = venue.state
            response['venue_address'] = venue.address
            response['genres'] = venue.genres
            db.session.add(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            flash('An error occurred. Venue ' + response['venue_name'] + ' could not be listed.')
            error_line_number()
        finally:
            db.session.close()
        if error:
            abort(500)
        else:
            print(response)
            try:
                # on successful db insert, flash success
                flash('Venue ' + response['venue_name'] + ' was successfully listed!')
                # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            except:
                flash('Something went wrong! Venue saved to database...')
            return render_template('pages/home.html')
    else:
        flash(f"{form.errors.items()}")
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
    error = False
    response = {}
    try:
        venue = Venue().query.get(venue_id)
        venue_shows = Show().query.filter(Show.venue_id == venue.id).all()
        artists_with_shows_at_venue = []
        for show in venue_shows:
            artists_with_shows_at_venue.append(show.artist_id)
        artists_with_shows_at_venue = list(dict.fromkeys(artists_with_shows_at_venue))
        print(venue)
        print(venue_shows)
        print(artists_with_shows_at_venue)
        db.session.delete(venue)
        db.session.commit()
        response['deleted'] = True
        response['venue_id'] = venue_id
        response['venue_name'] = venue.name
    except:
        error = True
        db.session.rollback()
        error_line_number()
        flash(f"Something went wrong when deleting Venue with id: {response['venue_id']}...")
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        flash(f"Successfully deleted Venue '{response['venue_name']}'!")
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    error = False
    data = []
    try:
        artists_list = Artist().query.all()
        for artist in artists_list:
            data.append(
                {
                    "id": artist.id,
                    "name": artist.name
                }
            )
    except:
        error = True
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 1,
        "data": [{
            "id": 4,
            "name": "Guns N Petals",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    error = False
    data = defaultdict
    current_datetime = datetime.now()
    try:
        # Get a list of all the Artists
        artists_list = Artist().query.all()

        # For each Artist id, build the data and appent it to the data object
        for artist in artists_list:
            # Get the data for this artist's past and upcoming shows
            past_shows_list = Show().query.filter(
                Show.artist_id == artist.id,
                Show.start_time < current_datetime
            )
            upcoming_shows_list = Show().query.filter(
                Show.artist_id == artist.id,
                Show.start_time > current_datetime
            )
            past_shows = []
            past_shows_count = 0
            upcoming_shows = []
            upcoming_shows_count = 0
            for show in past_shows_list:
                past_shows_count += 1
                past_shows.append(
                    {
                        "venue_id": show.venue_id,
                        "venue_name": show.venue.name,
                        "venue_image_link": show.venue.image_link,
                        "start_time": show.start_time
                    }
                )
            for show in upcoming_shows_list:
                upcoming_shows_count += 1
                upcoming_shows.append(
                    {
                        "venue_id": show.venue_id,
                        "venue_name": show.venue.name,
                        "venue_image_link": show.venue.image_link,
                        "start_time": show.start_time
                    }
                )
            # Build the data object of the artist information
            data = {
                "id": artist.id,
                "name": artist.name,
                "genres": artist.genres,
                "city": artist.city,
                "state": artist.state,
                "phone": artist.phone,
                "website": artist.website,
                "facebook_link": artist.facebook_link,
                "seeking_venue": artist.seeking_venue,
                "seeking_description": artist.seeking_description,
                "image_link": artist.image_link,
                "past_shows": past_shows,
                "upcoming_shows": upcoming_shows,
                "past_shows_count": past_shows_count,
                "upcoming_shows_count": upcoming_shows_count
            }
    except:
        error = True
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    error = False
    try:
        artist = Artist().query.get(artist_id)
        form = ArtistForm(obj=artist)
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
        error_line_number()
    else:
        return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    error = False
    form = ArtistForm(meta={'csrf': False})
    if form.validate():
        try:
            artist = Artist().query.get(artist_id)
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = form.genres.data
            artist.image_link = form.image_link.data
            artist.facebook_link = form.facebook_link.data
            artist.website = form.website_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            db.session.add(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            abort(500)
            error_line_number()
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        print(form.errors.items())
        for error in form.errors.items():
            flash(f"Error editing Artist. Field {error[0]} has error: {error[1][0]}")
        return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    error = False
    try:
        venue = Venue().query.get(venue_id)
        form = VenueForm(obj=venue)
    except:
        error = True
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    error = False
    form = VenueForm(meta={'csrf': False})
    if form.validate():
        try:
            venue = Venue().query.get(venue_id)
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.image_link = form.image_link.data
            venue.facebook_link = form.facebook_link.data
            venue.website = form.website_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.genres = form.genres.data
            db.session.add(venue)
            db.session.commit()
        except:
            error = True
            error_line_number()
        finally:
            db.session.close()
        if error:
            abort(500)
        else:
            return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        print(form.errors.items())
        for error in form.errors.items():
            flash(f"Error editing Venue. Field {error[0]} has error: {error[1][0]}")
        return render_template('pages/home.html')


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm(meta={"csrf": False})
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    error = False
    response = {}
    form = ArtistForm(meta={"csrf": False})
    if form.validate():
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            response['artist_name'] = artist.name
            response['artist_city'] = artist.city
            response['artist_state'] = artist.state
            response['artist_genres'] = artist.genres
            db.session.add(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            error_line_number()
            flash('An error occurred. Artist ' + response['artist_name'] + ' could not be listed.')
        finally:
            db.session.close()
        if error:
            abort(500)
        else:
            print(response)
            try:
                # on successful db insert, flash success
                flash('Artist ' + request.form['name'] + ' was successfully listed!')
            except:
                flash('Something went wrong! Venue saved to database...')
            return render_template('pages/home.html')
    else:
        flash(f"{form.errors.items()}")
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    # displays list of shows at /shows
    error = False
    data = []
    try:
        # Get the data about all Shows
        shows_list = Show().query.all()
        # Build the data object to return
        for show in shows_list:
            data.append(
                {
                    "venue_id": show.venue_id,
                    "venue_name": show.venue.name,
                    "artist_id": show.artist_id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": show.start_time
                }
            )
    except:
        error = True
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm(meta={"csrf": False})
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    response = {}
    form = ShowForm(meta={"csrf": False})
    if form.validate():
        try:
            show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(show)
            db.session.commit()
            response['show_artist'] = form.artist_id.data
            response['show_venue'] = form.venue_id.data
            response['show_start_time'] = show.start_time
        except:
            error = True
            db.session.rollback()
            error_line_number()
            flash('An error occurred. Show could not be listed.')
        if error:
            abort(500)
        else:
            # on successful db insert, flash success
            flash('Show was successfully listed!')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            return render_template('pages/home.html')
    else:
        flash(f"{form.errors.items()}")
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
