import array
import base64
from hashlib import sha1

import six

from txorbit.encoding import packUShort, packULong, Reader, ReadException

WS_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

# Frame Opcodes
CONTINUE, TEXT, BINARY, CLOSE, PING, PONG = 0, 1, 2, 8, 9, 10

# Status codes
NORMAL, GOING_AWAY, PROTOCOL_ERROR, UNSUPPORTED_DATA, NONE, ABNORMAL_CLOSE, INVALID_PAYLOAD = 1000, 1001, 1002, 1003, 1005, 1006, 1007
POLICY_VIOLATION, MESSAGE_TOO_BIG, MISSING_EXTENSIONS, INTERNAL_ERROR, TLS_HANDSHAKE_FAILED = 1008, 1009, 1010, 1011, 1056


def mask(buf, key):
	key = array.array('B', key)
	buf = array.array('B', buf)

	for i in six.moves.xrange(len(buf)):
		buf[i] ^= key[i % 4]

	return buf.tostring()


def buildAccept(key):
	return base64.b64encode(sha1(b''.join([key, WS_GUID])).digest())


def is_reserved_code(opcode):
	return 2 < opcode < 8 or opcode > 10


def is_control_code(opcode):
	return opcode > 7


class FrameBuildException(Exception):
	pass


def buildFrame(opcode, body, finished=True, bMask=None):
	if isinstance(body, six.text_type):
		body = six.b(body)

	body_length = len(body)

	if bMask is None:
		lengthMask = 0x00
	else:
		lengthMask = 0x80

	if body_length > 0xffff:
		length = b''.join([chr(lengthMask | 0x7f), packULong(body_length)])
	elif body_length > 0x7d:
		length = b''.join([chr(lengthMask | 0x7e), packUShort(body_length)])
	else:
		length = chr(lengthMask | body_length)

	# Mask it if we need to
	if bMask is not None:
		body = bMask + mask(body, bMask)

	if finished:
		header = 0x80
	else:
		header = 0x01

	header = chr(header | opcode)

	return six.b(header + length) + body


def parseFrames(rawData):
	r = Reader(rawData)

	while True:
		statusCode = NORMAL
		statusMessage = ''

		try:
			header = r.readByte()
			fin = header & 0x80
			opcode = header & 0xf

			length = r.readByte()
			masked = length & 0x80

			length &= 0x7f

			if length == 0x7e:
				length = r.readUShort()
			elif length == 0x7f:
				length = r.readULong()

			if masked:
				key = r.readChars(4)

			data = r.data[r.index:r.index + length]
			r.advance(length)

			if masked:
				data = mask(data, key)

			if opcode == TEXT:
				data = data.decode('utf8')
			elif opcode == CLOSE:
				tmpr = Reader(data)
				statusCode = tmpr.readUShort()
				statusMessage = data[2:].decode('utf8')

			r.commit()
			yield opcode, data, (statusCode, statusMessage), fin
		except ReadException:
			break
