#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
import config
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venue (Create, Read, Update and Delete)
#  ----------------------------------------------------------------


#  Create Venue (CREATE)
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    venue_form = VenueForm(request.form)
    try:
        new_venue = Venue(
            name=venue_form.name.data,
            city=venue_form.city.data,
            state=venue_form.state.data,
            address=venue_form.address.data,
            phone=venue_form.phone.data,
            genres=','.join(venue_form.genres.data),
            facebook_link=venue_form.facebook_link.data,
            image_link=venue_form.image_link.data,
            website_link=venue_form.website_link.data,
            searching_talent=venue_form.seeking_talent.data,
            search_description=venue_form.seeking_description.data
        )
        db.session.add(new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except ():
        db.session.rollback()
        error = True
        # on unsuccessful db insert, flash error
        flash('An error occurred. Venue ' +
              data.name + ' could not be listed.')
        print(sys.exc_info)
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Venues (READ)
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venues = Venue.query.distinct(Venue.city, Venue.state).all()
    data = []
    try:
        for venue in venues:
            venue_data = {
                "city": venue.city,
                "state": venue.state,
                "venues": []
            }
            city_venues = Venue.query.filter_by(city=venue.city).all()
            for i in city_venues:
                upcoming_shows_query = db.session.query(Show, Venue).join(
                    Venue).filter(Show.venue_id == i.id).filter(Show.date > datetime.now()).all()
                if venue_data["city"] == i.city:
                    venue_data["venues"].append({
                        "id": i.id,
                        "name": i.name,
                        "num_upcoming_shows": len(upcoming_shows_query),
                    })
            data.append(venue_data)
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    try:
        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres.split(','),
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.searching_talent,
            "seeking_description": venue.search_description,
            "image_link": venue.image_link,
            "past_shows": [],
            "upcoming_shows": [],
        }
        past_shows_query = db.session.query(Show, Venue, Artist).join(
            Venue).join(Artist).filter(Show.venue_id == venue_id).filter(Show.date < datetime.now()).all()
        for show in past_shows_query:
            data['past_shows'].append({
                "artist_id": show.Artist.id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.Show.date.strftime('%Y-%m-%d %H:%I')
            })

        upcoming_shows_query = db.session.query(Show, Venue, Artist).join(
            Venue).join(Artist).filter(Show.venue_id == venue_id).filter(Show.date > datetime.now()).all()
        for show in upcoming_shows_query:
            data['upcoming_shows'].append({
                "artist_id": show.Artist.id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.Show.date.strftime('%Y-%m-%d %H:%I')
            })
        data["past_shows_count"] = len(data['past_shows'])
        data["upcoming_shows_count"] = len(data['upcoming_shows'])
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    term = "%{}%".format(search_term.replace(" ", "\ "))
    try:
        search = Venue.query.filter(Venue.name.match(term)).all()
        result = []
        for i in search:
            data = {
                "id": i.id,
                "name": i.name,
                "num_upcoming_shows": len(i.shows)
            }
            result.append(data)
        response = {
            "count": len(result),
            "data": result
        }
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

#  Edit Venue (UPDATE)
#  ----------------------------------------------------------------


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    try:
        venue = Venue.query.get(venue_id)
        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.genres.data = venue.genres
        form.address.data = venue.address
        form.facebook_link.data = venue.facebook_link
        form.image_link.data = venue.image_link
        form.website_link.data = venue.website_link
        form.seeking_talent.data = venue.searching_talent
        form.seeking_description.data = venue.search_description
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    venue_form = VenueForm(request.form)
    try:
        # artist record with ID <artist_id> using the new attributes
        venue = Venue.query.get(venue_id)

        venue.name = venue_form.name.data
        venue.city = venue_form.city.data
        venue.state = venue_form.state.data
        venue.phone = venue_form.phone.data
        venue.genres = ','.join(venue_form.genres.data)
        venue.facebook_link = venue_form.facebook_link.data
        venue.image_link = venue_form.image_link.data
        venue.website_link = venue_form.website_link.data
        venue.searching_talent = venue_form.seeking_talent.data
        venue.search_description = venue_form.seeking_description.data
        db.session.commit()
    except ():
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Delete Venue (DELETE)
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')


#  Artist (CREATE, READ, UPDATE AND DELETE)
#  ----------------------------------------------------------------


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    body = {}
    artist_form = ArtistForm(request.form)
    try:
        new_artist = Artist(
            name=artist_form.name.data,
            city=artist_form.city.data,
            state=artist_form.state.data,
            phone=artist_form.phone.data,
            genres=','.join(artist_form.genres.data),
            facebook_link=artist_form.facebook_link.data,
            image_link=artist_form.image_link.data,
            website_link=artist_form.website_link.data,
            searching_venues=artist_form.seeking_venue.data,
            search_description=artist_form.seeking_description.data
        )
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except ():
        db.session.rollback()
        error = True
        # on unsuccessful db insert, flash error
        flash('An error occurred. Artist ' +
              data.name + ' could not be listed.')
        print(sys.exc_info)
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  View Artists (READ)
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    try:
        data = Artist.query.order_by('name').all()
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    try:
        data = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres.split(','),
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_venues": artist.searching_venues,
            "seeking_description": artist.search_description,
            "image_link": artist.image_link,
            "past_shows": [],
            "upcoming_shows": [],
        }
        past_shows_query = db.session.query(Show, Venue, Artist).join(
            Venue).join(Artist).filter(Show.artist_id == artist_id).filter(Show.date < datetime.now()).all()
        for show in past_shows_query:
            data['past_shows'].append({
                "venue_id": show.Venue.id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": show.Show.date.strftime('%Y-%m-%d %H:%I')
            })

        upcoming_shows_query = db.session.query(Show, Venue, Artist).join(
            Venue).join(Artist).filter(Show.artist_id == artist_id).filter(Show.date > datetime.now()).all()
        for show in upcoming_shows_query:
            data['upcoming_shows'].append({
                "venue_id": show.Venue.id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": show.Show.date.strftime('%Y-%m-%d %H:%I')
            })
        data["past_shows_count"] = len(data['past_shows'])
        data["upcoming_shows_count"] = len(data['upcoming_shows'])
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/show_artist.html', artist=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term')
    term = "%{}%".format(search_term.replace(" ", "\ "))
    try:
        search = Artist.query.filter(Artist.name.match(term)).all()
        result = []
        for i in search:
            data = {
                "id": i.id,
                "name": i.name,
                "num_upcoming_shows": len(i.shows)
            }
            result.append(data)
        response = {
            "count": len(result),
            "data": result
        }
    except ():
        db.session.rollback()
    finally:
        db.session.close()

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


#  Edit Artist (UPDATE)
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    try:
        artist = Artist.query.get(artist_id)
        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.genres.data = artist.genres
        form.facebook_link.data = artist.facebook_link
        form.image_link.data = artist.image_link
        form.website_link.data = artist.website_link
        form.seeking_venue.data = artist.searching_venues
        form.seeking_description.data = artist.search_description
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist_form = ArtistForm(request.form)
    try:
        # artist record with ID <artist_id> using the new attributes
        artist = Artist.query.get(artist_id)

        artist.name = artist_form.name.data
        artist.city = artist_form.city.data
        artist.state = artist_form.state.data
        artist.phone = artist_form.phone.data
        artist.genres = ','.join(artist_form.genres.data)
        artist.facebook_link = artist_form.facebook_link.data
        artist.image_link = artist_form.image_link.data
        artist.website_link = artist_form.website_link.data
        artist.searching_venues = artist_form.seeking_venue.data
        artist.search_description = artist_form.seeking_description.data
        db.session.commit()
    except ():
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


#  Delete Artist (DELETE)
#  ----------------------------------------------------------------


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        # on successful db update, flash success
        flash('Artist ' + artist.name + ' was successfully deleted')
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')


#  Shows (CREATE and READ)
#  ----------------------------------------------------------------


#  Create Shows (CREATE)
#  ----------------------------------------------------------------

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    show_form = ShowForm(request.form)
    try:
        new_show = Show(
            date=show_form.start_time.data,
            venue_id=show_form.venue_id.data,
            artist_id=show_form.artist_id.data
        )
        db.session.add(new_show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except ():
        error = True
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows (READ)
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    show_list = db.session.query(
        Show, Artist, Venue).join(Artist).join(Venue).all()
    data = []
    try:
        for showw in show_list:
            details = {
                "venue_id": showw.Venue.id,
                "venue_name": showw.Venue.name,
                "artist_id": showw.Artist.id,
                "artist_name": showw.Artist.name,
                "artist_image_link": showw.Artist.image_link,
                "start_time": showw.Show.date.strftime('%Y-%m-%d %H:%I')
            }
            data.append(details)
    except ():
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/shows.html', shows=data)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
