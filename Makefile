PY := .venv/bin/python

.PHONY: install run demo test eval docker docker-stop clean

install: ## 创建 venv 并安装依赖
	uv venv .venv
	uv pip install --python .venv/bin/python -r requirements.txt
	uv pip install --python .venv/bin/python -e .

run: ## 本地起服务（默认 8000 端口）
	$(PY) -m uvicorn semantic_sql_guard.main:app --host 0.0.0.0 --port 8000

demo: ## 跑全链路 demo（无需起服务）
	$(PY) -m semantic_sql_guard.demo

test: ## 跑测试（basetemp 指向工作区内，规避部分沙箱对系统临时目录的拦截）
	$(PY) -m pytest -q --basetemp="$PWD/.pytest-tmp"

eval: ## 跑样例评测集，输出准确率报告
	$(PY) -m semantic_sql_guard.evaluator

docker: ## docker-compose 一键拉起
	docker compose up -d --build

docker-stop:
	docker compose down

clean:
	rm -rf .pytest_cache .pytest-tmp src/**/__pycache__ data/*.db data/audit.log
