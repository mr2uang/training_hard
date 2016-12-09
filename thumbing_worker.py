import os
from celery import Celery
from PIL import Image
from my_db import db, Album, User

SIZE_16_16 = (16, 16)
SIZE_32_32 = (32, 32)
SIZE_64_64 = (64, 64)
SIZES = [SIZE_16_16, SIZE_32_32, SIZE_64_64]
NAME_16_16 = '.thumbnail16'
NAME_32_32 = '.thumbnail32'
NAME_64_64 = '.thumbnail64'
NAMES = [NAME_16_16, NAME_32_32, NAME_64_64]
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
app = Celery('thumbing_worker', broker='amqp://guest@localhost:5672//')


@app.task
def thumb_picture(file, identify):
    user = User.query.filter_by(username=identify).first()
    db.session.add(Album(file, user))
    in_file_name = os.path.splitext(file)[0]
    out_files = [in_file_name + name for name in NAMES]
    for index in range(len(SIZES)):
        im = Image.open(file)
        im.thumbnail(SIZES[index])
        im.save(out_files[index], "JPEG")
        db.session.add(Album(out_files[index], user))

    db.session.commit()
