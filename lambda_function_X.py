# lambda_function.py
import json
import boto3
from PIL import Image
from io import BytesIO
import urllib.request
import urllib.error

# Minimum 2 Megapixels
MIN_PIXELS = 2_000_000
TIMEOUT_SECONDS = 8

def download_image(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'FlourQualityBot/1.0'})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        return response.read()

def lambda_handler(event, context):
    try:
        # Parse JSON body: {"image_url": "https://..."}
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        image_url = body.get('image_url') or body.get('url') or body.get('imageUrl')

        if not image_url or not image_url.startswith('http'):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "passed": False,
                    "message": "Missing or invalid 'image_url' in request body"
                })
            }

        # Download image
        img_data = download_image(image_url)
        img = Image.open(BytesIO(img_data))
        width, height = img.size
        total_pixels = width * height
        megapixels = round(total_pixels / 1_000_000, 2)

        passed = total_pixels >= MIN_PIXELS

        response = {
            "passed": passed,
            "message": "Image quality OK" if passed 
                     else "Image too low resolution. Please take a closer, clearer photo (minimum 2MP required).",
            "resolution": f"{width}x{height}",
            "total_pixels": total_pixels,
            "megapixels": megapixels,
            "image_url": image_url,
            "required_megapixels": 2.0
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    except urllib.error.HTTPError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "passed": False,
                "message": f"Failed to download image: {e.code} {e.reason}"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "passed": False,
                "message": "Invalid image or processing error",
                "error": str(e)
            })
        }
    



