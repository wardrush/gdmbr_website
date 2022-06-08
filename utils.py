# Hold helper functions for the main flask app here

### Imports ###
import pandas as pd
import os
import requests
import time
import datetime

## Variables ###
api_limit_time_sec = 300
cache_filepath = 'api_cache'
location_record_filepath = os.path.join("/home", "wardrush", "mysite", "data", "GDMBR-2022_rawdata.csv")
spot_column_names = ['@clientUnixTime',
                    'id',
                    'messengerId',
                    'messengerName',
                    'unixTime',
                    'messageType',
                    'latitude',
                    'longitude',
                    'modelId',
                    'showCustomMsg',
                    'dateTime',
                    'messageDetail',
                    'batteryState',
                    'hidden',
                    'messageContent',
                    'altitude']

### Functions ###
def get_spot_api_key():
    return '0ArVRndOpKVJJGqc5hN7uGHzV34r5vUko'


def set_last_time_api_called(cache_filepath='api_cache'):
    with open(cache_filepath, 'w') as api_cache:
        api_cache.write(str(int(time.time())))


def get_last_time_api_called(cache_filepath='api_cache'):
    try:
        with open (cache_filepath) as api_cache:
            return int(api_cache.readlines()[0])
    except FileNotFoundError:
        set_last_time_api_called(cache_filepath)
        return get_last_time_api_called(cache_filepath)


def get_time_since_last_api_call():
    return int(time.time())-get_last_time_api_called()


def get_most_recent_lat_long(location_record_filepath=location_record_filepath):
    # try to grab most recent values
    try:
        df = pd.read_csv(location_record_filepath)
        return (df['latitude'][0], df['longitude'][0])
    # if the file doesn't exist, grab data, create file, and re-call function
    except FileNotFoundError:
        df = create_api_response_dataframe(debug=False)
        save_location_data(location_dataframe=df)
        return get_most_recent_lat_long(location_record_filepath)


def get_most_recent_update_time(location_record_filepath=location_record_filepath):
    # try to grab most recent values
    try:
        df = pd.read_csv(location_record_filepath)
        update_time = datetime.datetime.fromtimestamp(df['unixTime'][0])
        return update_time
    # if the file doesn't exist, grab data, create file, and re-call function
    except FileNotFoundError:
        df = create_api_response_dataframe()
        save_location_data(location_dataframe=df)
        return get_most_recent_update_time(location_record_filepath)


def get_spot_location_data(debug=False, api_limit_time_sec=300):
    # Make the API request to SPOT and return dict from JSON response
    # only make request if at least 5 minutes have passed
    if get_time_since_last_api_call() < api_limit_time_sec:
        print(f'No Request Made--still in API cooldown period. Time left: {api_limit_time_sec-get_time_since_last_api_call()}s')
    else:
        baseurl1 = "https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/"
        baseurl2 = "/message.json"
        url = baseurl1+get_spot_api_key()+baseurl2
        if debug==True: print(url)
        r = requests.get(url)
        set_last_time_api_called()
        return r.json()


def create_api_response_dataframe(spot_data=None,
                                  column_names=spot_column_names,
                                  api_limit_time_sec=300,
                                  debug=False):
    if spot_data is None:
        spot_data = get_spot_location_data(api_limit_time_sec=api_limit_time_sec, debug=debug)
    location_df = pd.DataFrame(columns=column_names)
    try:
        for message in spot_data['response']['feedMessageResponse']['messages']['message']:
            #temp
            location_df = location_df.append(message, ignore_index = True)
            #location_df = pd.concat([location_df, pd.DataFrame(message)],axis=0, join='outer')
            location_df = location_df.sort_values(by=['unixTime'], ascending=False)
        if debug==True:
            print(location_df.head())
            return location_df
        else:
            return location_df
    except (ValueError, TypeError) as e:
        print('No data pulled from API at this time. Please try again later')
    except KeyError as e:
        print(f'KeyError: No messages found in feed. It is likely the feed is outdated')



def save_location_data(api_response_dataframe,
                       location_record_filepath=location_record_filepath):
    # try to grab most recent values from file if it exists
    try:
        read_df = pd.read_csv(location_record_filepath)
        # Concatenate the new data onto the old frame and drop duplicate rows inplace
        combined_df = pd.concat([read_df, api_response_dataframe],axis=0, ignore_index=True).drop_duplicates(subset='unixTime', ignore_index=True, keep='first')
        # Drop old index from combined dataframe
        combined_df = combined_df.sort_values(by=['unixTime'], ascending=False).reset_index(drop=True)
        # Do not add new index when saving CSV
        combined_df.to_csv(location_record_filepath, index=False)
    # if the file doesn't exist, create file and save
    except FileNotFoundError:
        # Do not add new index when saving CSV
        api_response_dataframe = create_api_response_dataframe()
        api_response_dataframe.sort_values(by=['unixTime'], ascending=False).reset_index(drop=True).to_csv(location_record_filepath, index=False)


### Build the Map ###
def get_mapbox_accesskey():
    # returns the mapbox access key
    return 'pk.eyJ1Ijoid2FyZHJ1c2giLCJhIjoiY2wyNnR4bmplMDJkaDNqcjAxZm00OW94OCJ9.sDTtXh2pZMctCLrNAQgHaw'

def get_route_data():
    # Create function that returns the lat longs correctly formatted for MapBox
    # MapBox accepts list of lists
    # Reads CSV data stored in GDMBR-2021_v2_10k-point.csv
    filepath = os.path.join("/home", "wardrush", "mysite", "data", "GDMBR-2021_v2_full-route.csv")
    df = pd.read_csv(filepath)
    route_longs = df['Long'].to_list()
    route_lats = df['Lat'].to_list()
    route_data = [[long, lat] for long, lat in zip(route_longs,route_lats)]
    return route_data

if __name__ == "__main__":
    save_location_data(create_api_response_dataframe())