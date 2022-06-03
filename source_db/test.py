import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import numpy as np
import cv2
# from firebase_admin import db

cred = credentials.Certificate("mykey.json")

# firebase_admin.initialize_app(cred,{
#     #insert your firebase config
# })

# ref = db.reference()
# ref.update({'이름':'김영희'})

# ref = db.reference('이름')
# print(ref.get())

# firebase_admin.initialize_app(cred,{
#     'projectId': 'proj2022-3cd0d'
# })
# db = firestore.client()

# # doc_ref = db.collection('users').document('user02')
# # doc_ref.set({
# #     'level': 30,
# #     'money': 700,
# #     'job': "knight"
# # })

# users_ref = db.collection('asdf')
# docs = users_ref.stream()

# for doc in docs:
#     print('{}=>{}'.format(doc.id, doc.to_dict()))

app = firebase_admin.initialize_app(cred, {
        #insert your firebase config
})


bucket = storage.bucket()

storage.child('').download("","download.jpg")
