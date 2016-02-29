#!/bin/sh

rm -rf python cpp
mkdir -p python cpp
protoc -I=. --python_out=python --cpp_out=cpp ./gw.proto
