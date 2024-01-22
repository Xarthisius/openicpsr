# openicpsr
A simple tool for downloading OpenICPSR projects

### Example (new auth)

```
$ python3 openicpsr.py 122349
Getting session cookies...
Initiating OAuth flow...
Logging in...
Getting file info...
Downloading file: 122349-V1.zip

$ unzip -l /tmp/122349-V1.zip 
Archive:  /tmp/122349-V1.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
    52970  2024-01-22 17:13   2.png
---------                     -------
    52970                     1 file
```
