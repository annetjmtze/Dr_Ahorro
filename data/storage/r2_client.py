import os
import boto3
from botocore.config import Config
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

USE_R2 = os.getenv("USE_R2", "false").lower() == "true"
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

if USE_R2:
    s3_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )

def save_image(image_bytes: bytes, folder: str, filename: str) -> str:
    """
    Guarda la imagen en R2 o localmente según USE_R2.
    Retorna la URL pública (si R2) o la ruta local (si no).
    """
    if USE_R2:
        key = f"{folder}/{filename}"
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType="image/png",
            ACL="public-read",
        )
        url = f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{key}"
        logger.info(f"📸 Subido a R2: {url}")
        return url
    else:
        # Modo local (para desarrollo)
        local_dir = Path("data/screenshots") / folder
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / filename
        with open(local_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"📸 Guardado local: {local_path}")
        return str(local_path.absolute())