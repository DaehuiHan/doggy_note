from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import config
import os

app = Flask(__name__)

SECRET_KEY = config.DATABASE_CONFIG['sceret_key']

client = MongoClient('localhost', 27017)
db = client.dbsparta_plus_week4


# port = config.DATABASE_CONFIG['port']
# username = config.DATABASE_CONFIG['user']
# password = config.DATABASE_CONFIG['password']
# host = config.DATABASE_CONFIG['host']
# db_name = config.DATABASE_CONFIG['dbname']

# client = MongoClient(host, port, username=username, password=password)
# db = client.doggynotedb



@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    
    #최초 접속시 login page로 라우팅
    if token_receive is None:
        return render_template('/login.html')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        #DB에서 값 호출
        username = payload['id']
        posts = list(db.diarys.find({}))
        # objectID를 처리하기 위한 반복문
        for i in range(len(posts)):
            posts[i]['_id'] = str(posts[i]['_id'])
        #결과 출력    
        return render_template('index.html', posts=posts, username=username)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)
 
# 로그인
@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60*60)  # 로그인 1시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디 or 비밀번호가 일치하지 않습니다.'})

 
@app.route('/sign_up')
def sign_up():
   return render_template('signup.html')
 
@app.route('/sign_up/save', methods=['POST'])
def save():
    # 회원가입
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    name_receive = request.form['name_give']
    # DB에 저장
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "name": name_receive,                                       # 이름
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})
 
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


 # 저장하기(POST) API\
@app.route('/diarys', methods=['POST'])
def save_lists():
    name_receive = request.form['name_give']
    date_receive = request.form['date_give']
    sleep_receive = request.form['sleep_give']
    poop_receive = request.form['poop_give']
    feeding_receive = request.form['feeding_give']
    condition_receive = request.form['condition_give']
    another_receive = request.form['another_give']
    writer_receive = request.form['writer_give']
    file = request.files["file_give"]
     
    extension = file.filename.split('.')[-1]
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'file-{mytime}'    
    save_to = f'static/{filename}.{extension}'
    file.save(save_to)
            
    doc = {'name': name_receive,
           'date': date_receive,
           'sleep': sleep_receive,
           'poop': poop_receive,
           'feeding': feeding_receive,
           'condition': condition_receive,
           'another': another_receive,
           'writer':writer_receive,
           'file':f'{filename}.{extension}',
           }
    db.diarys.insert_one(doc)

    return jsonify({'msg': '저장완료!'})

@app.route('/detail/<post_id>')
def detail(post_id):
    token_receive = request.cookies.get('mytoken')
    
    #로그인 하지 않은채로 접속시 로그인화면으로
    if token_receive is None:
        return render_template('/login.html')
    
    
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        #DB에서 값 호출
        username = payload['id']
        post = list(db.diarys.find({"_id":ObjectId(post_id)}))
        return render_template("detail.html", post_id=post_id, post=post, username=username)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/update_post', methods=['POST'])
def update_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        
        name_receive = request.form['name_give']
        date_receive = request.form['date_give']
        sleep_receive = request.form['sleep_give']
        poop_receive = request.form['poop_give']
        feeding_receive = request.form['feeding_give']
        condition_receive = request.form['condition_give']
        another_receive = request.form['another_give']
        
        new_doc = {
           'name': name_receive,
           'date': date_receive,
           'sleep': sleep_receive,
           'poop': poop_receive,
           'feeding': feeding_receive,
           'condition': condition_receive,
           'another': another_receive,
           }
        
        currentImgSrc_receive = request.form['currentImgSrc_give'].split('/')
        target_dir = currentImgSrc_receive[-2]
        target_file = currentImgSrc_receive[-1]
        target_src = f"{target_dir}/{target_file}"
        if 'file_give' in request.files:
            if os.path.exists(target_src):
                os.remove(target_src)
            else:
                print('파일 없음')    
            file = request.files["file_give"]
            extension = file.filename.split('.')[-1]
            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
            filename = f'file-{mytime}'    
            save_to = f'static/{filename}.{extension}'
            file.save(save_to)
            new_doc['file'] = f'{filename}.{extension}'
        db.diarys.update_one({'writer': payload['id']}, {'$set':new_doc})
        return jsonify({"result": "success", 'msg': '업데이트 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
    
    
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

