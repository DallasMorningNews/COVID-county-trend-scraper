import boto3

# ----------------------------------------
# Shouldn't need to touch any of this.
# ----------------------------------------

def upload_data_s3(data, output_file_path, file_type):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('interactives.dallasnews.com')

    if file_type == 'csv':
        content_type = 'text/csv'

    if file_type == 'json':
        content_type = 'application/json'

    bucket.put_object(
        Key=output_file_path,
        Body=data,  # for json files
        ACL='public-read',
        ContentType=content_type
    )
