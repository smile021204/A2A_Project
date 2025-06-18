#!/bin/bash

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

# 사용할 Conda 환경 이름
CONDA_ENV_NAME="a2a-gpu"

# Conda 환경 활성화
echo "Activating Conda environment: $CONDA_ENV_NAME"
source ~/anaconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME

# 각 에이전트를 백그라운드에서 실행 (&)
echo "Starting all agent servers..."
uvicorn fetcher_agent:app --port 8001 &
uvicorn summarizer_agent:app --port 8002 &
uvicorn coordinator_agent:app --port 8000 &
uvicorn reviewer_agent:app --port 8003 &

# 모든 백그라운드 작업이 끝날 때까지 스크립트가 종료되지 않도록 대기
wait