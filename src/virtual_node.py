import json
import logging
import server_pb2_grpc

# This class represents a virtual node
class Virtual_node(server_pb2_grpc.ServerServicer):
    def __init__(self, local_addr, remote_addr):
        # Read configuration from json file
        config = json.load(open("config.json"))
        self.LOG_SIZE = config["log_size"]
        self.SIZE = 1 << self.LOG_SIZE
        self.REP_NUM = config["replication_num"]
        self.SUCCESSOR_NUM = config["successor_num"]
        # print("LOG_SIZE:\t", self.LOG_SIZE, "\nSIZE:\t\t", self.SIZE, "\nREP_NUM:\t", self.REP_NUM)

        self.local_addr = local_addr
        self.remote_addr = remote_addr

        

if __name__ == "__main__":
    virtual_node = Virtual_node("127.0.0.1:7000", "127.0.0.1:7000")
