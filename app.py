# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
import sys
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import (
    render_template,
    request,
    redirect,
    url_for
)
from flask_moment import Moment
from sqlalchemy.exc import SQLAlchemyError

from forms import *
from models import (
    app,
    db,
    Venue,
    Show,
    Artist
)

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app.config.from_object('config')
moment = Moment(app)
db.init_app(app)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    venues = Venue.query.order_by(Venue.created_date.desc()).limit(10).all()
    artists = Artist.query.order_by(Artist.created_date).limit(10).all()
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # get data from database
    all_venues = Venue.query.all()

    # use a dict to speed up finding venues with same (city, state)
    # each (city, state) maps to a list
    venues_dict = {}

    # loop over all data from database
    for venue in all_venues:
        # create groups of (city, state) tuple
        key = (venue.city, venue.state)

        # create a list of venues if one wasn't found for current (city, state) group
        if key not in venues_dict:
            venues_dict[key] = []

        # choose only data we want and append to dictionary's list
        time_now = datetime.utcnow()

        # either this or aggregate using postgres but I thought I'd decrease the calls to database
        upcoming_shows = list(filter(lambda show: show.start_time > time_now, venue.shows))

        curr_venue = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(upcoming_shows)
        }
        venues_dict[key].append(curr_venue)

    # areas will be sent to view to be shown to user
    areas = []

    for key, venues_in_city in venues_dict.items():
        # destructure the key
        city, state = key

        new_area = {
            "city": city,
            "state": state,
            "venues": venues_in_city
        }
        areas.append(new_area)

    return render_template('pages/venues.html', areas=areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    time_now = datetime.utcnow()
    data = []

    for venue in venues:
        upcoming_shows = list(filter(lambda show: show.start_time > time_now, venue.shows))
        cur = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(upcoming_shows),
        }
        data.append(cur)

    response = {
        "count": len(venues),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response,
                           search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    upcoming_shows = []
    past_shows = []

    time_now = datetime.utcnow()

    for show in venue.shows:
        cur_show = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        }
        if show.start_time > time_now:
            upcoming_shows.append(cur_show)
        else:
            past_shows.append(cur_show)

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
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # insert form data as a new Venue record in the db
    venue_form = VenueForm(request.form, meta={"csrf": False})

    if not venue_form.validate():
        flash('error validating venue form ' + str(venue_form.errors))
        return render_template('pages/home.html')

    try:
        # get data from post request
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']
        website = "https://www.google.com"

        image_link = "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
        venue = Venue(name=name,
                      city=city,
                      state=state,
                      address=address,
                      phone=phone,
                      website=website,
                      genres=genres,
                      image_link=image_link,
                      facebook_link=facebook_link)
        # try to insert into database
        db.session.add(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except SQLAlchemyError:
        # source: https://stackoverflow.com/questions/2193670/catching-sqlalchemy-exceptions/4430982
        # unsuccessful db insert, flash an error instead.
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    venue_name = ''
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()

        # on successful db delete, flash success
        flash('Venue ' + venue_name + ' was successfully deleted!')
    except SQLAlchemyError:
        # unsuccessful db delete, flash an error instead.
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' + venue_name + ' could not be deleted.')
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    time_now = datetime.utcnow()
    data = []

    for artist in artists:
        upcoming_shows = list(filter(lambda show: show.start_time > time_now, artist.shows))
        cur = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(upcoming_shows),
        }
        data.append(cur)

    response = {
        "count": len(artists),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    past_shows = []
    upcoming_shows = []
    time_now = datetime.utcnow()

    for show in artist.shows:
        cur_show = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
        }
        if show.start_time > time_now:
            upcoming_shows.append(cur_show)
        else:
            past_shows.append(cur_show)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "facebook_link": artist.facebook_link,
        "website": artist.website,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    data = None

    artist_form = ArtistForm(request.form, meta={"csrf": False})

    if not artist_form.validate():
        flash('error validating artist form ' + str(artist_form.errors))
        return render_template('pages/home.html')

    try:
        # get artist from database
        artist = Artist.query.get(artist_id)

        # update attributes
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']

        # commit
        db.session.commit()

        # on successful db edit, flash success
        flash('Artist ' + artist.name + ' was successfully edited!')
    except SQLAlchemyError:
        # unsuccessful db edit, flash an error instead.
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' + data.name + ' could not be edited.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue_form = VenueForm(request.form, meta={"csrf": False})

    if not venue_form.validate():
        flash('error validating venue form ' + str(venue_form.errors))
        return render_template('pages/home.html')

    try:
        # get data from post request
        venue = Venue.query.get(venue_id)

        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']

        db.session.commit()

        # on successful db edit, flash success
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
    except SQLAlchemyError:
        # unsuccessful db edit, flash an error instead.
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue with id' + venue_id + ' could not be edited.')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    artist_form = ArtistForm(request.form, meta={"csrf": False})

    if not artist_form.validate():
        flash('error validating artist form ' + str(artist_form.errors))
        return render_template('pages/home.html')

    try:
        # get data from post request
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']

        # create a new artist
        artist = Artist(name=name,
                        city=city,
                        state=state,
                        genres=genres,
                        phone=phone,
                        website='https://www.facebook.com',
                        image_link='https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60',
                        facebook_link=facebook_link)

        # try to insert into database
        db.session.add(artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except SQLAlchemyError:
        # unsuccessful db insert, flash an error instead.
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.', category='error')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    all_shows = Show.query.all()
    data = []
    for show in all_shows:
        cur = {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        }
        data.append(cur)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form

    try:
        # get data from post request
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']

        show = Show(venue_id=venue_id, artist_id=artist_id, start_time=format_datetime(start_time))

        # try to insert into database
        db.session.add(show)
        db.session.commit()

        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except SQLAlchemyError:
        # unsuccessful db insert, flash an error instead.
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(400)
def bad_request_error(error):
    return render_template('errors/400.html', message='Bad Request'), 400


@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('errors/401.html', message='Unauthorized'), 401


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html', message='Forbidden'), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(405)
def invalid_method_error(error):
    return render_template('errors/405.html', message='Invalid Method'), 405


@app.errorhandler(409)
def duplicate_resource_error(error):
    return render_template('errors/409.html', message='Duplicate Resource'), 409


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
