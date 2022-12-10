FILE=. 

.PHONY: tests



tests:
	poetry run isort ${FILE}
	poetry run black ${FILE}
	poetry run docformatter -r --in-place ${FILE} 
	poetry run pflake8 ${FILE}
	poetry run pytest -v ./tests

test-full:
	poetry run isort ${FILE}
	poetry run black ${FILE}
	poetry run docformatter -r --in-place ${FILE} 
	poetry run pflake8 ${FILE}
	poetry run pytest -v --slow ./tests

format:
	poetry run isort ${FILE}
	poetry run black ${FILE}
	poetry run docformatter -r --in-place ${FILE} 