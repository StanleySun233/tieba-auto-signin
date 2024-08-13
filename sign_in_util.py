import hashlib
import json
import logging
import time
import requests
import api


class TiebaSignin():
    def __init__(self):
        # 获取日志记录器对象
        self.logger = logging.getLogger(__name__)
        # 存储用户所关注的贴吧
        self.follow = []
        # 用户的BDUSS
        self.BDUSS = ""
        # 用户的tbs
        self.tbs = ""
        # 用户名字
        self.name = ""
        # Server酱
        self.server = ""

    def set_bduss(self, BDUSS):
        self.BDUSS = BDUSS

    def get_user_tbs(self):
        try:
            response = requests.get(api.TBS_URL, cookies={"BDUSS": self.BDUSS})
            js = json.loads(response.text)
            if int(js["is_login"]) == 1:
                self.logger.info("获取tbs成功")
                self.tbs = js["tbs"]
            else:
                self.logger.warning("获取tbs失败 -- {}".format(js))
        except Exception as e:
            self.logger.error("获取tbs部分出现错误 -- {}".format(e))

    def get_follow(self):
        self.follow = []
        try:
            response = requests.get(api.LIKE_URL, cookies={"BDUSS": self.BDUSS})
            js = json.loads(response.text)
            self.logger.info("获取贴吧列表成功")
            follow = js["data"]["like_forum"]
            for i in follow:
                self.follow.append({'name': i["forum_name"], 'is_sign': i["is_sign"]})
        except Exception as e:
            self.logger.error("获取贴吧列表部分出现错误 -- {}".format(e))

    def get_unsuccessful_list(self):
        return [i["name"] for i in self.follow if i["is_sign"] == 0]

    def sign(self, name, sleep=0.2):
        data = {"kw": name,
                "tbs": self.tbs,
                "sign": hashlib.md5(("kw=" + name + "tbs=" + self.tbs + "tiebaclient!!!").encode("utf-8")).hexdigest()}
        try:
            response = requests.post(api.SIGN_URL, data=data, cookies={"BDUSS": self.BDUSS})
            js = json.loads(response.text)
            if int(js["error_code"]) == 0:
                self.logger.info("签到成功: {}".format(name))
            else:
                self.logger.error("签到失败: {}".format(name))
        except Exception as e:
            self.logger.error("{}: 签到失败 -- {}".format(name, e))
        time.sleep(sleep)

    def server_push(self):
        self.get_follow()
        unsuccessful_list = self.get_unsuccessful_list()

        total_cnt = len(self.follow)
        unsuccessful_cnt = len(unsuccessful_list)
        success_cnt = total_cnt - unsuccessful_cnt

        if success_cnt == total_cnt:
            title = '[成功] {}'.format(self.name)
            desp = '本次签到{}个贴吧，签到成功{}个，签到失败{}个。'.format(total_cnt, success_cnt, unsuccessful_cnt)
            short = '签到成功{}个'.format(success_cnt)
        else:
            title = '[失败] {}'.format(self.name)
            desp = '本次签到{}个贴吧，签到成功{}个，签到失败{}个，失败列表: {}。'.format(total_cnt, success_cnt,
                                                                                     unsuccessful_cnt,
                                                                                     '，'.join(unsuccessful_list))
            short = '签到失败{}个'.format(unsuccessful_cnt)

        data = {"title": title, "desp": desp, "short": short}
        header = {"Content-type": 'application/x-www-form-urlencoded'}
        response = requests.post(api.SERVER_URL.format(self.server), headers=header, data=data)
        self.logger.info("已经向server酱发布推送")
        self.logger.info(response.text)

    def run(self, bduss, name, server, retry_time=5, delay_round=5):
        self.BDUSS = bduss
        self.name = name
        self.server = server
        self.get_user_tbs()
        flag = retry_time
        while flag:
            self.logger.info("当前次数: {}, 所有次数: {}".format(retry_time - flag + 1, retry_time))
            self.get_follow()
            unsuccessful_list = self.get_unsuccessful_list()
            self.logger.info("所有关注: {}".format(len(self.follow)))
            self.logger.info("等待签到: {}".format(len(unsuccessful_list)))
            for i in unsuccessful_list:
                self.sign(i)

            self.get_follow()
            unsuccessful_list = self.get_unsuccessful_list()
            self.logger.info("签到成功: {}".format(len(self.follow) - len(unsuccessful_list)))
            self.logger.info("签到失败: {}".format(len(unsuccessful_list)))
            if len(unsuccessful_list) == 0:
                self.logger.info("所有贴吧签到成功，提前退出")
                break
            self.logger.info("等待: {}".format(delay_round))
            time.sleep(delay_round)
            flag -= 1
        if server != '':
            self.server_push()
        return {"user_name": name,
                "fail_num": len(self.get_unsuccessful_list()),
                "fail_list": self.get_unsuccessful_list()}
