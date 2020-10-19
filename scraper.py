import datetime
import os
import requests
from slacker import Slacker
import sys

import sentry_sdk
sentry_sdk.init("https://5ca2e65fe06941a3b38932df7daa338a@o101507.ingest.sentry.io/5226049")

TREND_DATA = os.environ.get('TREND_DATA_FILE')

DSHS_DASHBOARD = 'https://services5.arcgis.com/ACaLB9ifngzawspq/arcgis/rest/services/DSHS_COVID19_Cases_Service/FeatureServer/0/query?f=json&where=Positive%3C%3E0&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=Positive%20desc&resultOffset=0&resultRecordCount=254&resultType=standard&cacheHint=true'

DSHS_UPDATE_FILE = 'https://services5.arcgis.com/ACaLB9ifngzawspq/arcgis/rest/services/DSHS_COVID19_Cases_Service/FeatureServer/0?f=json'

# File to be used if manual entry of missed daily counts needs to occur. Note: This file is out of date
# as soon as a subsequent successful run of the scraper occurs. To use, pull the TREND_DATA file and backfill
# any missing days in each county's trend list
# DSHS_REPAIRED_FILE = os.environ.get('REPAIR_FILE')


def calculate_averages(daily_values):
    """
    Takes a list of daily new cases for a county
    and calculates a 7-day rolling average for the past
    14 days
    """

    averages = []
    for i in range(7, len(daily_values)):
        try:
            last_day = daily_values[i].replace(',', '')
        except AttributeError:
            last_day = daily_values[i]

        try:
            first_day = daily_values[i - 7].replace(',', '')
        except AttributeError:
            first_day = daily_values[i - 7]

    avg = round((int(last_day) - int(first_day)) / 7, 2)
    averages.append(avg)

    return(averages)


def repair_file():
    """
    In an instance where daily totals are not collected
    (scraper failure, state data format change, etc), and
    daily totals need to be manually backfilled, this function
    will take the json file containing the correct daily numbers
    for the county and recalculate 7-day averages
    """

    repair_request = requests.get(DSHS_REPAIRED_FILE)
    repair_data = repair_request.json()

    for county in repair_data:
        county['averages'] = calculate_averages(county['trend'])

    return(repair_data)


def update_trends():
    """
    Function run daily to check for updated data from DSHS.
    If the DSHS data has updated since our last pull, grab the
    day's positive count for each county, and append it
    to the county's trend list in our data file while removing
    the first entry in the list (to keep 21 days worth of totals)
    """

    # our data file
    trend_request = requests.get(TREND_DATA)
    trend_data = trend_request.json()

    # dshs's daily county totals
    dshs_request = requests.get(DSHS_DASHBOARD)
    dshs_data = dshs_request.json()

    # dshs data file that contains last county update date
    update_request = requests.get(DSHS_UPDATE_FILE)
    update_data = update_request.json()

    # pulling last dshs update date
    last_update = datetime.date.fromtimestamp(update_data['editingInfo']['lastEditDate']/1000) - datetime.timedelta(days=1)
    # converting that date object into a list of year, month, date
    update_string = last_update.strftime('%Y-%m-%d').split('-')
    # constructing a MMDD string for our data object and comparisons
    dshs_date = update_string[1] + update_string[2]

    print(dshs_date)
    if (dshs_date != trend_data[0]['update_date']):
        for county in trend_data:
            county['update_date'] = dshs_date
            try:
                dshs_county_data = [item for item in dshs_data['features']
                if item['attributes']['County'] == county['name']][0]['attributes']['Positive']
            except IndexError:
                # sometimes dshs spells DeWitt county with a space. check for that
                if county['name'] == 'DeWitt':
                    try:
                        dshs_county_data = [item for item in dshs_data['features']
                        if item['attributes']['County'] == 'De Witt'][0]['attributes']['Positive']
                    except IndexError:
                        dshs_county_data = 0
                else:
                    dshs_county_data = 0

        # ditch the first entry in our daily trend totals
        county['trend'] = county['trend'][1:]

        # add the new total
        county['trend'].append(dshs_county_data)

        #calculate the averages
        county['averages'] = calculate_averages(county['trend'])
        slackMsg = 'DSHS county trend scraper updated with data from {0}.'.format(dshs_date)

    else:
        slackMsg = 'DSHS county trend scraper ran, but no new data found. Last update occured {0}.'.format(trend_data[0]['update_date'])
        print('No update yet')

    slack = Slacker(os.environ.get('SLACK_TOKEN'))
    # slack.chat.post_message(
    #     '#feed-coronavirus-scrapers',
    #     slackMsg,
    #     as_user=False,
    #     icon_emoji='cardboardbox',
    #     username='DSHS County Trend Scraper'
    #     )

    return(trend_data)


if __name__ == '__main__':
    globals()[sys.argv[1]]()
