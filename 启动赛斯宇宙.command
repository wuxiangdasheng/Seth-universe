#!/bin/bash

# 赛斯宇宙 - 双击启动

cd "$(dirname "$0")/wiki"

if lsof -ti:8081 > /dev/null 2>&1; then
    lsof -ti:8081 | xargs kill -9 2>/dev/null
    sleep 1
fi

python3 server.py &
sleep 1
open http://localhost:8081
wait
