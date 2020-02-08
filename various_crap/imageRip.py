import requests
import shutil
import os

def download_image(image_url, image_name):
    # Open the url image, set stream to True, this will return the stream content.
    resp = requests.get(image_url, stream=True)

    # Open a local file with wb ( write binary ) permission.
    if not os.path.exists(os.getcwd() + '/img_download'):
        os.makedirs(os.getcwd() + '/img_download')
    filePath = os.getcwd() + '/img_download/' + image_name + '.jpg'
    local_file = open(filePath, 'wb')

    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
    resp.raw.decode_content = True

    # Copy the response stream raw data to local image file.
    shutil.copyfileobj(resp.raw, local_file)

    # Remove the image url response object.
    del resp

download_image('https://i.ytimg.com/vi/WeaHq58ehs8/hqdefault.jpg', 'downloaded')
