# FACE ATTENDANCE
## _Face Recognition + Time Attendance_

Introduction [here](https://youtu.be/uZgDKjt4Mco)

Face Attendance is face recognition and time attendance system by you can record a times you check in or out with walk through WebCam.

How know it's you?, 1st you need to let this system to recognize your face by go to register menu look straight at the WebCam make sure see whole your face, enter your name click Register button after than you just walk through WebCam.

Everytime you walk through WebCam it not always insert data to database? Face Attendance will store buffer last checked data, if detact your face within 5 minutes after you already checked the times it not save new data of you.

Many Time Attendance system you need waitiing que like scan fingerprint (this need to buy fingerprint scan machine), key your employee code or student code to tracking a times or write paper,  Will it be better? If we can tracking a times check-in/out in multiple times, you walk in your office or school with your friend and have another one and walking behind you check-in or out same times with by no not need to wait que, no need fingerprint scan machine, just Chrome browser and WebCam.

## Specification
- Python 3.7
- Pip 21.1.3
- MySql 5.7.*
- Test on Chrome browser

## Features
- Face checking and stamp the times
- Face registration
- Report

## Installation
- 1st you need to install MySQL (suggest 5.7)
- Install Python3.7 and Pip (to install any packages)
- Download this project
- Run command `pip install -r requirements.txt`
- Create database by use schema `face_attendance.sql`
- Setup config.py at DB_*, whatever database name, user, password and port you want
- Let rock `flask run`

## Database Scheme
```mysql
CREATE TABLE `faces` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `face_code` text NOT NULL,
  `created` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;

CREATE TABLE `time_check` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `face_id` int(11) NOT NULL,
  `timechecking` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;
```

## Config
This one you should adjust `config.py`
```python
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
```

## Environment

Command `flask run` is production by default, you can command `export FLASK_ENV=development` for development environment

```
export FLASK_ENV=development #for development environment
flask run
```

## How to change interval for time checking
`app.py`
```python
global capture, whoru, success, error_message, res_status, time_interval
capture = 0
success = False
res_status = 400
error_message = ""
time_interval = 5 # <- Change here
```

## Roadmap Suggestion
This project is concept to do face recognition and time attendance, If you want to do more you can create table to store employees (or students) and can link to table faces by faces table will foreign key to id of employees table by employees table will store more detail of an employees, time logs report can display like if you track your face in that day more and more times it can display first time to check-in and another column is check-out is latest time you walk through the WebCam.
