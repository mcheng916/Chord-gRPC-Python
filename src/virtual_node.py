import json
import logging
import os
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
        self.STABLE_PERIOD = config["stabilize_period"]
        self.FIXFINGER_PERIOD = config["fixfinger_period"]
        self.CHECKPRE_PERIOD = config["checkpre_period"]
        # print("LOG_SIZE:\t", self.LOG_SIZE, "\nSIZE:\t\t", self.SIZE, "\nREP_NUM:\t", self.REP_NUM)

        self.local_addr = local_addr
        self.remote_addr = remote_addr

        # Set up Logger
        # create logger with 'chord'
        self.logger = logging.getLogger("chord")
        self.logger.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('[%(asctime)s,%(msecs)d %(levelname)s]: %(message)s',
                                      datefmt='%M:%S')
        # create file handler which logs even debug messages
        os.makedirs(os.path.dirname('log/logger-%d.txt' % self.local_addr), exist_ok=True)
        fh = logging.FileHandler('log/logger-%d.txt' % self.local_addr)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def run(self):
        pass

        

if __name__ == "__main__":
    virtual_node = Virtual_node("127.0.0.1:7000", "127.0.0.1:7000")
