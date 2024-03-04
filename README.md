# tieba-auto-signin
# 贴吧自动签到
## 运行
* 代码
```shell
pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python app.py
```
* 访问 http://localhost:5432
## 功能
1. Docker一键部署

进入仓库文件夹后，直接输入`sh build.sh` 或者
```shell
git clone git@github.com:StanleySun233/tieba-auto-signin.git
cd tieba-auto-signin
docker build -t tieba-auto-signin .
docker run -d -p 5432:5000 --restart=always tieba-auto-signin
```

Dockerfile
```dockerfile
FROM python:3.8-alpine
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
EXPOSE 5000

CMD ["python", "app.py"]
```
2. 签到
* 失败自动重新签到(default: 5次)
* 推送签到结果(server酱)
3. 定时签到
* 每日自动签到(default: 8:00 AM)
* 推送签到结果(server酱)
4. 管理系统(基于sqlite)
* 添加账号
* 修改账号
* 删除账号
* 查看签到记录
5. 界面设计
* ~~开发中~~
