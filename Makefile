.PHONY: help install test demo dataset ml figures all clean

help:
	@echo "LTRROE — available targets:"
	@echo "  make install   Install the package (editable) with dev deps"
	@echo "  make test      Run the test suite"
	@echo "  make demo      Run the standalone demo on the built-in test project"
	@echo "  make dataset   Generate synthetic datasets (project- and task-level)"
	@echo "  make ml        Train Random Forest models (project + task level)"
	@echo "  make figures   Regenerate correlation / diagnostic figures"
	@echo "  make all        dataset -> ml -> figures"
	@echo "  make clean     Remove generated outputs and caches"

install:
	pip install -e ".[dev,xgboost]"

test:
	pytest -q

demo:
	python -m ltrroe.core.demo

# --- pipeline (run in order) ---
dataset:
	python -m ltrroe.synth.project_level
	python -m ltrroe.synth.task_level

ml:
	python -m ltrroe.synth.rf_project
	python -m ltrroe.synth.rf_task

figures:
	python -m ltrroe.synth.spearman

all: dataset ml figures

clean:
	rm -rf outputs/files/* outputs/figures/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
