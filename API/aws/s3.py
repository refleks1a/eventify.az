import boto3
from fastapi import APIRouter, File, UploadFile
from botocore.exceptions import NoCredentialsError
from starlette import status 
from dotenv import load_dotenv
import os
from datetime import datetime 


load_dotenv()

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

# AWS Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
REGION_NAME = os.getenv("REGION_NAME")
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME,
)


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=expiration
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_image(dest: str, file: UploadFile = File(...)):
    try:
        time = datetime.now()
        file_content = await file.read()
        file_name = dest +  "/" + file.filename + str(time)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=file_content,
            ContentType=file.content_type,
        )
        file_url = f"https://{BUCKET_NAME}.s3.{REGION_NAME}.amazonaws.com/{file_name}"
        return file_url
    except NoCredentialsError:
        return None
    except Exception as e:
        return None
