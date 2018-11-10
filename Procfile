release: ./script/build_static.sh
web: gunicorn --log-level debug --worker-class eventlet -w 1 server:app
