# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chaosmonkey.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='chaosmonkey.proto',
  package='chaosmonkey',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x11\x63haosmonkey.proto\x12\x0b\x63haosmonkey\".\n\x06Status\x12$\n\x03ret\x18\x01 \x01(\x0e\x32\x17.chaosmonkey.StatusCode\"R\n\nConnMatrix\x12,\n\x04rows\x18\x01 \x03(\x0b\x32\x1e.chaosmonkey.ConnMatrix.MatRow\x1a\x16\n\x06MatRow\x12\x0c\n\x04vals\x18\x01 \x03(\x02\"1\n\x08MatValue\x12\x0b\n\x03row\x18\x01 \x01(\x05\x12\x0b\n\x03\x63ol\x18\x02 \x01(\x05\x12\x0b\n\x03val\x18\x03 \x01(\x02*\x1f\n\nStatusCode\x12\x06\n\x02OK\x10\x00\x12\t\n\x05\x45RROR\x10\x01\x32\x8a\x01\n\x0b\x43haosMonkey\x12>\n\x0cUploadMatrix\x12\x17.chaosmonkey.ConnMatrix\x1a\x13.chaosmonkey.Status\"\x00\x12;\n\x0bUpdateValue\x12\x15.chaosmonkey.MatValue\x1a\x13.chaosmonkey.Status\"\x00\x62\x06proto3')
)

_STATUSCODE = _descriptor.EnumDescriptor(
  name='StatusCode',
  full_name='chaosmonkey.StatusCode',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='OK', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ERROR', index=1, number=1,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=217,
  serialized_end=248,
)
_sym_db.RegisterEnumDescriptor(_STATUSCODE)

StatusCode = enum_type_wrapper.EnumTypeWrapper(_STATUSCODE)
OK = 0
ERROR = 1



_STATUS = _descriptor.Descriptor(
  name='Status',
  full_name='chaosmonkey.Status',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ret', full_name='chaosmonkey.Status.ret', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=34,
  serialized_end=80,
)


_CONNMATRIX_MATROW = _descriptor.Descriptor(
  name='MatRow',
  full_name='chaosmonkey.ConnMatrix.MatRow',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='vals', full_name='chaosmonkey.ConnMatrix.MatRow.vals', index=0,
      number=1, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=142,
  serialized_end=164,
)

_CONNMATRIX = _descriptor.Descriptor(
  name='ConnMatrix',
  full_name='chaosmonkey.ConnMatrix',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='rows', full_name='chaosmonkey.ConnMatrix.rows', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_CONNMATRIX_MATROW, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=82,
  serialized_end=164,
)


_MATVALUE = _descriptor.Descriptor(
  name='MatValue',
  full_name='chaosmonkey.MatValue',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='row', full_name='chaosmonkey.MatValue.row', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='col', full_name='chaosmonkey.MatValue.col', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='val', full_name='chaosmonkey.MatValue.val', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=166,
  serialized_end=215,
)

_STATUS.fields_by_name['ret'].enum_type = _STATUSCODE
_CONNMATRIX_MATROW.containing_type = _CONNMATRIX
_CONNMATRIX.fields_by_name['rows'].message_type = _CONNMATRIX_MATROW
DESCRIPTOR.message_types_by_name['Status'] = _STATUS
DESCRIPTOR.message_types_by_name['ConnMatrix'] = _CONNMATRIX
DESCRIPTOR.message_types_by_name['MatValue'] = _MATVALUE
DESCRIPTOR.enum_types_by_name['StatusCode'] = _STATUSCODE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Status = _reflection.GeneratedProtocolMessageType('Status', (_message.Message,), dict(
  DESCRIPTOR = _STATUS,
  __module__ = 'chaosmonkey_pb2'
  # @@protoc_insertion_point(class_scope:chaosmonkey.Status)
  ))
_sym_db.RegisterMessage(Status)

ConnMatrix = _reflection.GeneratedProtocolMessageType('ConnMatrix', (_message.Message,), dict(

  MatRow = _reflection.GeneratedProtocolMessageType('MatRow', (_message.Message,), dict(
    DESCRIPTOR = _CONNMATRIX_MATROW,
    __module__ = 'chaosmonkey_pb2'
    # @@protoc_insertion_point(class_scope:chaosmonkey.ConnMatrix.MatRow)
    ))
  ,
  DESCRIPTOR = _CONNMATRIX,
  __module__ = 'chaosmonkey_pb2'
  # @@protoc_insertion_point(class_scope:chaosmonkey.ConnMatrix)
  ))
_sym_db.RegisterMessage(ConnMatrix)
_sym_db.RegisterMessage(ConnMatrix.MatRow)

MatValue = _reflection.GeneratedProtocolMessageType('MatValue', (_message.Message,), dict(
  DESCRIPTOR = _MATVALUE,
  __module__ = 'chaosmonkey_pb2'
  # @@protoc_insertion_point(class_scope:chaosmonkey.MatValue)
  ))
_sym_db.RegisterMessage(MatValue)



_CHAOSMONKEY = _descriptor.ServiceDescriptor(
  name='ChaosMonkey',
  full_name='chaosmonkey.ChaosMonkey',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=251,
  serialized_end=389,
  methods=[
  _descriptor.MethodDescriptor(
    name='UploadMatrix',
    full_name='chaosmonkey.ChaosMonkey.UploadMatrix',
    index=0,
    containing_service=None,
    input_type=_CONNMATRIX,
    output_type=_STATUS,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='UpdateValue',
    full_name='chaosmonkey.ChaosMonkey.UpdateValue',
    index=1,
    containing_service=None,
    input_type=_MATVALUE,
    output_type=_STATUS,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_CHAOSMONKEY)

DESCRIPTOR.services_by_name['ChaosMonkey'] = _CHAOSMONKEY

# @@protoc_insertion_point(module_scope)
