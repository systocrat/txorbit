import random
import string

import six
from twisted.internet.defer import Deferred


class WSProtocol(object):
	def __init__(self, transaction):
		# note-- this is a circular reference, which is probably acceptable since a transaction shouldn't
		# ever be disposed while it still has connections associated with it, however keep in mind this
		# means the transaction/protocols will be stuck in scope if a protocol ever leaks
		self.transaction = transaction

	def connectionMade(self, ws):
		pass

	def dataReceived(self, ws, data, isBinary):
		pass

	def connectionEnd(self):
		pass

	def disconnect(self):
		self.ws.transport.abortConnection()

	@property
	def ws(self):
		return self.transaction.connections[self]


class Transaction(object):
	def __init__(self, protocol):
		self.protocol = protocol
		# map of protocol: underlying ws connection
		self.connections = {}
		self.finished = Deferred()

	def adoptWebSocket(self, protocol):
		p = self.protocol(self)
		self.connections[p] = protocol

		protocol.inner = p
		protocol.finished.addCallback(self.ws_disconnected, p)

		# p.connectionMade(protocol)

		return protocol

	def finish(self):
		for connection in self.connections.values():
			connection.transport.loseConnection()

		self.connections = {}
		self.finished.callback(self)

	def ws_disconnected(self, ws, proto):
		# is ws even available for writing here? this connection is presumably already terminated
		proto.connectionEnd()
		del self.connections[proto]


class TransactionNotFoundException(Exception):
	pass


try:
	transaction_charset = string.ascii_letters + string.digits
except AttributeError:
	transaction_charset = string.letters + string.digits


class TransactionManager(object):
	def __init__(self):
		self.transactions = {}

	def addTransaction(self, transaction, rstr=None):
		if rstr is None:
			rstr = ''.join([random.choice(transaction_charset) for _ in six.moves.xrange(32)])

		self.transactions[rstr] = transaction

		transaction.finished.addCallback(self.completeTransaction, rstr)
		return rstr

	def hasTransaction(self, key):
		return key in self.transactions

	def completeTransaction(self, result, rstr):
		del self.transactions[rstr]
		return result

	def __call__(self, secretKey):
		if secretKey not in self.transactions:
			raise TransactionNotFoundException()

		return self.transactions[secretKey]
