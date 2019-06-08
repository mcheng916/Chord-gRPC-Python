import server_pb2_grpc
import server_pb2
import grpc
import time

def getNodeStatus(addr):
    find_request = server_pb2.EmptyRequest()
    channel = grpc.insecure_channel(addr)
    stub = server_pb2_grpc.ServerStub(channel)
    find_resp = stub.get_node_status(find_request)
    print("id:\t", find_resp.id)
    print("ip:\t", find_resp.ip)
    print("pred_id:\t", find_resp.pred_id)
    print("pred_ip:\t", find_resp.pred_ip)
    print("suclist:")
    for i in range(len(find_resp.suclist_id)):
        print(find_resp.suclist_id[i], find_resp.suclist_ip[i])
    print("finger table:")
    for i in range(len(find_resp.finger_id)):
        print(find_resp.finger_id[i], find_resp.finger_ip[i])

def run(Addr):
    start = time.time()

    # TODO: Implement PUT and GET
    myKey = "1"*1024
    myValue = "1"*1024
    start = time.time()
    seq_num = 1

    for _ in range(100):
        try:
            while True:
                channel = grpc.insecure_channel(Addr)
                stub = server_pb2_grpc.ServerStub(channel)
                # print("Try to put")
                stub.put(server_pb2.PutRequest(key = myKey, value = myValue))
        except Exception as e:
            print(e)
        seq_num += 1


    print(time.time() - start)

    start = time.time()
    try:
        while True:
            channel = grpc.insecure_channel(Addr)
            stub = server_pb2_grpc.ServerStub(channel)
            print("Try to get")
            stub.get(server_pb2.GetRequest(key = myKey))
    except Exception as e:
        print(e)
    print(time.time() - start)

    #
    # with grpc.insecure_channel(address) as channel:
    #     stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
    #     # print("Try to put")
    #     response = stub.Put(kvstore_pb2.PutRequest(key = "1", value = "100"))
    #     print("Client PUT received: " + str(response.ret))
    #
    #
    #     response = stub.Get(kvstore_pb2.GetRequest(key = "1"))
    #     print("Client GET received: " + str(response.value))

if __name__ == "__main__":
    getNodeStatus("127.0.0.1:7001")
    run("127.0.0.1:7001")

