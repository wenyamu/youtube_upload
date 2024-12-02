#!/usr/bin/env python
#
# Upload videos to Youtube from the command-line using APIv3.
#
# Author: Arnau Sanchez <pyarnau@gmail.com>
# Project: https://github.com/tokland/youtube-upload
"""
Upload a video to Youtube from the command-line.

    $ main.py --title="test title" \
             --description="test" \
             --category=Music \
             --tags="tag1, tag2" \
             1.mp4 2.mp4

"""

import os
import sys
import optparse
import collections
import webbrowser
from io import open

import googleapiclient.errors
import oauth2client

from oauth2client import file

import upload_video
import categories
import lib
import playlists

#导入auth目录下的 __init__.py
import auth
#导入auth目录下的 console.py
from auth import console

# python3 需要安装 progressbar2, 但导入时使用 progressbar
# pip install progressbar2
try:
    import progressbar
except ImportError:
    progressbar = None

class InvalidCategory(Exception): pass
class OptionsError(Exception): pass
class AuthenticationError(Exception): pass
class RequestError(Exception): pass

EXIT_CODES = {
    OptionsError: 2,
    InvalidCategory: 3,
    RequestError: 3,
    AuthenticationError: 4,
    oauth2client.client.FlowExchangeError: 4,
    NotImplementedError: 5,
}

WATCH_VIDEO_URL = "https://www.youtube.com/watch?v={id}"

debug = lib.debug
struct = collections.namedtuple

# 进度条显示
def get_progress_info(file_size):
    """Return a function callback to update the progressbar."""
    progressinfo = struct("ProgressInfo", ["callback", "finish"])
    
    if progressbar:
        bar = progressbar.ProgressBar(maxval=file_size, widgets=[
            progressbar.Percentage(),
            ' ', progressbar.Bar('=', '[', ']'),
            ' ', progressbar.FileTransferSpeed(),
            ' ', progressbar.Timer(),
            #' ', progressbar.AdaptiveETA(),
        ])
        
        #upload_video.py文件中的函数_upload_to_request 获取的
        #status.total_size 和 status.resumable_progress
        def _callback(total_size, completed):
            if not hasattr(bar, "next_update"):
                bar.start()
            bar.update(completed)
        
        def _finish():
            if hasattr(bar, "next_update"):
                return bar.finish()
        
        return progressinfo(callback=_callback, finish=_finish)
    else:
        return progressinfo(callback=None, finish=lambda: True)


def get_category_id(category):
    """Return category ID from its name."""
    if category:
        if category in categories.IDS:
            category_id = categories.IDS[category]
            debug("视频分类: {0} (id={1})".format(category, category_id))
            return str(categories.IDS[category])
        else:
            msg = "{0} 不是一个有效的分类".format(category)
            raise InvalidCategory(msg)


def upload_youtube_video(youtube, options, video_path):
    """Upload video"""
    u = lib.to_utf8
    title = u(options.title)
    if hasattr(u('string'), 'decode'):
        description = u(options.description or "").decode("string-escape")
    else:
        description = options.description
        
    tags = [u(s.strip()) for s in (options.tags or "").split(",")]
    
    file_size = os.path.getsize(video_path)
    #print("文件大小,字节数: ", file_size)
    
    progress = get_progress_info(file_size)
    
    category_id = get_category_id(options.category)
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
            "tags": tags,
            "defaultLanguage": options.default_language,
            "defaultAudioLanguage": options.default_audio_language,
            
        },
        "status": {
            "embeddable": options.embeddable,
            "privacyStatus": ("private" if options.publish_at else options.privacy),
            "publishAt": options.publish_at,
            "license": options.license,
            
        },
        "recordingDetails": {
            "location": lib.string_to_dict(options.location),
            "recordingDate": options.recording_date,
        },
    }
    
    debug("开始上传: {0}".format(video_path))
    try:
        video_id = upload_video.upload(youtube, video_path,
                                       request_body, progress_callback=progress.callback,
                                       chunksize=options.chunksize)
    finally:
        progress.finish()
    return video_id


def get_youtube_handler(options):
    """Return the API Youtube object."""
    home = os.path.expanduser("~")
    default_credentials = os.path.join(home, ".youtube-upload-credentials.json")
    client_secrets = options.client_secrets or os.path.join(home, ".client_secrets.json")
    credentials = options.credentials_file or default_credentials
    #debug("Using client secrets: {0}".format(client_secrets))
    #debug("Using credentials file: {0}".format(credentials))
    
    return auth.get_resource(client_secrets, credentials,
                             get_code_callback=auth.console.get_code)


def parse_options_error(parser, options):
    """Check errors in options."""
    required_options = ["title"]
    missing = [opt for opt in required_options if not getattr(options, opt)]
    if missing:
        parser.print_usage()
        msg = "缺少一些必需的选项: {0}".format(", ".join(missing))
        raise OptionsError(msg)


def run_main(parser, options, videos, output=sys.stdout):
    """Run the main scripts from the parsed options/videos."""
    parse_options_error(parser, options)
    youtube = get_youtube_handler(options)
    
    #上传命令,如果只是为了生成证书文件,可以注释掉
    ''''''
    if youtube:
        for video_path in videos:
            video_id = upload_youtube_video(youtube, options, video_path)
            video_url = WATCH_VIDEO_URL.format(id=video_id)
            debug("视频网址: {0}".format(video_url))
            
            #设置视频封面
            if options.thumb:
                youtube.thumbnails().set(videoId=video_id, media_body=options.thumb).execute()
            #加入播放列表,如果不存在,则先创建播放列表,然后再加入
            if options.playlist:
                playlists.add_video_to_playlist(youtube, video_id,
                                                title=lib.to_utf8(options.playlist), privacy=options.privacy)
            #output.write(video_id)
    else:
        raise AuthenticationError("Cannot get youtube resource")
    

def main(arguments):
    """Upload videos to Youtube."""
    usage = """Usage: %prog [OPTIONS] VIDEO [VIDEO2 ...]
    
    Upload videos to Youtube."""
    parser = optparse.OptionParser(usage)
    
    # 视频元数据
    parser.add_option('-t', '--title', dest='title', type="string",
                      help='Video title')
    parser.add_option('-c', '--category', dest='category', type="string",
                      help='Name of video category')
    parser.add_option('-d', '--description', dest='description', type="string",
                      help='Video description')
    parser.add_option('', '--description-file', dest='description_file', type="string",
                      help='Video description file', default=None)
    parser.add_option('', '--tags', dest='tags', type="string",
                      help='Video tags (separated by commas: "tag1, tag2,...")')
    parser.add_option('', '--privacy', dest='privacy', metavar="STRING",
                      default="public", help='public | unlisted | private')
    parser.add_option('', '--publish-at', dest='publish_at', metavar="datetime",
                      default=None, help='(ISO 8601): YYYY-MM-DDThh:mm:ss.sZ')
    parser.add_option('', '--thumbnail', dest='thumb', type="string", metavar="FILE",
                      help='Image file(JPEG or PNG)')
    parser.add_option('', '--playlist', dest='playlist', type="string",
                      help='Playlist title')
    
    # 不常用元数据
    parser.add_option('', '--embeddable', dest='embeddable', default=True,
                      help='Video is embeddable')
    parser.add_option('', '--license', dest='license', metavar="string",
                      choices=('youtube', 'creativeCommon'), default='youtube',
                      help='License for the video')
    parser.add_option('', '--location', dest='location', type="string",
                      default=None, metavar="latitude=VAL,longitude=VAL[,altitude=VAL]",help='Video location"')
    parser.add_option('', '--recording-date', dest='recording_date', metavar="datetime",                  default=None, help="(ISO 8601): YYYY-MM-DDThh:mm:ss.sZ")
    parser.add_option('', '--default-language', dest='default_language', type="string",
                      default=None, metavar="string",
                      help="(ISO 639-1): en | fr | de | ...")
    parser.add_option('', '--default-audio-language', dest='default_audio_language',                  type="string", default=None, metavar="string",
                      help="(ISO 639-1): en | fr | de | ...")
    
    # 验证
    parser.add_option('', '--client-secrets', dest='client_secrets',
                      type="string", help='Client secrets JSON file')
    parser.add_option('', '--credentials-file', dest='credentials_file',
                      type="string", help='Credentials JSON file')
    
    # 附加选项
    """
    chunksize 参数指定每次上传的每个数据块的大小（以字节为单位）
    为可靠连接设置较高的值，因为块越少，上传速度越快。
    为在可靠性较低的连接上更好地恢复，设置较低的值。
    """
    parser.add_option('', '--chunksize', dest='chunksize', type="int",
                      default=1024 * 1024 * 8, help='Update file chunksize')
    
    options, videos = parser.parse_args(arguments)
    #print(options) #{'title': 'test title', 'description': 'info', ...}
    #print(videos)  #["video1.mp4", "video2.mp4"]
    if options.description_file is not None and os.path.exists(options.description_file):
        with open(options.description_file, encoding="utf-8") as file:
            options.description = file.read()
        
    try:
        #上传命令
        run_main(parser, options, videos)
        #pass
    except googleapiclient.errors.HttpError as error:
        response = bytes.decode(error.content, encoding=lib.get_encoding()).strip()
        raise RequestError(u"Server response: {0}".format(response))
    

def run():
    sys.exit(lib.catch_exceptions(EXIT_CODES, main, sys.argv[1:]))
    
if __name__ == '__main__':
    run()
    
