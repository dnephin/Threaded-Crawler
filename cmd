#!/bin/bash
#
# Build and development related tasks
#


export PYTHONPATH=./conf:./lib:.:$COMMON 

if [ "$1" == "" ]; then
	echo "Usage:
	$0 <operation> [<params>]
	
Operations:
	clean		removev .pyc files
	test		run all tests
	run			run a single module, expcets the module name (with path) as a param
	doc			build the API documentation
"

elif [ "$1" == "test" ]; then
	python ./test/__init__.py

elif [ "$1" == "run" ]; then
	python ${@:2:9}

elif [ "$1" == "clean" ]; then
	find -name \*.pyc -exec rm {} \;

elif [ "$1" == "doc" ]; then
	epydoc -v -o ./doc/API/ --name "Threaded Crawler" --graph all lib/*

else
	echo "Unknown operation '$1'."
fi
