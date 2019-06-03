import server_pb2_grpc
import server_pb2
import grpc

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

if __name__ == "__main__":
    getNodeStatus("127.0.0.1:7001")