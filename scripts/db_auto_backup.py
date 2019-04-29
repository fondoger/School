# -*- coding: UTF-8 -*-

"""本脚本用于定时备份mysql数据库

将mysqldump导出的数据存储到又拍云上。

Crontab命令如下：
# 每月2到31号，每晚凌晨3点备份mysql数据，过期时间为30天
0 3 2-31 * * /bin/bash/python3 /path/to/file.py --db=redis -e30
# 每月1号凌晨3点备份mysql数据，无过期时间
0 3 1 * * /bin/bash/python3 /path/to/file.py --db=redis
# 每月2到31号，每晚凌晨3点备份mysql数据，过期时间为30天
0 3 2-31 * * /bin/bash/python3 /path/to/file.py --db=mysql -e30
# 每月1号凌晨3点备份mysql数据，无过期时间
0 3 1 * * /bin/bash/python3 /path/to/file.py --db=mysql
"""

import os
import sys
import time
import argparse
import hmac
import base64
import hashlib
import logging
import subprocess
from datetime import datetime
from requests import Session, Request
from aliyun_email import AliyunEmail


logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] - %(funcName)s - %(message)s', stream=sys.stdout)
# save log messages to file
log_path = os.path.join(os.path.relpath(__file__), 'db_auto_backup.log')
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] - %(funcName)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

aliyun = AliyunEmail()

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


def backup_mysql(expire_days=30):
    backup_file_name = datetime.now().strftime('mysql-autobackup-%Y-%m-%d-%H:%M:%S.sql.gz')
    cmd = "mysqldump -u{user} -p'{password}' {db_name} | gzip > {output}".format(
        user=DB_USER, password=DB_PASSWORD, db_name=DB_DATABASE, output=backup_file_name)
    try:
        logging.info("executing command: %s" % cmd)
        subprocess.run(cmd, check=True)
        logging.info("uploading file to upyun: %s" % backup_file_name)
        Upyun.upload(backup_file_name, backup_file_name, expire_days)
        logging.info("backup Success!")
    except Exception as e:
        logging.exception("backup failed!")
        aliyun.send_email('1075004549@qq.com', subject='【社交北航】自动备份失败',
                          text_body="%s, 详细信息请查看日志" % str(e))
        sys.exit(1)


def backup_redis(expire=30):

    def save_and_verify():
        """Use background save, and check status"""
        prev_lastsave = subprocess.check_output(['redis-cli', 'lastsave']).decode()
        logging.info("execute cmd: redis-cli bgsave")
        subprocess.run(['redis-cli', 'bgsave'], check=True)
        count = 0
        while count < 30:
            count += 1
            time.sleep(1)
            logging.info("checking dumping status...%d" % count)
            if prev_lastsave != subprocess.check_output(['redis-cli', 'lastsave']).decode():
                logging.info('successfully dumped redis database!')
                return
        raise Exception("can't verify redis bgsave status")

    def get_dump_path():
        """Get redis's dump.rdb path via commands"""
        outputs = subprocess.check_output('redis-cli config get "*" | grep -e "dbfilename" -e "dir" -A1',
                                          shell=True).decode().split("\n")
        filename, directory = outputs[1], outputs[4]
        return directory + '/' + filename

    redis_dump_path = get_dump_path()
    backup_file_name = datetime.now().strftime('redis-autobackup-%Y-%m-%d-%H:%M:%S.rdb')

    try:
        save_and_verify()
        Upyun.upload(redis_dump_path, backup_file_name, expire)
        logging.info("backup success!")
    except Exception as e:
        logging.exception("backup failed!")
        aliyun.send_email('1075004549@qq.com', subject='【社交北航】自动备份失败',
                          text_body="%s, 详细信息请查看日志" % str(e))
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script is used to backup redis and mysql databases.')
    parser.add_argument('--db', help='database type, redis or mysql',
                        choices=['redis', 'mysql'], required=True)
    parser.add_argument("-e", "--expire-days", help="how long this backup will be kept, days",
                        type=int)
    args = parser.parse_args()
    if args.db == 'redis':
        backup_redis(args.expire_days)
    elif args.db == 'mysql':
        backup_mysql(args.expire_days)
    sys.exit(0)
