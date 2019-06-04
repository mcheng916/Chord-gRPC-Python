from virtual_node import Virtual_node
import logging
from concurrent import futures
import time
import click
import grpc
import server_pb2_grpc
import csv
import logging
import logging.handlers
import sys
import os
import socket
import json

@click.command()
@click.argument('address', default='0.0.0.0:7000')
@click.option('--id', type=int, default=0)
@click.option('--join', type=str)
@click.option('--server_config_file', default='config.json')
def start_server(address, id, join, server_config_file):
    # 1024*1024 = 10MB is the size

    server_config = json.load(open(server_config_file))
    server_name = f'{id}-{address.replace(":", "-")}'

    logger = logging.getLogger('Chord')
    logger.setLevel(logging.INFO)
    # # Terminal log output
    # term_handler = logging.StreamHandler(sys.stdout)
    # term_handler.setLevel(logging.INFO)
    # term_handler.setFormatter(logging.Formatter("[%(asctime)s - %(levelname)s]: %(message)s"))
    # logger.addHandler(term_handler)
    # # Record write-ahead log (wal) once get rpc 'appendEntries'
    # os.makedirs('log', exist_ok=True)
    # wal_handler = logging.FileHandler(f'log/{server_name}-wal.log')
    # wal_handler.setLevel(logging.CRITICAL)
    # wal_handler.setFormatter(logging.Formatter("[%(asctime)s - %(levelname)s]: %(message)s"))
    # # WARN: this will overwrite the log
    # logger.addHandler(wal_handler)
    # logger.addHandler(term_handler)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    virtual_node = Virtual_node(id, address, join, server_config)
    server_pb2_grpc.add_ServerServicer_to_server(virtual_node, server)
    server.add_insecure_port(address)
    server.start()
    virtual_node.run()
    logger.info(f'{socket.gethostname()}')
    logger.info(f'Server [{server_name}] listening {address}')
    try:
        while True:
            time.sleep(24*60*60)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    start_server()
