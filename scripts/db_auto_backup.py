# -*- coding: UTF-8 -*-


"""本脚本用于定时备份mysql数据库

将mysqldump导出的数据存储到又拍云上。

每晚凌晨3点备份数据，Crontab命令如下：
0 3 * * * /bin/bash/python3 /path/to/file.py
"""


import hmac
import base64
import hashlib
import logging
import subprocess
from datetime import datetime
from requests import Session, Request

logging.basicConfig(filename="db_auto_backup.log", level=logging.DEBUG)


# 设置又拍云信息
# 注意: secret = hashlib.md5('操作员密码'.encode()).hexdigest()
OPERATOR_NAME = 'autobackup'
OPERATOR_SECRET = '51bfdb1f889e96484bf31eb74a82e804'
SERVICE_NAME = 'school-db-autobackup'
SERVER_URL = 'https://v0.api.upyun.com'

DB_USER = 'test'
DB_PASSWORD = 'Yq!((&1024'
DB_DATABASE = 'TEST'

class Upyun:
    """使用又拍云提供的REST API上传文件

    文档地址：https://help.upyun.com/knowledge-base/rest_api/
    认证方式采用签名认证：https://help.upyun.com/knowledge-base/object_storage_authorization/#e7adbee5908de8aea4e8af81
    """

    @staticmethod
    def _httpdate_rfc1123(dt=None):
        dt = dt or datetime.utcnow()
        return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

    @staticmethod
    def _sign(client_key, client_secret, method, uri, date, policy=None, md5=None):
        """签名"""
        signarr = []
        for v in [method, uri, date, policy, md5]:
            if v is not None:
                signarr.append(v)
        signstr = '&'.join(signarr)
        signstr = base64.b64encode(
            hmac.new(client_secret.encode(), signstr.encode(),
                     digestmod=hashlib.sha1).digest()
        ).decode()
        return 'UPYUN %s:%s' % (client_key, signstr)

    @staticmethod
    def _send_request(method, url, headers, body):
        """发送请求"""
        s = Session()
        prepped = Request(method, url).prepare()
        prepped.headers = headers
        prepped.body = body
        r = s.send(prepped)
        return r.status_code, r.text

    @staticmethod
    def upload(file_path, target_name, expire=None):
        """上传文件

        :param file_path: 本地路径
        :param target_name: 又拍云上的存储路径
        :param expire: 过期时间(单位:天), 可选
        :return: None
        """
        with open(file_path, 'rb') as f:
            file = f.read()
        date = Upyun._httpdate_rfc1123()
        file_md5 = hashlib.md5(file).hexdigest()
        uri = '/{service}/{target}'.format(service=SERVICE_NAME, target=target_name)
        method = 'PUT'
        signature = Upyun._sign(OPERATOR_NAME, OPERATOR_SECRET, method, uri, date, md5=file_md5)
        print(signature)
        headers = {
            'Authorization': signature,
            'Date': date,
            'Content-Length': str(len(file)),
            'Content-MD5': file_md5,
        }
        if expire is not None:
            headers['x-upyun-meta-ttl'] = expire

        status, content = Upyun._send_request(method, SERVER_URL + uri, headers, file)

        if status != 200:
            raise Exception("Can't upload file via API, status=%d, response: %s" % (status, content))


def main():
    backup_file_name = datetime.now().strftime('autobackup-%Y-%m-%d-%H:%M:%S.mysql-db.gz')
    cmd = "mysqldump -u{user} -p{password} {db_name} | gzip > {output}".format(
        user=DB_USER, password=DB_PASSWORD, db_name=DB_DATABASE, output=backup_file_name)
    try:
        subprocess.run(cmd, check=True)
        Upyun.upload(backup_file_name, backup_file_name, 30)
    except:
        logging.exception("备份失败！")


if __name__ == '__main__':
    main()
    exit(0)
