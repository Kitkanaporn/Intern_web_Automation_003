@echo off

cd /d C:\Users\outsource2960\Downloads\test_claude\08_Test_UAT_DOCKER_AUTOMATION

docker run --rm ^
  --env-file .env ^
  -v "%cd%\logs:/app/logs" ^
  uat-automation-test >> logs/task_scheduler_output.log 2>&1