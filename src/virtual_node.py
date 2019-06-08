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
from threading import Lock


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
        self.GLOBAL_TIMEOUT = 1
        self.JOIN_RETRY_PERIOD = 2

        self.local_addr = local_addr
        self.remote_addr = remote_addr
        # self.id = sha1(self.local_addr, self.SIZE)
        self.id = id
        self.only_node_phase = -1
        self.second_node = False

        # [server id, server IP]
        self.finger = [[-1, ""] for _ in range(self.LOG_SIZE)]
        self.successor_list = [[-1, ""] for _ in range(self.SUCCESSOR_NUM)]
        self.predecessor = [-1, ""]
        self.next = 0

        self.fix_finger_notified = False
        self.rectify_cond = Condition()
        self.fix_finger_cond = Condition()
        self.check_pred_cond = Condition()
        self.stabilize_cond = Condition()
        self.successor_list_lock = Lock()

        self.state_machine = {}
        self.logs = []

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
        # TODO: added corner case when id == -1
        if n2 == -1:
            return False
        if n1 == -1:
            return True
        # Since it's a circle if n1=n3 then n2 is between
        if n1 == n3:
            return True
        # if n1 < n3:
        #     return n1 < n2 < n3
        # else:
        #     return n1 < n2 or n2 < n3
        n2 = (n2-n1) % (1 << self.LOG_SIZE)
        n3 = (n3-n1) % (1 << self.LOG_SIZE)
        return 0 < n2 < n3

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
        res = [self.id, self.local_addr]
        while i >= 0:
            # mcip: searching for predecessor such as for ex: between (40, 5)
            # if self.id < self.finger[i][0] < id or (self.finger[i][0] > self.id > id) or \
            #         (self.id > id > self.finger[i][0]):
            # if self.finger[i][0] != -1 and self.between(self.id, self.finger[i][0], id) and self.id != id:
            if self.between(self.id, self.finger[i][0], id):
                res = self.finger[i]
                break
            i -= 1
        i = len(self.successor_list) - 1
        while i >= 0:
            if self.between(res[0], self.successor_list[i][0], id):
                res = self.successor_list[i]
                break
        # self.logger.debug(f'[Closest_pred]: for id <{id}> is <{res[0]}>')
        return res

    # ask node n to find the successor of id
    def find_successor(self, request, context):
        # There is bug in paper algorithm, need to add boundary judgement
        # if self.id == self.successor_list[0][0] or request.id == self.id:  # Only 1 node in ring
        #     return server_pb2.FindSucResponse(id=self.id, ip=self.local_addr)
        # if request.id > self.id and request.id <= self.successor_list[0][0]:
        #     return server_pb2.FindSucResponse(id = self.successor_list[0][0], ip = self.successor_list[0][1])

        # if request.id == self.successor_list[0][0] or (self.between(self.id, request.id, self.successor_list[0][0])
        # and self.id != self.successor_list[0][0]):
        # TODO this has to be done after we find its real successor
        # to_compare = self.successor_list[0]
        # self.logger.debug(f"[Find_suc]: <{request.id}> <{to_compare[0]}> <{self.between(self.id, request.id, to_compare[0])}>")
        # threading.Thread(target=self.update_succlist_w_req, args=(request.inc_id, request.inc_ip,)).start()'
        # if request.id == to_compare[0] or self.between(self.id, request.id, to_compare[0]):
        #     self.logger.debug(f'[Receive f[Join]: self id:ind_suc req]: found successor for req id: <{request.id}>, its id: '
        #                       f'<{to_compare[0]}>')
        #     response = server_pb2.FindSucResponse(id=to_compare[0], ip=to_compare[1])
        # TODO: when the request is itself's first successor
        # self.logger.debug(f'[Receive find_suc req]: received request, <{request.id}>, <{request.inc_id}>, <{request.inc_ip}>')
        if request.id == -1:
            self.logger.debug(f'[First node]: Special request, successor will be itself')
            return server_pb2.FindSucResponse(id=self.id, ip=self.local_addr)
        elif request.id == self.successor_list[0][0] or self.between(self.id, request.id, self.successor_list[0][0]):
            self.logger.debug(f'[Receive find_suc req]: successor for id: <{request.id}> is id: '
                              f'<{self.successor_list[0][0]}>')
            response = server_pb2.FindSucResponse(id=self.successor_list[0][0], ip=self.successor_list[0][1])
            if self.only_node_phase == 0:
                self.only_node_phase = 1
                self.logger.debug(f'[First node]: Joining 2nd node <{request.inc_id}>, ip: <{request.inc_ip}>')
                threading.Thread(target=self.join, args=(self.id, request.inc_ip,)).start()
                # self.join(self.id, request.inc_ip)
            return response
        # Recursively find the successor
        else:
            # Assume not all r successors fail simultaneously
            # self.logger.debug(f'[Receive find_suc req]: !!!!!')
            n_next = self.closest_preceding_node(request.id)
            # self.logger.debug(f'[Receive find_suc req]: closest pred: <{n_next[0]}>')
            possible_succ = self.init_find_successor(request.id, n_next[1])
            self.logger.debug(f'[Receive find_suc req]: Query closest pred, id: <{n_next[0]}>, for id: <{request.id}>')
            return server_pb2.FindSucResponse(id=possible_succ[0], ip=possible_succ[1])  # TODO: might need to check this line

    def update_succlist_w_req(self, id, ip):
        self.successor_list_lock.acquire()
        if id == self.id:
            pass
        elif self.id == self.successor_list[0][0]:
            self.successor_list[0] = [id, ip]
            self.logger.debug(f'[Update succ_list]: c1 <{self.successor_list}>')
        elif self.successor_list[-1][0] == -1:
            for idx, suc in enumerate(self.successor_list):
                if suc[0] == id:
                    break
                elif suc[0] == -1:
                    self.successor_list[idx] = [id, ip]
                    self.logger.debug(f'[Update succ_list]: c2 <{self.successor_list}>')
                    break
                elif self.between(self.id, id, suc[0]):
                    # self.logger.debug(f'[Update succ_list]: length <{idx}> <{self.successor_list[:idx]}> '
                    #                   f'<{[[id, ip]]}> <{self.successor_list[idx+1:-1]}>')
                    self.successor_list = self.successor_list[:idx]+[[id, ip]]+self.successor_list[idx+1:-1]
                    self.logger.debug(f'[Update succ_list]: c3 <{self.successor_list}>')
                    break
        elif self.between(self.id, id, self.successor_list[-1][0]):
            for idx, suc in enumerate(self.successor_list):
                if suc[0] == id:
                    break
                elif self.between(self.id, id, suc[0]):
                    # self.logger.debug(f'[Update succ_list]: length <{idx}> <{self.successor_list[:idx]}> '
                    #                   f'<{[[id, ip]]}> <{self.successor_list[idx+1:-1]}>')
                    self.successor_list = self.successor_list[:idx]+[[id, ip]]+self.successor_list[idx+1:-1]
                    self.logger.debug(f'[Update succ_list]: c4 <{self.successor_list}>')
                    break
        self.successor_list_lock.release()

    # ask node n to find the successor of id
    def init_find_successor(self, id, ip):
        # TODO: find successor for first node return the predecessor???
        # Also need to cover the case where it's the first node in the ring
        self.logger.debug(f'[Init find suc]: query for <{id}>, channel <{ip}>, incoming id <{self.id}>, incoming ip <{self.local_addr}>')
        find_request = server_pb2.FindSucRequest(id=id, inc_id=self.id, inc_ip=self.local_addr)
        # self.logger.debug(f'[Init find suc]: 1111')
        if self.only_node_phase == 1:
            self.only_node_phase = 2
            find_request.id = -1
            self.logger.debug(f'[First node]: find_request <{self.id}> is -1???')
        elif self.id == self.successor_list[0][0]:
            self.logger.debug(f'[First node]: successor_list[0] <{self.successor_list[0]}>')
            return self.successor_list[0]
        channel = grpc.insecure_channel(ip)
        # self.logger.debug(f'[Init find suc]: 3333')
        # grpc.channel_ready_future(channel).result()
        stub = server_pb2_grpc.ServerStub(channel)
        # self.logger.debug(f'[Init find suc]: 4444')
        find_resp = stub.find_successor(find_request, timeout=self.GLOBAL_TIMEOUT)
        # self.logger.debug(f'[Init find suc]: 5555')
        # self.logger.debug(f"[init_find_suc]: lookup id: <{find_request.id}>, ip: <{ip}>")
        self.logger.debug(f"[init_find_suc]: lookup id: <{find_request.id}>, found id: <{find_resp.id}>")
        return [find_resp.id, find_resp.ip]
        # find_request = server_pb2.FindSucRequest(id=self.id)
        # channel = grpc.insecure_channel(ip)
        # stub = server_pb2_grpc.ServerStub(channel)
        # find_resp = stub.find_successor(find_request, timeout=self.GLOBAL_TIMEOUT)
        # newSucc = [find_resp.id, find_resp.ip]

    # return the successor list
    def find_succlist(self, request, context):
        # threading.Thread(target=self.update_succlist_w_req, args=(request.inc_id, request.inc_ip,)).start()
        resp = server_pb2.FindSucclistResponse()
        # TODO: is this correct?
        # How to assign repeated field, https://stackoverflow.com/questions/23726335/how-to-assign-to-repeated-field
        for i in range(len(self.successor_list)):
            resp.id_list.append(self.successor_list[i][0])
            resp.ip_list.append(self.successor_list[i][1])
        return resp

    def init_find_successorlist(self, id, ip, need_pred):
        find_sl_request = server_pb2.FindSucclistRequest(inc_id=self.id, inc_ip=self.local_addr)
        channel = grpc.insecure_channel(ip)
        # grpc.channel_ready_future(channel).result()
        stub = server_pb2_grpc.ServerStub(channel)
        pred_resp = 0
        if need_pred:
            empty_request = server_pb2.EmptyRequest()
            pred_resp = stub.find_predecessor(empty_request, timeout=self.GLOBAL_TIMEOUT)
        find_sl_resp = stub.find_succlist(find_sl_request, timeout=self.GLOBAL_TIMEOUT)
        return find_sl_resp, pred_resp

    def live_predecessor(self, request, context):
        return server_pb2.PredecessorResponse(ret=server_pb2.SUCCESS)

    def find_predecessor(self, request, context):
        return server_pb2.FindPredResponse(id=self.predecessor[0], ip=self.predecessor[1])

    # create a new Chord ring
    def create(self):
        self.only_node_phase = 0
        self.predecessor = [-1, ""]
        self.successor_list[0] = [self.id, self.local_addr]
        self.logger.debug(f"[Create]: Create chord ring, 1st vn id: <{self.id}>, ip: <{self.local_addr}>")

    # join a Chord ring containing node id
    def join(self, id, ip):
        while True:
            try:
                # TODO: add 1 into the id is correct???
                newSucc = self.init_find_successor(self.id, ip)
                # self.logger.debug(f'<{self.id}>, <{ip}>')
                self.logger.debug(f'[Join]: self id: <{self.id}> found successor id: <{newSucc[0]}> ip: <{newSucc[1]}>')
                break
            except Exception as e:
                self.logger.error(f'[Join]: Failed finding successor for id: <{id}> ip: <{ip}>\nerror: <{e}>')
                time.sleep(self.JOIN_RETRY_PERIOD)
        while True:
            try:
                # find_request = server_pb2.EmptyRequest()
                # channel = grpc.insecure_channel(newSucc[1])
                # stub = server_pb2_grpc.ServerStub(channel)
                # find_resp = stub.find_succlist(find_request, timeout=self.GLOBAL_TIMEOUT)
                find_sl_resp, _ = self.init_find_successorlist(newSucc[0], newSucc[1], False)
                # self.logger.debug(f"<[Join]: find_sl_resp: {find_sl_resp}>")
                self.append_but_last(newSucc, find_sl_resp)
                self.predecessor = [-1, ""]
                self.logger.debug(f'[Join]: Suc list now: <{self.successor_list}>')
                with self.stabilize_cond:
                    self.stabilize_cond.notify()
                break
            except Exception as e:
                self.logger.error(f'[Join]: Failed finding succ list for id:<{newSucc[0]}> ip: <{newSucc[1]}>'
                                  f'\nerror: <{e}>')
                time.sleep(self.JOIN_RETRY_PERIOD)

    # Deal with following case
    # succList = append(newSucc, butLast(newSucc.succList));
    # Suc list now: <[[0, 'localhost:7000'], [-1, ''], [-1, ''], [-1, ''], [-1, '']]>
    # Succ_list maintains: <[[6, 'localhost:7001'], [0, 'localhost:7000'], [-1, ''], [-1, ''], [-1, '']]>
    def append_but_last(self, head, response):

        self.successor_list_lock.acquire()
        self.successor_list = [head]
        for idx in range(len(response.id_list)-1):
            # TODO: if successor is itself or already exists in successor list, then set it to -1???
            if response.id_list[idx] == -1 or response.id_list[idx] == self.id or \
                    response.id_list[idx] == self.successor_list[0][0]:
                break
            self.successor_list += [[response.id_list[idx], response.ip_list[idx]]]
        # self.logger.debug(f'[Append_but_last]: <{head}> <{response.id_list}> <{idx}> <{n}>')
        self.successor_list += [[-1, ""]]*(self.SUCCESSOR_NUM-len(self.successor_list))
        # self.successor_list[0] = head
        # count = 0
        # idx = 1
        # for i in range(len(response.id_list) - 1):
        #     # TODO: if successor is itself or already exists in successor list, then set it to -1???
        #     if response.id_list[i] == self.id or response.id_list[i] == self.successor_list[0][0]:
        #         count += 1
        #     else:
        #         self.successor_list[idx] = [response.id_list[i], response.ip_list[i]]
        #         idx += 1
        # self.successor_list += [[-1, ""]]*count
        self.successor_list_lock.release()
        # self.logger.debug(f'[Append_but_last]: <{self.successor_list}>')

    # Verifies n's immediate successor, and tells the successor about n. called periodically.
    # Upon finishing, call rectify on the successor
    def stabilize(self):
        with self.stabilize_cond:
            self.logger.debug("[Stabilize]: wait to be notified")
            self.stabilize_cond.wait()
        while True:
            # self.logger.debug("[Stabilize]: notified")
            # while len(self.successor_list) > 0:  # the length of the list is always > 0
            try:
                # TODO: how to start fix finger
                # check if there was no successor initially for starting fix_finger
                # Query its successor for its predecessor and successor list
                # empty_request = server_pb2.EmptyRequest()
                # channel = grpc.insecure_channel(self.successor_list[0][1])
                # stub = server_pb2_grpc.ServerStub(channel)
                # pred_resp = stub.find_predecessor(empty_request, timeout=self.GLOBAL_TIMEOUT)
                # succlist_resp = stub.find_succlist(empty_request, timeout=self.GLOBAL_TIMEOUT)
                find_sl_resp1, pred_resp = self.init_find_successorlist(self.successor_list[0][0], self.successor_list[0][1], True)
                # Successor's predecessor is a possible next successor
                possible_succ = [pred_resp.id, pred_resp.ip]
                # TODO: how to deal with response correctly
                # self.successor_list = [[succlist_resp.id_list[0], succlist_resp.ip_list[0]]]
                # empty_request2 = server_pb2.EmptyRequest()
                # channel2 = grpc.insecure_channel(find_sl_resp1.ip_list[0])
                # stub2 = server_pb2_grpc.ServerStub(channel2)
                # find_sl_resp2 = stub2.find_succlist(empty_request2, timeout=self.GLOBAL_TIMEOUT)
                # find_sl_resp2, _ = self.init_find_successorlist(find_sl_resp1.id_list[0], find_sl_resp1.ip_list[0], False)
                self.append_but_last(self.successor_list[0], find_sl_resp1)
                if self.between(self.id, possible_succ[0], self.successor_list[0][0]):
                    try:
                        # empty_request3 = server_pb2.EmptyRequest()
                        # channel3 = grpc.insecure_channel(possible_succ[1])
                        # stub3 = server_pb2_grpc.ServerStub(channel3)
                        # succlist_resp3 = stub3.find_succlist(empty_request3, timeout=self.GLOBAL_TIMEOUT)
                        find_sl_resp3, _ = self.init_find_successorlist(possible_succ[0], possible_succ[1], False)
                        self.append_but_last(possible_succ, find_sl_resp3)
                        self.logger.debug(f'[Stabilize]: succ is succ pred, succ list: '
                                          f'<{self.successor_list}>, btw <{self.id}> <{possible_succ[0]}> '
                                          f'<{self.successor_list[0][0]}>')
                    except Exception as e:
                        self.logger.error(f'[Stabilize]: prev succ pred <{possible_succ}> query failed\nerror: <{e}>')
                else:
                    self.logger.debug(f'[Stabilize]: Succ_list maintains: <{self.successor_list}>')
                try:
                    # Notify the head
                    with self.rectify_cond:
                        self.rectify_cond.notify()
                    # if there was no successor and now there is, fix_finger can start
                    if not self.fix_finger_notified:
                        self.fix_finger_notified = True
                        with self.fix_finger_cond:
                            self.fix_finger_cond.notify()
                except Exception as e:
                    self.logger.error(f'[Stabilize]: rectify req failed\nerror: <{e}>')
            except Exception as e:
                # TODO: need to deal with shrinking successor list?
                self.logger.error(f'[Stabilize]: no response for first successor check, '
                                  f'\nerror: <{e}>')
                self.logger.debug(f'[Stabilize]: {self.successor_list[0][0]}, {self.successor_list[0][1]}')
                self.successor_list = self.successor_list[1:] + [[-1, ""]]
            with self.stabilize_cond:
                # self.logger.debug(f'[Stabilize]: now wait?')
                self.stabilize_cond.wait(self.STABLE_PERIOD / 1000.0)
        # threading.Timer(self.STABLE_PERIOD / 1000.0, self.stabilize).start()

    def init_rectify(self):
        while True:
            with self.rectify_cond:
                self.rectify_cond.wait()
            rectify_request = server_pb2.RectifyRequest(id=self.id, ip=self.local_addr)
            channel4 = grpc.insecure_channel(self.successor_list[0][1])
            # grpc.channel_ready_future(channel4).result()
            stub4 = server_pb2_grpc.ServerStub(channel4)
            rectify_resp = stub4.rectify(rectify_request, timeout=self.GLOBAL_TIMEOUT)
            if rectify_resp.ret == server_pb2.SUCCESS:
                self.logger.debug(f'[Rectify]: rectified <{self.successor_list[0][0]}> with <{self.id}>')

    # rectify establishes predecessor correctly, it is called upon stabilization
    def rectify(self, request, context):
        self.logger.debug(f'[Rectify]: request is: id <{request.id}> ip <{request.ip}>')
        if self.predecessor[0] == -1:
            self.predecessor = [request.id, request.ip]
            self.logger.debug(f'[Rectify]: Pred is now id: <{request.id}> ip: <{request.ip}>, no pred')
            # TODO: wake up the threads in initial node of chord ring here???
            # if self.id == self.successor_list[0][0]:
            #     with self.stabilize_cond:
            #         self.stabilize_cond.notify()
        else:
            try:  # query pred to see if live
                check_request = server_pb2.PredecessorRequest(id=self.id)
                channel = grpc.insecure_channel(self.predecessor[1])
                # grpc.channel_ready_future(channel).result()
                stub = server_pb2_grpc.ServerStub(channel)
                resp = stub.live_predecessor(check_request, timeout=self.GLOBAL_TIMEOUT)
                if resp.ret == server_pb2.SUCCESS and self.between(self.predecessor[0], request.id, self.id):
                    self.predecessor = [request.id, request.ip]

                    # self.logger.debug(f'[Rectify]: Predecessor is now id: <{request.id}> ip: <{request.ip}>, between '
                    #                   f'<{self.predecessor[0]}> <{request.id}> <{self.id}>?????')
                else:
                    self.predecessor = [request.id, request.ip]
            except Exception as e:
                self.predecessor = [request.id, request.ip]
                self.logger.debug(f'[Rectify]: Predecessor is now id: <{request.id}> ip: <{request.ip}>, old dead'
                                  f'\nerror: <{e}>')
        return server_pb2.RectifyResponse(ret=server_pb2.SUCCESS)

    # Refreshes finger table entries. next stores the index of the next finger to fix. Called periodically.
    def fix_finger(self):
        # if self.successor_list[0][0] == self.id or self.successor_list[0][0] == -1:
        #     self.logger.debug(f"[Finger]: Successor is <{self.successor_list[0][0]}>, wait to be notified")
        #     with self.fix_finger_cond:
        #         self.fix_finger_cond.wait()
        with self.fix_finger_cond:
            self.fix_finger_cond.wait()
        self.logger.debug("[Finger]: started")
        while True:
            try:
                self.finger[self.next] = self.init_find_successor((self.id + (1 << self.next)) % (1 << self.LOG_SIZE),
                                                                  self.local_addr)
                # self.logger.debug(f"<{self.id}>, <{self.id + (1 << self.next)}>, <{self.LOG_SIZE}>, "
                #                   f"<{(1 << self.LOG_SIZE)}> "
                #                   f"<{(self.id + (1 << self.next)) % (1 << self.LOG_SIZE)}>")
                self.logger.debug(f"[Finger]: fix_next: <{self.next}>, id: "
                                  f"<{(self.id + (1 << self.next)) % (1 << self.LOG_SIZE)}>, "
                                  f"finger_table: <{self.finger}>")
                self.next = (self.next + 1) % self.LOG_SIZE
                # if self.successor_list[self.next][0] == -1:  # there is no successor at this place, set to 0
                #     self.next = 0
            except Exception as e:
                self.logger.error(f"[Finger]: Failed at fix_next: <{self.next}>\nerror: <{e}>")
            with self.fix_finger_cond:
                self.fix_finger_cond.wait(self.FIXFINGER_PERIOD / 1000.0)
        # threading.Timer(self.FIXFINGER_PERIOD / 1000.0, self.fix_finger).start()

    # Checks whether predecessor has failed, call periodically
    # TODO: this function can be fully replaced by rectify?
    def check_predecessor(self):
        while True:
            # self.logger.debug("[Check pred]")
            try:
                check_request = server_pb2.PredecessorRequest(id=self.id)
                channel = grpc.insecure_channel(self.predecessor[1])
                # grpc.channel_ready_future(channel).result()
                stub = server_pb2_grpc.ServerStub(channel)
                check_resp = stub.live_predecessor(check_request, timeout=self.GLOBAL_TIMEOUT)
                if check_resp.ret != server_pb2.SUCCESS:
                    self.predecessor = [-1, ""]
            except Exception:
                self.predecessor = [-1, ""]
            with self.check_pred_cond:
                self.check_pred_cond.wait(self.CHECKPRE_PERIOD / 1000.0)

    def replicate_entries(self, request, context):
        pass

    def thread_send_replicate(self, id, ip, req):
        try:
            while True:
                # TODO: this need to be done
                # check_request = server_pb2.ReplicateRequest
                channel = grpc.insecure_channel(ip)
                # grpc.channel_ready_future(channel).result()
                stub = server_pb2_grpc.ServerStub(channel)
                replicate_resp = stub.replicate_entries(req, timeout=self.GLOBAL_TIMEOUT)
                if not replicate_resp.SUCCESS:
                    with self.stabilize_cond:
                        self.stabilize_cond.notify()
                else:
                    return
        except Exception:
            pass

    def send_replicate_entries(self, req):
        for suc in self.successor_list:
            send_thread = threading.Thread(target=self.thread_send_replicate, args=(suc[0], suc[1], req,))
            send_thread.start()

    def get(self, request, context):
        get_resp = server_pb2.GetResponse()
        hash_val = self.sha1(request.key, self.SIZE)
        if not self.between(self.predecessor[0], hash_val, self.id):
            find_suc_resp = self.init_find_successor(hash_val, self.successor_list[0][1])
            get_resp.ret = server_pb2.FAILURE
            get_resp.response = ""
            get_resp.nodeID = find_suc_resp.id
            get_resp.nodeIP = find_suc_resp.ip
        else:
            try:
                get_resp.ret = server_pb2.SUCCESS
                get_resp.response = self.state_machine[request.key]
                get_resp.nodeID = -1
                get_resp.nodeIP = ""
            except KeyError:
                get_resp.ret = server_pb2.FAILURE
                get_resp.response = "N/A"
                get_resp.nodeID = -1
                get_resp.nodeIP = ""
        return get_resp

    def put(self, request, context):
        put_resp = server_pb2.PutResponse()
        hash_val = self.sha1(request.key, self.SIZE)
        if not self.between(self.predecessor[0], hash_val, self.id):
            find_suc_resp = self.init_find_successor(hash_val, self.successor_list[0][1])
            put_resp.ret = server_pb2.FAILURE
            put_resp.nodeID = find_suc_resp.id
            put_resp.nodeIP = find_suc_resp.ip
        else:
            self.logs += [[request.key, request.value]]
            self.state_machine[request.key] = request.value
            put_resp.ret = server_pb2.SUCCESS
            put_resp.nodeID = -1
            put_resp.nodeIP = ""

        return put_resp

    def run(self):
        # self.logger.debug(f"[Init]: Start virtual node, id is: <{self.id}>")
        if self.remote_addr == self.local_addr:
            self.create()
            # self.logger.debug(f"[Init]: New Chord Ring with vn, id: <{self.id}>, ip: <{self.ip}>")
        stabilize_th = threading.Thread(target=self.stabilize, args=())
        stabilize_th.start()
        fix_finger_th = threading.Thread(target=self.fix_finger, args=())
        fix_finger_th.start()
        threading.Thread(target=self.init_rectify, args=()).start()
        if self.local_addr != self.remote_addr:
            self.join(self.id, self.remote_addr)
        # Call periodical functions
        # TODO: this function can be fully replaced by rectify?
        # check_pred_th = threading.Thread(target=self.check_predecessor, args=())
        # check_pred_th.start()

    def sha1(self, key, size):
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

    



