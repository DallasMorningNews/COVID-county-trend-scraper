import json
import os
import scraper

from utils import upload_data_s3

def handler(event, context):
    print('service started')
    # Call the function from your imported file
    data = json.dumps(scraper.update_trends())

    bucket_filepath = os.environ.get('TARGET_BUCKET')

    upload_data_s3(data, bucket_filepath, 'json')

if __name__ == '__main__':
    handler(1, 2)
