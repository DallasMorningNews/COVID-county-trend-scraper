from utils import upload_data_s3

import scraper
import json

def handler(event, context):
    print('service started')
    # Call the function from your imported file
    data = json.dumps(scraper.update_trends())

    # data = json.dumps(scraper.order_data())

    bucket_filepath = 'data-store/2020/coronavirus-county-trends.json'

    upload_data_s3(data, bucket_filepath, 'json')
# this function is just for our testing purposes,
# just calling the main handler function
if __name__ == '__main__':
    handler(1, 2)
