# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import server_pb2 as server__pb2


class ServerStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.find_successor = channel.unary_unary(
        '/server.Server/find_successor',
        request_serializer=server__pb2.FindSucRequest.SerializeToString,
        response_deserializer=server__pb2.FindSucResponse.FromString,
        )


class ServerServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def find_successor(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_ServerServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'find_successor': grpc.unary_unary_rpc_method_handler(
          servicer.find_successor,
          request_deserializer=server__pb2.FindSucRequest.FromString,
          response_serializer=server__pb2.FindSucResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'server.Server', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
