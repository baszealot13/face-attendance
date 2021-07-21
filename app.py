from flask import Flask, flash, jsonify, render_template, render_template_string, request, Response, redirect, abort, stream_with_context

from datetime import datetime
import time
import os
import cv2
import face_recognition
import json
import asyncio
import mysql.connector as mysql
import numpy as np

try:
    os.mkdir('./stores')
except OSError as error:
    pass

app = Flask(__name__)

if app.config["ENV"] == "production":
    app.config.from_object("config.ProductionConfig")
elif app.config["ENV"] == "development":
    app.config.from_object("config.DevelopmentConfig")

app.secret_key = app.config["SECRET_KEY"]

app.config["TEMPLATES_AUTO_RELOAD"] = True

global capture, whoru, success, error_message, res_status, time_interval
capture = 0
success = False
res_status = 400
error_message = ""
time_interval = 5

db = mysql.connect(
    host=app.config["DB_HOST"],
    user=app.config["DB_USER"],
    passwd=app.config["DB_PASSWD"],
    port=app.config["DB_PORT"],
    database=app.config["DB_NAME"]
)

def generate_frames():
    camera = cv2.VideoCapture(0)
    global capture, whoru, success, error_message, res_status
    while(True):
        ret, frame = camera.read()
        if not ret:
            pass
        else:
            if(capture):
                now = datetime.now()
                p = os.path.sep.join(
                    ['stores', f'face-{whoru.lower()}-{str(now).replace(":", "")}.png'])
                cv2.imwrite(p, frame)

                load_image = face_recognition.load_image_file(p)
                face_locations = face_recognition.face_locations(load_image)

                capture = 0

                if (len(face_locations) > 1):
                    success = False
                    res_status = 400
                    error_message = "More than one face detected, please try again."
                    os.remove(p)
                    break
                else:
                    face_encoding = face_recognition.face_encodings(load_image)
                    if (len(face_encoding) > 0):
                        json_face_enc = json.dumps(face_encoding[0].tolist())

                        os.remove(p)
                        success = True
                        try:
                            db.cursor().execute(
                                "INSERT INTO faces (name, face_code) VALUES (%s, %s)", (whoru, json_face_enc))
                            db.commit()
                            break
                        except:
                            success = False
                            res_status = 409
                            error_message = "Conflicts, name."
                            db.rollback()
                            break
                    break

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def generate_comparing_frames():
    video_capture = cv2.VideoCapture(0)

    sqlcursor = db.cursor()
    sqlcursor.execute("SELECT id, name, face_code FROM faces")
    results = sqlcursor.fetchall()

    tc_buffer = {}
    known_face_id = []
    known_face_names = []
    known_face_encodings = []

    for row in results:
        lrow = list(row)
        lrow[2] = lrow[2][1:len(lrow[2])-1]

        known_face_id.append(lrow[0])
        known_face_names.append(lrow[1])
        known_face_encodings.append([float(x) for x in lrow[2].split(",")])

    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while(True):
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Unknown"
                face_id = 0
                dt_format = '%Y-%m-%d %H:%M:%S'
                diff_minutes = time_interval
                face_matched = False

                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    face_id = known_face_id[best_match_index]
                    timecheck = datetime.now()
                    face_matched = True
                
                face_names.append(name)
                
                if face_matched == True:
                    if len(tc_buffer) >= 1000:
                        tc_buffer = {}

                    if len(tc_buffer) > 0:
                        if name in tc_buffer:
                            bufftime = datetime.strptime(tc_buffer[name], dt_format)
                            diff_minutes = (timecheck - bufftime).seconds/60

                    if diff_minutes >= time_interval:
                        db.cursor().execute(
                            "INSERT INTO time_check (face_id, timechecking) VALUES (%s, %s)", (face_id, timecheck))
                        db.commit()
                        tc_buffer[name] = timecheck.strftime(dt_format)
                
        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            colors = (0, 0, 255)
            if 'Unknown' not in name:
                colors = (0, 200, 0)

            cv2.rectangle(frame, (left, top), (right, bottom), colors, 2)
            cv2.rectangle(frame, (left, bottom - 35),
                          (right, bottom), colors, cv2.FILLED)

            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        font, 1.0, (255, 255, 255), 1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


@stream_with_context
def watch_log_streaming():
    logbuffers = []
    yield render_template_string('<h4>Logs</h4>')
    while True:
        sqlcursor = db.cursor()
        sqlcursor.execute(
            "SELECT name, timechecking FROM time_check INNER JOIN faces ON time_check.face_id=faces.id WHERE DATE(timechecking)=CURRENT_DATE() ORDER BY timechecking ASC")
        results = sqlcursor.fetchall()

        # yield render_template_string('<table style="width:100%"><tr><th style=width:50%">Name</th><th style=width:50%">Attendance</th><tr>')
        
        for row in results:
            if f'{row[0]}-{row[1]}' not in logbuffers:
                yield render_template_string(f'<p><span>{row[0]}</span> - <span>{row[1]}</span></p>')
                logbuffers.append(f'{row[0]}-{row[1]}')

        # yield('<table>')
        time.sleep(time_interval)
        # await asyncio.sleep(3)(time_interval)


@app.route('/')
def index():   
    sqlcursor = db.cursor()
    sqlcursor.execute("SELECT id, name, face_code FROM faces")
    results = sqlcursor.fetchall()
    
    if len(results) == 0:
        return redirect('/faceregister')
    else:
        return render_template('index.html')


@app.route('/faceregister', methods=["GET", "POST"])
async def faceregister():
    if request.method == "POST":
        global capture, whoru, success, error_message, res_status
        whoru = request.form.get('whoru')
        capture = 1

        await asyncio.sleep(3)

        if success == False:
            return render_template("error.html", error={
                "status": res_status,
                "message": error_message
            })
        else:
            flash('New Face Registered')
            return redirect('/faceregister')
    else:
        return render_template('faceregister.html')

@app.route('/report', methods=["GET", "POST"])
def report():
    sqlcursor = db.cursor()
    display = "SELECT name, timechecking FROM time_check INNER JOIN faces ON time_check.face_id=faces.id"
    condition = f"{display} WHERE DATE(timechecking)=CURRENT_DATE()"
    command = f"{condition} ORDER BY timechecking ASC"
    tmpcondition = None

    if request.method == "POST":
        name = request.form.get('name')
        date = request.form.get('date')
        value = None

        print(f"name = {name}")
        print(f"date = {date}")

        if name:
            tmpcondition = "WHERE name=%(name)s"
            value = ({"name": name})

        if date:
            if tmpcondition != None:
                tmpcondition += "AND DATE(timechecking)=%(date)s"
                value = ({"name":name, "date": date})
            else:
                tmpcondition = "WHERE DATE(timechecking)=%(date)s"
                value = ({"date": date})

        print(f"tmpcondition {tmpcondition}")
        if tmpcondition != None:
            condition = f"{display} {tmpcondition}"
            command = f"{condition} ORDER BY timechecking ASC"
            print(f"command {command}")
            sqlcursor.execute(command, value)
        else:
            sqlcursor.execute(command)
    else:
        sqlcursor.execute(command)
        
    results = sqlcursor.fetchall()

    return render_template("report.html", results=results)

@app.route('/video_streaming')
def video_streaming():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_comparing')
def video_comparing():
    return Response(generate_comparing_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/watching_logs')
def watching_logs():
    return Response(watch_log_streaming())
# camera.release()
# cv2.destroyAllWindows()

# if __name__ == '__main__':
#     app.run(port=8000)
