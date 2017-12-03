from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.internet.task import LoopingCall

from txorbit import framing


class WebSocketServerFactory(Factory):
	def __init__(self, *args, **kwargs):
		reactor = kwargs.pop('reactor', None)
		if reactor is None:
			from twisted.internet import reactor

		self.reactor = reactor

	def buildProtocol(self, addr):
		return WebSocketProtocol()


class WebSocketProtocol(Protocol):
	def __init__(self):
		self.finished = Deferred()
		self.pingLoop = LoopingCall(self.ping)
		self._pingTimeout = None
		self.connected = False
		self.closedCleanly = False

	def sendBinary(self, payload):
		'''
		Send a binary payload to the remote client
		:param payload: bytes object
		:return:
		'''
		self.sendMessage(payload, True)

	def sendText(self, payload):
		'''
		Send a text payload to the remote client
		:param payload: The data to send
		'''
		self.sendMessage(payload.encode('utf8'), False)

	def sendMessage(self, data, isBinary=True):
		'''
		Send a message (either with the BINARY or TEXT opcode) to the remote client
		:param data: The data to send.
		:param isBinary: Whether the data is binary or text
		'''
		self.sendFrame(framing.BINARY if isBinary else framing.TEXT, data)

	def sendFrame(self, opcode, data):
		'''
			Send a raw WebSocket frame to the remote client
		:param opcode: The opcode to use
		:param data: The data to send with
		'''
		self.transport.write(framing.buildFrame(opcode, data))

	def ping(self):
		if self._pingTimeout is not None and self._pingTimeout.active:
			return

		if self.connected:
			self.sendFrame(framing.PING, 'orbit-ping')
			self._pingTimeout = reactor.callLater(20, self.transport.abortConnection)

	def connectionMade(self):
		self.connected = True
		self.inner.connectionMade(self)
		self.pingLoop.start(10)

	def close(self, wasClean, code, reason):
		self.pingLoop.stop()

		if self._pingTimeout is not None and self._pingTimeout.active:
			self._pingTimeout.cancel()

		self.finished.callback((wasClean, code, reason))

	def dataReceived(self, data):
		for opcode, data, (code, message), fin in framing.parseFrames(data):
			if opcode == framing.CLOSE:
				self.closedCleanly = True
				self.close(True, code, message)

			elif opcode == framing.PING:
				self.sendFrame(framing.PONG, data)

			elif opcode == framing.PONG:
				if self._pingTimeout is not None and self._pingTimeout.active:
					self._pingTimeout.cancel()
					self._pingTimeout = None

			elif opcode in (framing.BINARY, framing.TEXT):
				self.inner.dataReceived(self, data, opcode == framing.BINARY)

	def connectionLost(self, reason=connectionDone):
		self.connected = False

		if not self.closedCleanly:
			self.close(False, -1, reason)
