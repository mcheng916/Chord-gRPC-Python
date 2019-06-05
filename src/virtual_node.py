import json
import logging
import os
import threading
import hashlib 
from concurrent import futures
import time
import server_pb2_grpc
import server_pb2
import grpc
from threading import Condition


# This class represents a virtual node
class Virtual_node(server_pb2_grpc.ServerServicer):
    def __init__(self, id: int, local_addr, remote_addr, config):
        # Read configuration from json file
        # config = json.load(open("config.json"))
        self.LOG_SIZE = config["log_size"]
        self.SIZE = 1 << self.LOG_SIZE
        self.REP_NUM = config["replication_num"]
        self.SUCCESSOR_NUM = config["successor_num"]
        self.STABLE_PERIOD = config["stabilize_period"]
        self.FIXFINGER_PERIOD = config["fixfinger_period"]
        self.CHECKPRE_PERIOD = config["checkpre_period"]
        # print("LOG_SIZE:\t", self.LOG_SIZE, "\nSIZE:\t\t", self.SIZE, "\nREP_NUM:\t", self.REP_NUM)
        self.GLOBAL_TIMEOUT = 0.2
        self.JOIN_RETRY_PERIOD = 2

        self.local_addr = local_addr
        self.remote_addr = remote_addr
        # self.id = sha1(self.local_addr, self.SIZE)
        self.id = id

        # [server id, server IP]
        self.finger = [[-1, ""] for _ in range(self.LOG_SIZE)]
        self.successor_list = [[-1, ""] for _ in range(self.SUCCESSOR_NUM)]
        self.predecessor = [-1, ""]
        self.next = 0

        self.fix_finger_cond = Condition()
        self.check_pred_cond = Condition()
        self.stabilize_cond = Condition()

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
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        # create console handler with a higher log level
        # TODO: adjust level here
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def between(self, n1, n2, n3):
        if n1 < n3:
            return n1 < n2 < n3
        else:
            return n1 < n2 or n2 < n3

    def get_node_status(self, request, context):
        resp = server_pb2.NodeStatus()
        resp.id = self.id
        resp.ip = self.local_addr
        resp.pred_id = self.predecessor[0]
        resp.pred_ip = self.predecessor[1]
        for i in range(len(self.successor_list)):
            resp.suclist_id.append(self.successor_list[i][0])
            resp.suclist_ip.append(self.successor_list[i][1])
        for i in range(len(self.finger)):
            resp.finger_id.append(self.finger[i][0])
            resp.finger_ip.append(self.finger[i][1])
        return resp

    # search the local table for the highest predecessor of id
    def closest_preceding_node(self, id):
        i = self.LOG_SIZE - 1
        while i >= 0:
            # mcip: searching for predecessor such as for ex: between (40, 5)
            # if self.id < self.finger[i][0] < id or (self.finger[i][0] > self.id > id) or \
            #         (self.id > id > self.finger[i][0]):
            if self.finger[i][0] != -1 and self.between(self.id, self.finger[i][0], id) and self.id != id:
                return self.finger[i]
            i -= 1
        return [self.id, self.local_addr]

    # ask node n to find the successor of id
    def find_successor(self, request, context):
        # There is bug in paper algorithm, need to add boundary judgement
        if self.id == self.successor_list[0][0] or request.id == self.id:  # Only 1 node in ring
            return server_pb2.FindSucResponse(id=self.id, ip=self.local_addr)
        # if request.id > self.id and request.id <= self.successor_list[0][0]:
        #     return server_pb2.FindSucResponse(id = self.successor_list[0][0], ip = self.successor_list[0][1])
        # TODO: between logic might be incorrect
        if request.id == self.successor_list[0][0] or (self.between(self.id, request.id, self.successor_list[0][0]) and
                                                       self.id != self.successor_list[0][0]):
            return server_pb2.FindSucResponse(id=self.successor_list[0][0], ip=self.successor_list[0][1])
        # Recursively find the successor
        else:
            # Assume not all r successors fail simultaneously
            n_next = self.closest_preceding_node(request.id)
            find_request = server_pb2.FindSucRequest(id = request.id)
            channel = grpc.insecure_channel(n_next[1])
            stub = server_pb2_grpc.ServerStub(channel)
            find_resp = stub.find_successor(find_request)
            return server_pb2.FindSucResponse(id=find_resp.id, ip=find_resp.ip)  # TODO: might need to check this line

    def send_find_successor_request(self, id, ip):
        find_request = server_pb2.FindSucRequest(id=id)
        channel = grpc.insecure_channel(ip)
        stub = server_pb2_grpc.ServerStub(channel)
        find_resp = stub.find_successor(find_request)
        return [find_resp.id, find_resp.ip]

    # return the successor list
    def find_succlist(self, request, context):
        resp = server_pb2.FindSucclistResponse()
        # TODO: is this correct?
        # How to assign repeated field, https://stackoverflow.com/questions/23726335/how-to-assign-to-repeated-field
        for i in range(len(self.successor_list)):
            resp.id_list.append(self.successor_list[i][0])
            resp.ip_list.append(self.successor_list[i][1])
        return resp

    def live_predecessor(self, request, context):
        return server_pb2.PredecessorResponse(ret=server_pb2.SUCCESS)

    def find_predecessor(self, request, context):
        return server_pb2.FindPredResponse(id=self.predecessor[0], ip=self.predecessor[1])

    # create a new Chord ring
    def create(self):
        self.predecessor = [-1, ""]
        self.successor_list[0] = [self.id, self.local_addr]
        self.logger.debug(f"[Init]: First virtual node, id <{self.id}>, ip <{self.local_addr}>")

    # join a Chord ring containing node id
    def join(self, id, ip):
        while True:
            try:
                find_request = server_pb2.FindSucRequest(id=self.id)
                channel = grpc.insecure_channel(ip)
                stub = server_pb2_grpc.ServerStub(channel)
                find_resp = stub.find_successor(find_request, timeout=self.GLOBAL_TIMEOUT)
                newSucc = [find_resp.id, find_resp.ip]
                self.logger.debug(f'[Join]: Find successor to be id: <{find_resp.id}> ip: <{find_resp.ip}>')
                break
            except Exception as e:
                self.logger.error(f'[Join]: Failed to find successor at id: <{id}> ip: <{ip}>\nerror: <{e}>')
                time.sleep(self.JOIN_RETRY_PERIOD)
        while True:
            try:
                find_request = server_pb2.EmptyRequest()
                channel = grpc.insecure_channel(newSucc[1])
                stub = server_pb2_grpc.ServerStub(channel)
                find_resp = stub.find_succlist(find_request, timeout=self.GLOBAL_TIMEOUT)
                self.successor_list[0] = newSucc
                for i in range(len(find_resp.id_list) - 1):
                    self.successor_list[i+1][0] = find_resp.id_list[i]
                    self.successor_list[i+1][1] = find_resp.ip_list[i]
                self.logger.debug(f'[Join]: Successor list is added <{self.successor_list}>')
                self.predecessor = [-1, ""]
                with self.stabilize_cond:
                    self.stabilize_cond.notify()
                with self.fix_finger_cond:
                    self.fix_finger_cond.notify()
                break
            except Exception as e:
                self.logger.error(f'[Join]: Failed to find successor list at id:<{newSucc[0]}> ip: <{newSucc[1]}>'
                                  f'\nerror: <{e}>')
                time.sleep(self.JOIN_RETRY_PERIOD)

    # Verifies n's immediate successor, and tells the successor about n. called periodically.
    # It would call
    def stabilize(self):
        with self.stabilize_cond:
            self.stabilize_cond.wait()
        while True:
            self.logger.debug("[Stabilize]: started")
            # while len(self.successor_list) > 0:  # the length of the list is always > 0
            try:
                # TODO: how to start fix finger
                # check if there was no successor initially for starting fix_finger
                suc_is_itself = (self.successor_list[0] == self.id)
                # Query its successor for its predecessor and successor list
                empty_request = server_pb2.EmptyRequest()
                channel = grpc.insecure_channel(self.successor_list[0][1])
                stub = server_pb2_grpc.ServerStub(channel)
                pred_resp = stub.find_predecessor(empty_request, timeout=self.GLOBAL_TIMEOUT)
                succlist_resp = stub.find_succlist(empty_request, timeout=self.GLOBAL_TIMEOUT)
                # Successor's predecessor is a possible next successor
                possible_succ = [pred_resp.id, pred_resp.ip]
                # TODO: how to deal with response correctly
                self.successor_list = [[succlist_resp.id_list[0], succlist_resp.ip_list[0]]]
                empty_request2 = server_pb2.EmptyRequest()
                channel2 = grpc.insecure_channel(self.successor_list[0][1])
                stub2 = server_pb2_grpc.ServerStub(channel2)
                succlist_resp2 = stub2.find_succlist(empty_request2, timeout=self.GLOBAL_TIMEOUT)
                for i in range(len(succlist_resp2.id_list)-1):
                    self.successor_list += [[succlist_resp2.id_list[i], succlist_resp2.ip_list[i]]]
                if self.between(self.id, possible_succ[0], self.successor_list[0][0]):
                    try:
                        empty_request3 = server_pb2.EmptyRequest()
                        channel3 = grpc.insecure_channel(possible_succ[1])
                        stub3 = server_pb2_grpc.ServerStub(channel3)
                        succlist_resp3 = stub3.find_succlist(empty_request3, timeout=self.GLOBAL_TIMEOUT)
                        self.successor_list = [[possible_succ]]
                        for i in range(len(succlist_resp3.id_list)-1):
                            self.successor_list += [[succlist_resp3.id_list[i], succlist_resp3.ip_list[i]]]
                        self.logger.debug(f'[Stabilize]: Successor is now previous successors pred, successor list:'
                                          f' <{self.successor_list}>')
                    except Exception as e:
                        self.logger.error(f'[Stabilize]: previous successors pred is queried but failed\n <{e}>')
                else:
                    self.logger.debug(f'[Stabilize]: Successor list might be the same: <{self.successor_list}>')
                # if there was no successor and now there is, fix_finger can start
                if suc_is_itself:
                    with self.fix_finger_cond:
                        self.fix_finger_cond.notify()
                try:
                    # Notify the head
                    rectify_request = server_pb2.RectifyRequest(id=self.id, ip=self.local_addr)
                    channel4 = grpc.insecure_channel(self.successor_list[0][1])
                    stub4 = server_pb2_grpc.ServerStub(channel4)
                    stub4.rectify(rectify_request, timeout=self.GLOBAL_TIMEOUT)
                except Exception as e:
                    self.logger.error(f'[Stabilize]: rectify request failed')
                break
            except Exception as e:
                # TODO: need to deal with shrinking successor list?
                self.successor_list = self.successor_list[1:]
                self.logger.error(f'[Stabilize]: no response for first successor check, \nerror: <{e}>')
        # threading.Timer(self.STABLE_PERIOD / 1000.0, self.stabilize).start()

    # rectify establishes predecessor correctly, it is called upon stabilization
    def rectify(self, request, context):
        # self.logger.debug(f'[Rectify]: request is: id <{request.id}> ip <{request.ip}>')
        if self.predecessor[0] == -1:
            self.predecessor = [request.id, request.ip]
            self.logger.debug(f'[Rectify]: Predecessor is now id: <{request.id}> ip: <{request.ip}> due to no pred')
        else:
            try:  # query pred to see if live
                check_request = server_pb2.PredecessorRequest(id=self.id)
                channel = grpc.insecure_channel(self.predecessor[1])
                stub = server_pb2_grpc.ServerStub(channel)
                stub.live_predecessor(check_request, timeout=self.GLOBAL_TIMEOUT)
                if self.between(self.predecessor[0], request.id, self.id):
                    self.predecessor = [request.id, request.ip]
                    self.logger.debug(f'[Rectify]: Predecessor is now id: <{request.id}> ip: <{request.ip}> '
                                      f'since new pred proposal is between')
            except Exception as e:
                self.predecessor = [request.id , request.ip]
                self.logger.debug(f'[Rectify]: Predecessor is now id: <{request.id}> ip: <{request.ip}> since its pred'
                                  f' is not live')
        return server_pb2_grpc.EmptyResponse()

    # Refreshes finger table entries. next stores the index of the next finger to fix. Called periodically.
    def fix_finger(self):
        self.logger.debug(f"[Finger]: successor list: <{self.successor_list}>, id: <{self.id}>")
        if self.successor_list[0] == self.id:
            self.logger.debug("[Finger]: current successor is itself, wait to be notified")
            with self.fix_finger_cond:
                self.fix_finger_cond.wait()
        while True:
            try:
                self.finger[self.next] = self.send_find_successor_request(self.id + 1 << self.next, self.local_addr)
                self.logger.debug(f"[Finger]: Fix finger index: <{self.next}>, suc list length: <{len(self.successor_list)}>")
                self.next = (self.next + 1) % self.LOG_SIZE
                if self.successor_list[self.next][0] == -1:  # there is no successor at this place, set to 0
                    self.next = 0
            except Exception as e:
                self.logger.error(f"[Finger]: Can't fix finger index: <{self.next}>\nerror: <{e}>")
            with self.fix_finger_cond:
                self.fix_finger_cond.wait(self.FIXFINGER_PERIOD / 1000.0)
        # threading.Timer(self.FIXFINGER_PERIOD / 1000.0, self.fix_finger).start()

    # call periodically. checks whether predecessor has failed
    # TODO: this function can be fully replaced by rectify?
    def check_predecessor(self):
        while True:
            self.logger.debug("[Check pred]")
            try:
                check_request = server_pb2.PredecessorRequest(id=self.id)
                channel = grpc.insecure_channel(self.predecessor[1])
                stub = server_pb2_grpc.ServerStub(channel)
                check_resp = stub.live_predecessor(check_request, timeout=self.GLOBAL_TIMEOUT)
                if check_resp.ret != server_pb2.SUCCESS:
                    self.predecessor = [-1, ""]
            except Exception as e:
                self.predecessor = [-1, ""]
            with self.check_pred_cond:
                self.check_pred_cond.wait(self.CHECKPRE_PERIOD / 1000.0)

    def replicate_entries(self, request, context):
        pass

    def send_replicate_entries(self, req):
        for suc in self.successor_list:
            send_thread = threading.Thread(target=thread_send_replicate, args=(suc[0], suc[1], req,))
            send_thread.start()

    def thread_send_replicate(self, id, ip, req):
        try:
            while True:
                channel = grpc.insecure_channel(ip)
                grpc.channel_ready_future(channel).result()
                stub = server_pb2_grpc.ServerStub(channel)
                replicate_resp = stub.replicate_entries(req, timeout=self.GLOBAL_TIMEOUT)
                if not replicate_resp.SUCCESS:
                    with self.stabilize_cond:
                        self.stabilize_cond.notify()
                else:
                    return
        except Exception as e:
            pass

    def run(self):
        # self.logger.debug(f"[Init]: Start virtual node, id is: <{self.id}>")
        stabilize_th = threading.Thread(target=self.stabilize, args=())
        stabilize_th.start()
        fix_finger_th = threading.Thread(target=self.fix_finger, args=())
        fix_finger_th.start()
        if self.remote_addr == self.local_addr:
            self.create()
            # self.logger.debug(f"[Init]: New Chord Ring with vn, id: <{self.id}>, ip: <{self.ip}>")
        else:
            self.join(self.id, self.remote_addr)
        # Call periodical functions
        # TODO: this function can be fully replaced by rectify?
        # check_pred_th = threading.Thread(target=self.check_predecessor, args=())
        # check_pred_th.start()

    def sha1(key, size):
        return int(hashlib.sha1(key.encode()).hexdigest(), 16) % size

# def start_virtual_node(localAddr, remoteAddr):
#     virtual_node = Virtual_node(localAddr, remoteAddr)
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
#     server_pb2_grpc.add_ServerServicer_to_server(virtual_node, server)
#     server.add_insecure_port(localAddr)
#     server.start()
#     virtual_node.run()
#     try:
#         while True:
#             time.sleep(24*60*60)
#     except KeyboardInterrupt:
#         server.stop(0)

# if __name__ == "__main__":
#     threading.Thread(target=start_virtual_node, args=("127.0.0.1:7000", None)).start()
#     threading.Thread(target=start_virtual_node, args=("127.0.0.1:7001", "127.0.0.1:7000")).start()
#     # threading.Thread(target=start_virtual_node, args=("127.0.0.1:7002", "127.0.0.1:7000")).start()
#     # threading.Thread(target=start_virtual_node, args=("127.0.0.1:7003", "127.0.0.1:7000")).start()
#     # threading.Thread(target=start_virtual_node, args=("127.0.0.1:7004", "127.0.0.1:7000")).start()

    



