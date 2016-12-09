#!/usr/bin/env python3
import unittest
import shutil
import io
import tempfile
from flask import request

try:
    from ..upload_service import app
    from ..my_db import db, User, Album
except:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from upload_service import app
    from my_db import db, User, Album


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app = app
        self.app.config['TESTING'] = True
        self.db = db
        self.db.create_all()
        with open(path.join(self.test_dir, 'pic.jpg'), 'w') as f:

        self.User = User
        self.user = self.User(
            username='test',
            email='test@gmail.com'
        )
        self.Album = Album
        self.pic = self.Album(
            path='/home/begood/pic.jpg',
            user=self.user
        )
        self.db.session.add(self.user)
        self.db.session.add(self.pic)
        self.db.session.commit()
        self.app.debug = True

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        self.db.session.remove()
        self.db.drop_all()

    def test_Upload(self):
        client = self.app.test_client()
        resp1 = client.post('/')
        resp2 = client.post('/',
                            data=dict(
                                file=(None, ''), id='test'
                            ),
                            content_type="multipart/form-data")
        resp3 = client.post(
            '/',
            data=dict(
                file=(io.BytesIO(b'test'),
                      'test.jpg'), id='test'
            ),
            content_type="multipart/form-data")
        assert '400' in str(resp1.status)
        assert '404' in str(resp2.status)
        assert '302' in str(resp3.status)

    def test_create_user(self):
        assert self.User.query.count() == 1
        self.db.session.add(self.User('test2', 'abc@gmail.com'))
        self.db.session.commit()
        assert self.User.query.count() == 2

    def test_get_user(self):
        user = self.User.query.first()
        assert user.username == 'test'
        assert user.email == 'test@gmail.com'

    def test_delete_user(self):
        user = self.User.query.first()
        assert self.User.query.count() == 1
        self.db.session.delete(user)
        self.db.session.commit()
        assert self.User.query.count() == 0

    def test_add_pic(self):
        assert self.Album.query.count() == 1
        self.db.session.add(self.Album('test/path', self.user))
        self.db.session.commit()
        assert self.Album.query.count() == 2

    def test_get_pic(self):
        assert self.Album.query.count() == 1
        pic = self.Album.query.first()
        print(pic.path)
        assert pic.path == '/home/begood/pic.jpg'

    def test_delete_pic(self):
        assert self.Album.query.count() == 1
        self.db.session.delete(self.Album.query.first())
        self.db.session.commit()
        assert self.Album.query.count() == 0

    def test_api(self):
        client = self.app.test_client()
        api_images = client.get('/images')
        assert '200' in api_images.status
        api_rename = client.put('/images/rename', content_type='application/json',
                                data={
                                    'name': 'pic',
                                    'rename': 'repic',
                                    'user': 'test'
                                })
        print(api_rename)

if __name__ == '__main__':
    unittest.main()
