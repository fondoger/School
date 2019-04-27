import json
from flask import jsonify, request
from . import api
from .. import db
from ..models import TempImage
from .errors import bad_request


@api.route('/update', methods=['GET'])
def get_updage_info():
    platform = request.args.get('platform', '')
    if platform == 'ios':
        return "haha"
    if platform == 'android':
        json = {
            "version": "1.0.1",
            "description": "更新功能测试",
            "download_url": None,
        }
        return jsonify(json)
    return bad_request('please specify a platform(ios/android)')


@api.route('/upyun-notify-url', methods=['POST'])
def receive_image_notify():
    # todo, check signature for security
    # http://47.93.240.135/api/v1
    url = request.form.get('url')
    width = int(request.form.get('image-width'))
    height = int(request.form.get('image-height'))
    type = request.form.get('image-type')
    colors = request.form.get('theme_color')
    theme_color = json.loads(colors)[0]['color']
    time = int(request.form.get('time'))
    image = TempImage(url=url, width=width, height=height, type=type,
                      theme_color=theme_color, time=time)
    db.session.add(image)
    db.session.commit()
    return ''

    

