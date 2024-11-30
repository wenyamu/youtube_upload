# youtube_upload
简易版
修改自: https://github.com/tokland/youtube-upload


## 要安装的包
```
pip install --upgrade google-api-python-client
pip install --upgrade google-auth-oauthlib google-auth-httplib2
pip install --upgrade oauth2client
#进度条
pip install progressbar2
```


注意: 文件的默认位置
### linux
```
/root/.client_secrets.json
/root/.youtube-upload-credentials.json
```
### windows
```
C:\Users\xxx\.client_secrets.json
C:\Users\xxx\.youtube-upload-credentials.json
```

第一次上传会提示验证, 把 url 复制到浏览器中并打开, 一直下一步,最后得到一串字符串,复制然后粘贴到shell中,验证成功即可上传视频.
并且生成 /root/.youtube-upload-credentials.json 文件, 下次上传就不需要再验证了
```
python main.py \
  --title="upload test" \
  --description="description test" \
  --category="People & Blogs" \
  --client-secrets="client_secrets.json" \
  --credentials-file="client_secrets/access_token.json" \
  --privacy=private \
  --publish-at="2024-11-30T15:32:17.0Z" \
  test.mp4 abc.mp4 123.mp4
```

更多参数(还有些参数不常用,没有列出,详细可见源代码)
```
  --description-file="/root/description.txt" # 视频详情文本文件
  --embeddable=True # 允许他人在其网站中嵌入视频, 缺省值为True。
  --tags="mutter, beethoven" # 标签, 仅为了避免拼错词的辅助。
  --playlist="My Vlogs" # 视频加入播放列表,没有则创建
  --thumbnail="img.jpg"  # 视频封面
```

## windows 调用

首先要解决 cmd/powershell 访问youtube的问题
windows cmd/powershell 中访问谷歌

环境：shadowsocks、windows
本地ss端口设置(这里1080)

cmd命令行:(不用socks5)(临时设置)(也可放置环境变量)
```
set http_proxy=http://127.0.0.1:1080
set https_proxy=http://127.0.0.1:1080
```
powershell命令行:
```
$env:http_proxy="http://127.0.0.1:1080"
$env:https_proxy="http://127.0.0.1:1080"
```
简易测试命令：`curl https://www.google.com`（别用ping）

为什么我开启SSR 在PowerShell里 `ping www.github.com` 还是超时呀
因为Ping使用的是ICMP协议，SSR应该只能代理sock5和http协议

## 使用 subprocess 运行命令
```
import os
import subprocess

#设置代理
#此变量是临时的,只在此脚本运行时生效
os.environ['http_proxy']  = 'http://127.0.0.1:1800'
os.environ['https_proxy'] = 'http://127.0.0.1:1800'

client_secrets_file = "client_secrets.json"
credentials_file = "client_secrets/access_token.json"
cmd = [
        'python', 'main.py',
        '--title', "test title666",
        '--client-secrets', f"{client_secrets_file}",
        '--credentials-file', f"{credentials_file}",
        '--description', "test description",
        #'--thumbnail', "vvv/test2.jpg",
        '--privacy', 'private',
        '--publish-at',"2024-12-05T15:32:17.0Z",
        #'--playlist', "My Vlogs666"
        ]
video_list = ['vvv/test1.mp4','vvv/test2.mp4']
cmd.extend(video_list)# 将视频追加到后面
subprocess.run(cmd, shell=True)

```

