import json
import logging
import os
import threading
from concurrent import futures
import time
import server_pb2_grpc
import server_pb2
import grpc


# This class represents a virtual node
class Virtual_node(server_pb2_grpc.ServerServicer):
    def __init__(self, local_addr, remote_addr, id):
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
        self.id = id

        self.finger = [[None, None] for _ in range(self.LOG_SIZE)]
        self.successor_list = [[None, None] for _ in range(self.SUCCESSOR_NUM)]
        self.predecessor = [None, None]
        self.next = 0



        # Set up Logger
        # create logger with 'chord'
        self.logger = logging.getLogger("chord")
        self.logger.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('[%(asctime)s,%(msecs)d %(levelname)s]: %(message)s',
                                      datefmt='%M:%S')
        # create file handler which logs even debug messages
        os.makedirs(os.path.dirname('log/logger-%d.txt' % self.id), exist_ok=True)
        fh = logging.FileHandler('log/logger-%d.txt' % self.id)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    # search the local table for the highest predecessor of id
    def closest_preceding_node(self, id):
        i = self.LOG_SIZE - 1
        while i >= 0:
            if self.finger[i][0] > self.id and self.finger[i][0] < id:
                return self.finger[i]
            i -= 1
        return [self.id, self.local_addr]

    # ask node n to find the successor of id
    def find_successor(self, request, context):
        # There is bug in paper algorithm, need to add boundary judgement
        if request.id == self.id:
            return server_pb2.FindSucResponse(id = request.id, ip = self.local_addr)
        if request.id > self.id and request.id <= self.successor_list[0][0]:
            return server_pb2.FindSucResponse(id = self.successor_list[0][0], ip = self.successor_list[0][1])
        else:
            n_next = self.closest_preceding_node(request.id)
            find_request = server_pb2.FindSucRequest(id = n_next[0])
            channel = grpc.insecure_channel(n_next[1])
            stub = server_pb2_grpc.ServerStub(channel)
            find_resp = stub.find_successor(find_request)
            return find_resp

    # return the successor list
    def find_succlist(self, request, context):
        resp = server_pb2.FindSucclistResponse()
        for i in range(len(self.successor_list)):
            resp.id_list.append(self.successor_list[i][0])
            resp.ip_list.append(self.successor_list[i][1])
        return resp

    def live_predecessor(self, request, context):
        return server_pb2.PredecessorResponse(ret = server_pb2.SUCCESS)

    # create a new Chord ring
    def create(self):
        self.predecessor = [None, None]
        self.successor_list[0] = [self.id, self.local_addr]

    # join a Chord ring containing node id
    def join(self, id, ip):
        pass

    # called periodically. verifies n's immediate successor, and tells the successor about n.
    def stabilize(self):
        print("Stabilize")
        threading.Timer(self.STABLE_PERIOD / 1000.0, self.stabilize).start()

    def notify(self, id, ip):
        pass

    # called periodically. refreshes finger table entries. next stores the index of the next finger to fix.
    def fix_finger(self):
        self.next = self.next + 1
        if self.next >= self.LOG_SIZE:
            self.next = 0
        try:
            find_request = server_pb2.FindSucRequest(id = (self.id + 1 << (self.next)))
            channel = grpc.insecure_channel(self.local_addr)
            stub = server_pb2_grpc.ServerStub(channel)
            find_resp = stub.find_successor(find_request)
            self.finger[self.next][0] = find_resp.id
            self.finger[self.next][1] = find_resp.ip
            print("Fix finger index ", self.next)
        except Exception:
            print("Can't fix finger index ", self.next)
        threading.Timer(self.FIXFINGER_PERIOD / 1000.0, self.fix_finger).start()

    # call periodically. checks whether predecessor has failed
    def check_predecessor(self):
        print("Check predecessor")
        if self.predecessor[1] != None:
            try:
                check_request = server_pb2.PredecessorRequest(id = self.id)
                channel = grpc.insecure_channel(self.predecessor[1])
                stub = server_pb2_grpc.ServerStub(channel)
                check_resp = stub.live_predecessor(check_request, timeout = 0.2)
                if check_resp.ret != server_pb2.SUCCESS:
                    self.predecessor[0] = None
                    self.predecessor[1] = None
            except Exception:
                self.predecessor[0] = None
                self.predecessor[1] = None
        threading.Timer(self.CHECKPRE_PERIOD / 1000.0, self.check_predecessor).start()

    def run(self):
        if self.remote_addr == None:
            self.create()
        else:
            self.join(self.id, self.remote_addr)
        # Call periodical functions
        self.stabilize()
        self.fix_finger()
        self.check_predecessor()

        

if __name__ == "__main__":
    virtual_node = Virtual_node("127.0.0.1:7000", None, 0)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    server_pb2_grpc.add_ServerServicer_to_server(virtual_node, server)
    server.add_insecure_port("127.0.0.1:7000")
    server.start()
    
    virtual_node.run()

    try:
        while True:
            time.sleep(24*60*60)
    except KeyboardInterrupt:
        server.stop(0)



