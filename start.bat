@echo off
cd src
set FLASK_APP=server
python3 -m flask --debug run
