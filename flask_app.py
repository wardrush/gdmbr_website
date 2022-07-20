import flask
from flask import request, url_for, render_template, redirect
import utils
from datetime import datetime


# Get New Data
utils.save_location_data(utils.create_api_response_dataframe())
# Package needed data into dict for Jinja2 parsing
data = {
        "mapbox_access_token":utils.get_mapbox_accesskey(),
        "gdmbr_route_data":utils.get_route_data(),
        "recent_update_time":utils.get_most_recent_update_time(),
        "site_refresh_time":datetime.now()
        }
data['current_lat'], data['current_long'] = utils.get_most_recent_lat_long()


app = flask.Flask(__name__)

@app.errorhandler(Exception)
def handle_500():
    #original = getattr(e, "original_exception", None)

    #if original is None:
        # direct 500 error, such as abort(500)
    #    return render_template("500.html"), 500

    # wrapped unhandled error
    return render_template("index3.html")

@app.route('/',methods=['GET','POST'])
def my_maps():
  return render_template('formatted.html', data=data)

if __name__ == '__main__':
    app.run(debug=False)