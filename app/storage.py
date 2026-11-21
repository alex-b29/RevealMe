from __future__ import annotations

import json

import boto3
import streamlit as st


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=st.secrets["S3_ENDPOINT"],
        aws_access_key_id=st.secrets["S3_ACCESS_KEY"],
        aws_secret_access_key=st.secrets["S3_SECRET_KEY"],
    )


def fetch_game_config() -> dict | None:
    """Fetch game_config.json from the configured Supabase bucket."""
    try:
        client = get_s3_client()
        response = client.get_object(
            Bucket=st.secrets["BUCKET_NAME"],
            Key="game_config.json",
        )
        return json.loads(response["Body"].read().decode("utf-8"))
    except Exception:
        return None


def save_game_config_to_storage(game_config: dict) -> bool:
    """Upload game_config.json to the configured Supabase bucket."""
    try:
        client = get_s3_client()
        content = json.dumps(game_config, ensure_ascii=False, indent=2).encode("utf-8")
        client.put_object(
            Bucket=st.secrets["BUCKET_NAME"],
            Key="game_config.json",
            Body=content,
            ContentType="application/json",
        )
        return True
    except Exception:
        return False


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
