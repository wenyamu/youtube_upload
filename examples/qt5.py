import sys
import os
import paramiko
import hashlib
import pytz
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QProgressBar

class UploadApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.server_label = QLabel('Server Address:')
        self.server_input = QLineEdit("5.77.17.18")
        layout.addWidget(self.server_label)
        layout.addWidget(self.server_input)
        
        self.port_label = QLabel('Port:')
        self.port_input = QLineEdit("22")
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)
        
        self.username_label = QLabel('Username:')
        self.username_input = QLineEdit("root")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit("123456")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        
        self.file_label = QLabel('File Path:')
        self.file_input = QLineEdit("test.mp4")
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.file_label)
        layout.addWidget(self.file_input)
        layout.addWidget(self.browse_button)
        
        self.upload_button = QPushButton('Upload')
        self.upload_button.clicked.connect(self.start_upload)
        layout.addWidget(self.upload_button)
        
        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)
        
        self.setLayout(layout)
        self.setWindowTitle('Upload Video to Server')
        self.setGeometry(600, 300, 300, 400)
        
        self.show()
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open File')
        self.file_input.setText(file_path)
        
    def calculate_hash(self, file_path, hash_type='MD5'):
        """
        计算文件的哈希值
        :param file_path: 文件路径
        :param hash_type: 哈希类型，默认为 MD5, 还可以指定其它,如 SHA-256
        :return: 文件的哈希值
        """
        hash_func = hashlib.new(hash_type)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
            #从哈希值的索引8开始取长度为24-8的字符串
            hash_val = hash_func.hexdigest()[8:24] 
            new_file_name = hash_val+os.path.splitext(file_path)[1]
        return new_file_name
        
    def start_upload(self):
        server_ip  = self.server_input.text()
        port       = int(self.port_input.text())
        username   = self.username_input.text()
        password   = self.password_input.text()
        local_path = self.file_input.text()
        
        # 上传文件到服务器后的位置和名称
        up_dir = "/root/"# 最后的/号一定要加上
        hash_file_name = self.calculate_hash(local_path)
        remote_path = os.path.join(up_dir, hash_file_name)
        
        self.upload_button.setEnabled(False)
        self.progressBar.setValue(0)
        
        def update_progress(transferred, total):
            progress = int((transferred / total) * 100)
            self.progressBar.setValue(progress)
            
        upload_file(server_ip, port, username, password, local_path, remote_path, callback=update_progress)
        self.upload_button.setEnabled(True)
        
def cn_to_us_time(bj_time_str):
    
    # 使用datetime模块解析北京时间字符串 2023-04-01 07:00:00
    # 将字符串解析为datetime对象
    bj_time = datetime.strptime(bj_time_str, '%Y-%m-%d %H:%M:%S')
    
    # 转换为北京时区 2023-04-01 07:00:00+08:00
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_time = bj_tz.localize(bj_time)
    
    # 转换为UTC时间 2023-03-31 23:00:00+00:00
    utc_time = bj_time.astimezone(pytz.utc)
    
    # 将时间转换为 iso 8601 utc格式 2023-03-31T23:00:00.0Z
    # 将datetime对象格式化为字符串
    formatted_time = utc_time.strftime("%Y-%m-%dT%H:%M:%S.0Z")
    
    return formatted_time
    
def upload_file(server_ip, port, username, password, local_path, remote_path, callback=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(server_ip, port=port, username=username, password=password)
        sftp = ssh.open_sftp()
        
        try:
            remote_file_stat = sftp.stat(remote_path)
            local_file_stat  = os.stat(local_path)
            # 如果本地和远程文件的大小相等
            if remote_file_stat.st_size == local_file_stat.st_size:
                print("文件已经存在")
            else:
                raise IOError() # 手动引发一个异常
                
        except IOError:
            print("文件不存在,或大小不相等")
            
            try:
                print("开始上传文件到服务器")
                sftp.put(local_path, remote_path, callback=callback)
                print("上传成功")
                
            except:
                print("上传文件到服务器失败")
                return # 退出函数,不向下执行
                #raise # 重新抛出异常，中断程序执行
                #sys.exit(1) # 退出程序, qt5界面会被关闭
        
        print("开始上传文件到 youtube")
        
        utc_time_str = cn_to_us_time('2024-11-30 7:00:00')
        print(utc_time_str)
        command0 = '''
        python3 -V
        '''
        
        command1 = '''
        wget https://github.com/tokland/youtube-upload/archive/master.zip
        unzip master.zip
        cd youtube-upload-master
        # 安装程序
        python3 setup.py install
        '''
        command2 = '''
        pip install --upgrade google-api-python-client
        pip install --upgrade google-auth-oauthlib google-auth-httplib2
        pip install --upgrade oauth2client
        '''
        command3 = f'''
        youtube-upload \
          --title="dddd" \
          --description="test description" \
          --category="People & Blogs" \
          --tags="mutter, beethoven" \
          --client-secrets="/root/cs.json" \
          --credentials-file="/root/cr.json" \
          --playlist="My Blogs" \
          --publish-at="{utc_time_str}" \
          {remote_path}
        '''
        
        # 连接成功后执行命令
        stdin, stdout, stderr = ssh.exec_command(command0)
        #打印命令输出
        output = stdout.read().decode()
        error  = stderr.read().decode()
        
        print("Output:", output)
        print("Error:", error)
        
        # 关闭 sftp 连接
        sftp.close()
    except paramiko.ssh_exception.AuthenticationException:
        print("用户名或密码错误")
    except paramiko.ssh_exception.SSHException:
        print("SSH 异常")
    except paramiko.ssh_exception.NoValidConnectionsError:
        print("无法连接服务器")
    except Exception as e:
        print(f"异常信息: {str(e)}")
    finally:
        # 关闭 ssh 连接
        ssh.close()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = UploadApp()
    sys.exit(app.exec_())
