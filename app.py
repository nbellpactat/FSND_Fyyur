# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
import os
import sys
from collections import defaultdict
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_moment import Moment

import models
from forms import *
from models import db, Artist, Show, Venue


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
db.init_app(app)
migrate = Migrate(app, db)


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
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    error = False
    response = {}
    # Dictionary mapping venue_id to num_upcoming_shows
    upcoming_shows = defaultdict(int)
    current_datetime = datetime.now()
    try:
        form_data = request.form.items()
        search_value = ""
        for item in form_data:
            search_value = item[1]
        search_results = Venue().query.filter(Venue.name.ilike(f'%{search_value}%')).all()

        venue_data = []
        for venue in search_results:

            # Determine the number of upcoming shows per venue
            upcoming_shows_list = Show().query.filter(Show.start_time > current_datetime)
            for show in upcoming_shows_list:
                upcoming_shows[show.venue_id] += 1

            venue_data.append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": upcoming_shows[venue.id]
                }
            )
        response = {
            "count": len(search_results),
            "data": venue_data
        }
    except:
        error = True
        db.session.rollback()
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/search_venues.html', results=response,
                               search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    error = False
    response = {}
    current_datetime = datetime.now()
    past_shows = []
    upcoming_shows = []
    try:
        # Get the information about the Venue
        venue = Venue().query.get(venue_id)

        for show in venue.shows:
            show_data = {
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time
            }
            if show.start_time <= current_datetime:
                past_shows.append(show_data)
            else:
                upcoming_shows.append(show_data)

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
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
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
            venue = Venue()
            form.populate_obj(venue)
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
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    error = False
    response = {}
    # Dictionary mapping venue_id to num_upcoming_shows
    upcoming_shows = defaultdict(int)
    current_datetime = datetime.now()
    try:
        form_data = request.form.items()
        search_value = ""
        for item in form_data:
            search_value = item[1]
        search_results = Artist().query.filter(Artist.name.ilike(f'%{search_value}%')).all()

        artist_data = []
        for artist in search_results:

            # Determine the number of upcoming shows per venue
            upcoming_shows_list = Show().query.filter(Show.start_time > current_datetime)
            for show in upcoming_shows_list:
                upcoming_shows[show.artist_id] += 1

            artist_data.append(
                {
                    "id": artist.id,
                    "name": artist.name,
                    "num_upcoming_shows": upcoming_shows[artist.id]
                }
            )
        response = {
            "count": len(search_results),
            "data": artist_data
        }
    except:
        error = True
        db.session.rollback()
        error_line_number()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/search_artists.html', results=response,
                               search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    error = False
    data = defaultdict
    current_datetime = datetime.now()
    past_shows = []
    upcoming_shows = []
    try:
        # Get a list of all the Artist
        artist = Artist().query.get(artist_id)

        for show in artist.shows:
            show_data = {
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time
            }
            if show.start_time <= current_datetime:
                past_shows.append(show_data)
            else:
                upcoming_shows.append(show_data)
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
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
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
            form.populate_obj(artist)
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
            flash("Artist updatd!")
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
            form.populate_obj(venue)
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
            flash("Venue updated!")
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
            artist = Artist()
            form.populate_obj(artist)
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
            flash('An error occurred. Artist not created.')
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
            show = Show()
            form.populate_obj(show)
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
