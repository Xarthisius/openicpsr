# import functools
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}
OPENICPSR_URL = "https://test.openicpsr.org/openicpsr/"

try:
    pid = sys.argv[1]
except IndexError:
    print(f"Usage: {__name__} <PROJECT ID>")
    exit()

with requests.Session() as session:
    # Get required session cookies
    print("Getting session cookies...")
    req = session.get(
        "https://test.openicpsr.org/openicpsr/",
        headers=headers,
    )
    req.raise_for_status()
    cookies = req.cookies  # Get JSESSIONID

    print("Initiating OAuth flow...")
    headers["Referer"] = OPENICPSR_URL
    login_req = session.get(
        f"{OPENICPSR_URL}login",
        headers=headers,
        cookies=cookies,
        allow_redirects=True,
    )
    login_req.raise_for_status()

    action_url_pattern = r'action="([^"]*)"'
    matches = re.findall(action_url_pattern, login_req.text)
    action_url = matches[0] if matches else None

    # Parse the URL to extract query parameters
    url_components = urlparse(action_url.replace("&amp;", "&"))
    query_params = parse_qs(url_components.query)

    # Extract specific decoded query parameters
    params = {
        param: query_params.get(param)[0]
        for param in ["session_code", "client_id", "execution", "tab_id"]
    }
    data = {
        "username": os.environ["ICPSR_EMAIL"],
        "password": os.environ["ICPSR_PASS"],
    }
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    print("Logging in...")
    req = session.post(
        "https://login.uat.icpsr.umich.edu/realms/icpsr/login-actions/authenticate",
        params=params,
        headers=headers,
        cookies=cookies,
        data=data,
        allow_redirects=True,
    )
    req.raise_for_status()
    headers.pop("Content-Type")

    data_url = (
        f"{OPENICPSR_URL}project/{pid}/version/V1/download/project"
        f"?dirPath=/openicpsr/{pid}/fcr:versions/V1"
    )
    print("Getting file info...")
    head_response = session.head(data_url, headers=headers, cookies=cookies)
    head_response.raise_for_status()
    # Get the filename from the Content-Disposition header
    content_disposition = head_response.headers.get("Content-Disposition")
    filename = None
    if content_disposition:
        _, params = content_disposition.split(";")
        for param in params.split(";"):
            key, value = param.strip().split("=")
            if key.lower() == "filename":
                filename = value.strip('"')

    if filename:
        print(f"Downloading file: {filename}")

        # Send a GET request with stream=True to download the ZIP file
        get_response = session.get(data_url, headers=head_response.headers, stream=True)

        # Check if the GET request was successful (status code 200)
        if get_response.status_code == 200:
            # Create a ZipFile object from the content of the response
            with open(f"/tmp/{filename}", "wb") as fp:
                for chunk in get_response.raw:
                    fp.write(chunk)
        else:
            print(
                f"Failed to download ZIP file. Status code: {get_response.status_code}"
            )
    else:
        print("Filename not found in Content-Disposition header.")
