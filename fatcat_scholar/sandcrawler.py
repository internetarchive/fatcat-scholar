from typing import Any, Dict, Optional

import minio
import requests


class SandcrawlerPostgrestClient:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_grobid(self, sha1: str) -> Optional[Dict[str, Any]]:
        resp = requests.get(self.api_url + "/grobid", params=dict(sha1hex="eq." + sha1))
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json:
            return resp_json[0]
        else:
            return None

    def get_pdf_meta(self, sha1: str) -> Optional[Dict[str, Any]]:
        resp = requests.get(
            self.api_url + "/pdf_meta", params=dict(sha1hex="eq." + sha1)
        )
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json:
            return resp_json[0]
        else:
            return None

    def get_html_meta(self, sha1: str) -> Optional[Dict[str, Any]]:
        resp = requests.get(
            self.api_url + "/html_meta", params=dict(sha1hex="eq." + sha1)
        )
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json:
            return resp_json[0]
        else:
            return None

    def get_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        resp = requests.get(self.api_url + "/crossref", params=dict(doi="eq." + doi))
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json:
            return resp_json[0]
        else:
            return None


class SandcrawlerMinioClient:
    def __init__(
        self,
        host_url: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        default_bucket: Optional[str] = "sandcrawler",
    ):
        """
        host is minio connection string (host:port)
        access and secret key are as expected
        default_bucket can be supplied so that it doesn't need to be repeated for each function call

        Example config:

            host="localhost:9000",
            access_key=os.environ['MINIO_ACCESS_KEY'],
            secret_key=os.environ['MINIO_SECRET_KEY'],
        """
        self.mc = minio.Minio(
            host_url, access_key=access_key, secret_key=secret_key, secure=False,
        )
        self.default_bucket = default_bucket

    def _blob_path(self, folder: str, sha1hex: str, extension: str, prefix: str) -> str:
        if not extension:
            extension = ""
        if not prefix:
            prefix = ""
        assert len(sha1hex) == 40
        obj_path = "{}{}/{}/{}/{}{}".format(
            prefix, folder, sha1hex[0:2], sha1hex[2:4], sha1hex, extension,
        )
        return obj_path

    def get_blob(
        self,
        folder: str,
        sha1hex: str,
        extension: str = "",
        prefix: str = "",
        bucket: Optional[str] = None,
    ) -> bytes:
        """
        sha1hex is sha1 of the blob itself

        Fetched blob from the given bucket/folder, using the sandcrawler SHA1 path convention
        """
        obj_path = self._blob_path(folder, sha1hex, extension, prefix)
        if not bucket:
            bucket = self.default_bucket
        assert bucket
        blob = self.mc.get_object(bucket, obj_path,)
        # TODO: optionally verify SHA-1?
        return blob.data
