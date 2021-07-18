class Config(object):
    DEBUG = False

class ProductionConfig(Config):
    SECRET_KEY = 'secret_123'
    DB_HOST = 'localhost'
    DB_PORT = 3308
    DB_USER = 'prod_user'
    DB_PASSWD = 'password'
    DB_NAME = 'face_attendance'

class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = 'secret_456'
    DB_HOST = 'localhost'
    DB_PORT = 3308
    DB_USER = 'dev_user'
    DB_PASSWD = 'password'
    DB_NAME = 'face_attendance_development'



