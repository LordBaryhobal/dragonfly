import coverage
import os
os.environ.putenv("COVERAGE_PROCESS_START", "$PWD/.coveragerc")
coverage.process_startup()