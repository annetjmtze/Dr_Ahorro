import boto3
from datetime import datetime
import os
from botocore.exceptions import ClientError

def get_r2_client():
    """Retorna un cliente boto3 configurado para Cloudflare R2."""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT_URL'),   # Ej: https://<account_id>.r2.cloudflarestorage.com
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='auto'  # Recomendado para R2
    )

def subir_imagen(imagen_bytes, farmacia, medicamento):
    """
    Sube una imagen a R2 y devuelve el key (nombre del objeto) para guardar en BD.
    
    Args:
        imagen_bytes (bytes): Datos binarios de la imagen (PNG).
        farmacia (str): Nombre de la farmacia (ej. "farmacia_guadalajara").
        medicamento (str): Nombre del medicamento (ej. "paracetamol").
    
    Returns:
        str: Key del objeto en R2, ej. "screenshots/farmacia_guadalajara/paracetamol/2026-07-22_14-30.png".
    """
    # Limpiar caracteres problemáticos y formatear fecha
    farmacia_clean = farmacia.replace(' ', '_').lower()
    medicamento_clean = medicamento.replace(' ', '_').lower()
    fecha = datetime.now().strftime('%Y-%m-%d_%H-%M')
    key = f"screenshots/{farmacia_clean}/{medicamento_clean}/{fecha}.png"
    
    client = get_r2_client()
    try:
        client.put_object(
            Bucket=os.getenv('R2_BUCKET_NAME'),
            Key=key,
            Body=imagen_bytes,
            ContentType='image/png'
        )
        return key
    except ClientError as e:
        # Log del error (puedes usar logging o print)
        print(f"Error subiendo imagen a R2: {e}")
        raise