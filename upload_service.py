import os
from flask import Flask, request, redirect, url_for, jsonify
from thumbing_worker import thumb_picture
from werkzeug import secure_filename
from my_db import User, Album, db

ASSET = '/static/asset/'
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + ASSET
ALLOW_EXTENSIONS = set(['jpg'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '********'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOW_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        identify = request.form.get('id', None)
        if 'file' not in request.files or not identify:
            return "Bad request", 400

        file = request.files['file']
        if file.filename == '':
            return "File empty", 404

        if User.query.filter_by(username=identify).first() is None:
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], identify)
            if not os.path.exists(path):
                os.makedirs(path)
            in_file = os.path.join(path, filename)
            file.save(in_file)
            thumb_picture.delay(in_file, identify)
            return redirect(url_for('upload_file',
                                    filename=file.filename))

    return '''
    <!doctype html>
    <title>Upload file</title>
    <hl>Upload file</hl>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=id name=id>
         <input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


def get_length(file):
    return os.path.getsize(file.path)


def get_name(file):
    names = file.path.rsplit('/', 1)[-1]
    return names, names.rsplit('.', 1)[0]


def rename(file, name):
    exten = file.path.rsplit('.', 1)[1]
    return os.path.join(os.path.dirname(file.path), name + '.' + exten)


@app.route('/images', methods=['GET'])
def api():
    if request.method == 'GET':
        pictures = Album.query.all()
        images = dict()
        for pic in pictures:
            full_name, real_name = get_name(pic)
            size = get_length(pic)
            images[full_name] = {
                'name': real_name,
                'path': pic.path,
                'size': size
            }
        return jsonify(result=images)


@app.route('/images/rename', methods=['PUT'])
def rename_pic():
    if request.method == 'PUT':
        data = request.get_json()
        name = data.get('name', '')
        re_name = data.get('rename', '')
        in_user = data.get('user', '')
        if not name or not in_user or not re_name:
            return 'wrong name or user'

        user = User.query.filter_by(username=in_user).first()
        if not user:
            return 'No user in table'

        pics = Album.filter(name, user).all()
        if not pics:
            return 'Pics with that name'

        for pic in pics:
            path = rename(pic, re_name)
            try:
                os.rename(pic.path, path)

            except:
                return 'File in folder not found'
            pic.path = path

        db.session.commit()
        return 'Done!!!'


@app.route('/images/delete', methods=['PUT'])
def detele_pic():
    if request.method == 'PUT':
        data = request.get_json()
        name = data.get('name', '')
        in_user = data.get('user', '')
        if not name or not in_user:
            return 'wrong name or user'

        user = User.query.filter_by(username=in_user).first()
        if not user:
            return 'No user in table'

        pics = Album.filter(name, user).all()
        if not pics:
            return 'No pics with that name'

        for pic in pics:
            try:
                os.remove(pic.path)
            except:
                return 'File in folder not found'
            db.session.delete(pic)

        db.session.commit()
        return 'Done!!!'


@app.route('/images/select', methods=['GET'])
def select_pic():
    if request.method == 'GET':
        data = request.get_json()
        name = data.get('name', '')
        in_user = data.get('user', '')
        if not name or not in_user:
            return ' wrong name or user'

        user = User.query.filter_by(username=in_user).first()
        if not user:
            return 'No user in table'

        pic = Album.filter(name, user).first()
        if not pic:
            return 'No pick with that name'
        full_name, real_name = get_name(pic)
        size = get_length(pic)
        return jsonify(result={
            full_name: {
                'name': real_name,
                'path': pic.path,
                'size': size
            }
        })

if __name__ == '__main__':
    app.run()
