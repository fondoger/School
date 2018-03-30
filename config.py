import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://fondoger:Yq!((&1024@119.28.135.207/TEST'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '123'
    TRAP_BAD_REQUEST_ERRORS = False # For restful api
    TRAP_HTTP_EXCEPTIONS = False
    IMAGE_SERVER = 'http://asserts.fondoger.cn/'

    @staticmethod
    def init_app(app):
        pass



config = {"default": Config}