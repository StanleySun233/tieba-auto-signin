import logging
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import time
from concurrent.futures import ThreadPoolExecutor
import sign_in_util
from threading import Thread

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "data.db")
db = SQLAlchemy(app)
logging.basicConfig(level=logging.INFO)
executor = ThreadPoolExecutor()
sign_util = sign_in_util.TiebaSignin()


def getNowTime(s="%Y-%m-%d %H:%M:%S") -> str:
    return datetime.today().strftime(s)


# 账号模型
class Account(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    server_token = db.Column(db.Text, nullable=False)
    cookies = db.Column(db.Text, nullable=False)
    create_date = db.Column(db.Text, nullable=False)
    update_date = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Account('{self.uid}', '{self.user_name}', '{self.cookies}', '{self.create_date}', '{self.update_date}')"


# 登录记录模型
class SignInLog(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"SignInLog('{self.uid}', '{self.date}', '{self.message}', '{self.user_name}')"

    def to_dict(self):
        return {"uid": self.uid, "date": self.date, "message": self.message, "user_name": self.user_name}


class AutoSign(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)


def sign(user_name, cookies, server_token=""):
    # 实际的签到逻辑在这里，你需要根据你的需求修改这个函数
    feedback = sign_util.run(cookies, user_name, server_token)
    date = getNowTime()
    new_log = SignInLog(user_name=user_name,
                        date=date)
    if feedback["fail_num"] == 0:
        new_log.message = "签到成功"
    else:
        new_log.message = "签到失败，数量:" + str(feedback["fail_num"])
    with app.app_context():
        db.session.add(new_log)
        db.session.commit()


def schedule_daily_task():
    logging.info("自动签到进程启动")
    while True:
        current_time = getNowTime()
        with app.app_context():
            is_sign = AutoSign.query.all()
            if len(is_sign) == 0:
                is_sign = ''
            else:
                is_sign = is_sign[-1].date
        if is_sign == current_time[:10]:
            pass
        else:
            run_sign_task()
            with app.app_context():
                new_auto_sign = AutoSign(uid=current_time[:10], time=current_time, date=current_time[:10])
                db.session.add(new_auto_sign)
                db.session.commit()
        time.sleep(1)


def run_sign_task():
    # Get the list of accounts and run the sign function for each account
    logging.info("执行每日签到任务")
    with app.app_context():
        accounts = Account.query.all()
    for account in accounts:
        sign(account.user_name, account.cookies, account.server_token)


with app.app_context():
    db.create_all()
    scheduler_thread = Thread(target=schedule_daily_task)
    scheduler_thread.start()


@app.route('/')
def index():
    accounts = Account.query.all()
    return render_template('index.html', accounts=accounts)


@app.route('/add_account', methods=['POST'])
def add_account():
    if request.method == 'POST':
        user_name = request.form['user_name']
        cookies = request.form['cookies']
        server_token = request.form['server_token']
        if server_token is None:
            server_token = ""
        create_date = getNowTime()
        update_date = create_date
        new_account = Account(user_name=user_name,
                              cookies=cookies,
                              server_token=server_token,
                              create_date=create_date,
                              update_date=update_date)
        db.session.add(new_account)
        db.session.commit()

    return redirect(url_for('index'))


@app.route('/add_account_form')
def add_account_form():
    return render_template('add_account.html')


@app.route('/execute_sign_in/<int:uid>')
def execute_sign_in(uid):
    account = Account.query.get(uid)

    # 异步执行 sign 函数
    executor.submit(sign, user_name=account.user_name, cookies=account.cookies, server_token=account.server_token)

    return redirect(url_for('index'))


@app.route('/sign_in_log')
def sign_in_log():
    logs = SignInLog.query.order_by(SignInLog.uid.desc()).all()
    return render_template('sign_in_log.html', logs=logs)


@app.route('/manage_accounts')
def manage_accounts():
    accounts = Account.query.all()
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    for account in accounts:
        logs_today = SignInLog.query.filter(SignInLog.date >= str(current_date),
                                            SignInLog.date < str(current_date + timedelta(days=1)),
                                            SignInLog.user_name == account.user_name).all()

        if len(logs_today) == 0:
            account.status = "未签"
        else:
            logs = [logs.to_dict()["message"] for logs in logs_today]
            if "签到成功" in logs:
                account.status = "成功"
            else:
                account.status = "异常"

    return render_template('manage_accounts.html', accounts=accounts)


@app.route('/edit_account/<int:uid>', methods=['GET', 'POST'])
def edit_account(uid):
    account = Account.query.get(uid)
    if request.method == 'POST':
        account.user_name = request.form['user_name']
        account.cookies = request.form['cookies']
        account.server_token = request.form['server_token']
        if account.server_token is None:
            account.server_token = ""
        account.update_date = getNowTime()
        db.session.commit()
        return redirect(url_for('manage_accounts'))
    return render_template('edit_account.html', account=account)


@app.route('/delete_account/<int:uid>')
def delete_account(uid):
    account = Account.query.get(uid)
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('manage_accounts'))


@app.route('/delete_log/<int:uid>')
def delete_log(uid):
    log = SignInLog.query.get(uid)
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for('sign_in_log'))


@app.route('/sign_in_history/<string:user_name>')
def sign_in_history(user_name):
    logs = SignInLog.query.filter_by(user_name=user_name).all()
    return render_template('sign_in_history.html', sign_in_history=logs)


@app.route('/restart/<string:date>')
def restart(date):
    auto_sign = AutoSign.query.filter_by(date=date).first()
    db.session.delete(auto_sign)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
