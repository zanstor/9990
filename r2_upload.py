#!/usr/bin/env python3
"""Upload / delete files in Cloudflare R2. Keys are read from .env and never printed.

Usage:
  python3 r2_upload.py upload <local_file> [<object_name>]   -> prints public URL
  python3 r2_upload.py delete <object_name>
  python3 r2_upload.py check <url>                           -> HTTP status + content-type
"""
import mimetypes
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env():
    env = {}
    with open(os.path.join(HERE, ".env")) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def client(env):
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=f"https://{env['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def content_type(path):
    ext = os.path.splitext(path)[1].lower()
    return {".mp4": "video/mp4", ".mov": "video/quicktime"}.get(
        ext, mimetypes.guess_type(path)[0] or "application/octet-stream"
    )


def check(url):
    # Cloudflare rejects the default Python-urllib User-Agent with 403
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length")


def main():
    cmd = sys.argv[1]
    env = load_env()
    if cmd == "upload":
        path = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(path)
        client(env).upload_file(path, env["R2_BUCKET"], name,
                                ExtraArgs={"ContentType": content_type(name)})
        print(f"{env['R2_PUBLIC_BASE'].rstrip('/')}/{name}")
    elif cmd == "delete":
        client(env).delete_object(Bucket=env["R2_BUCKET"], Key=sys.argv[2])
        print("deleted", sys.argv[2])
    elif cmd == "check":
        print(*check(sys.argv[2]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
