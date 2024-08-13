docker build -t tieba-auto-signin .

docker run -d -p 5432:5000 --restart=always tieba-auto-signin
