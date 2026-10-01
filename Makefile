.PHONY: check test selftest validate leakscan probe matrix watch

check: validate matrix test selftest

matrix:
	python3 scripts/matrix.py check

watch:
	python3 scripts/watch.py check

validate:
	claude plugin validate --strict .

test:
	python3 -m unittest discover -s tests

selftest:
	bash scripts/selftest.sh
	bash scripts/leakscan.sh --selftest

leakscan:
	bash scripts/leakscan.sh

# live, costs a model call per harness; exit codes in scripts/probe.sh
probe:
	-for h in claude cursor agy copilot grok codex opencode; do bash scripts/probe.sh $$h; done
