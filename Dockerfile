# 使用一个包含 Python 的轻量级基础镜像
FROM python:3.8-alpine

# 设置工作目录
WORKDIR /app

# 复制应用程序代码和文件
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露应用的端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"]
