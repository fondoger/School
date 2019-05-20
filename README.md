Social_BUAA Server
========

这是的一个类似微博的校园社交平台后端服务，基于Python Flask。

你可以点此链接进入官方网站：[官网链接](http://fondoger.github.io/Social_School)

这是整个社交北航系统的后端服务，与之配套的还有一个移动端的项目，[项目主页](https://github.com/fondoger/Social_School)。

安装依赖及运行
-------

**安装依赖**

pip install -r requirements.txt


**数据库初始化**

```
python manage.py db init
```

**本地运行**

```bash
python manage.py runserver -h0.0.0.0 -p80
```

**服务器部署**


第一步：

新增环境变量
```
export flask_server_type="development"
```

同时，在`config.py`中定义数据库地址等信息。

第二步：

启动服务，推荐使用[Gunicorn](http://gunicorn.org/)，步骤如下：

```bash
gunicorn -w 3 manage:app -b 0.0.0.0:8000
```

第三步：

配置nginx，转发80端口请求到gunicorn:

```bash
sudo ln -s deployment/nginx /etc/nginx/sites-enabled/mysitename.conf
```

API设计及文档
-------

API采用restful API风格设计。

三种类型的请求：

* GET 获取数据
* POST 创建数据
* PUT/PATCH 修改数据

完整的API参见，[API文档-更新中](https://documenter.getpostman.com/view/2780787/RWMBQAJU#1cbc7b44-0da7-74c2-635e-0efd45567f90)。


使用到的云服务
-------

目前使用到的云服务如下：

* [阿里云学生服务器](https://promotion.aliyun.com/ntms/campus2017.html)：9.9元每月，1核2G，1M带宽。

* [阿里云邮件推送](https://www.aliyun.com/)：用于发送邮件验证码（因为自建邮件服务器容易被封）。

* [又拍云云存储](https://www.upyun.com/)：用于图片存储（阿里云服务器带宽太小，图片加载速度炒鸡慢）。




