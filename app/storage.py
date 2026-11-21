from __future__ import annotations

import boto3
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_image_from_storage(name: str) -> bytes | None:
    """Return an image from private Supabase S3 storage, or None if misconfigured."""
    endpoint = st.secrets.get("S3_ENDPOINT", "")
    bucket = st.secrets.get("BUCKET_NAME", "")
    access_key = st.secrets.get("S3_ACCESS_KEY", "")
    secret_key = st.secrets.get("S3_SECRET_KEY", "")

    if not all((endpoint, bucket, access_key, secret_key)):
        return None

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        response = client.get_object(
            Bucket=bucket,
            Key=f"{name}.jpg",
        )
        return response["Body"].read()
    except Exception:
        return None
