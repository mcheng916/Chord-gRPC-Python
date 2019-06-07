#! /bin/bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./server.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./chaosmonkey.proto
