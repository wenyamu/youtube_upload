import httplib2
import os

from apiclient.discovery import build

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

'''
浏览器验证,生成证书文件
'''

# 设置代理
os.environ['http_proxy']  = 'http://127.0.0.1:1800'
os.environ['https_proxy'] = 'http://127.0.0.1:1800'


YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_authenticated_service(client_secrets_file, credentials_file):
    flow = flow_from_clientsecrets(client_secrets_file,
        scope=YOUTUBE_UPLOAD_SCOPE,
        message="")
    
    storage = Storage(credentials_file)
    credentials = storage.get()
    
    if credentials is None or credentials.invalid:
        run_flow(flow, storage)
    

if __name__ == '__main__':
    
    client_secrets_file = "client_secrets.json"
    credentials_file = "credentials.json"
    get_authenticated_service(client_secrets_file, credentials_file)
    
