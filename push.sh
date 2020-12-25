#!/bin/bash

#transfer python code to bb and run 


scp  *.sh *.py bbp:workspace/jeem1000/ 

# profile locally
# python -m cProfile -s time j.py > j.prof

