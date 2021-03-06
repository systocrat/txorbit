from twisted.internet.defer import maybeDeferred
from twisted.protocols.policies import ProtocolWrapper
from twisted.web.resource import NoResource, IResource, Resource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implementer

from txorbit.framing import buildAccept
from txorbit.websockets import WebSocketServerFactory


class WSGISiteResource(Resource):
	def __init__(self, wsgiResource, children):
		Resource.__init__(self)
		self._wsgiResource = wsgiResource
		self.children = children

	def getChild(self, path, request):
		request.prepath.pop()
		request.postpath.insert(0, path)
		return self._wsgiResource


@implementer(IResource)
class WebSocketResource(object):
	"""
	A Twisted Web resource for WebSocket.
	"""
	isLeaf = True

	def __init__(self, lookup, keyword=None):
		"""

		:param factory: An instance of :class:`autobahn.twisted.websocket.WebSocketServerFactory`.
		:type factory: obj
		:param lookup: a function that accepts the keyword query parameter and returns a Transaction, or throws an exception if one wasn't found
		:type lookup: func
		:param keyword: the query parameter used to locate transactions
		:type keyword: string or None
		"""
		self._factory = WebSocketServerFactory()
		self.lookup = lookup
		self.keyword = keyword

	# noinspection PyUnusedLocal
	def getChildWithDefault(self, name, request):
		"""
		This resource cannot have children, hence this will always fail.
		"""
		return NoResource("No such child resource.")

	def putChild(self, path, child):
		"""
		This resource cannot have children, hence this is always ignored.
		"""

	def render(self, request):
		request.defaultContentType = None
		protocol = self._factory.buildProtocol(request.transport.getPeer())

		if not protocol:
			# If protocol creation fails, we signal "internal server error"
			request.setResponseCode(500)
			return b""

		# If we fail at all, we'll fail with 400 and no response.
		failed = False

		if request.method != b'GET':
			failed = True

		upgrade = request.getHeader('Upgrade')

		if not upgrade or 'websocket' not in upgrade.lower():
			failed = True

		connection = request.getHeader('Connection')

		if not connection or 'upgrade' not in connection.lower():
			failed = True

		key = request.getHeader('Sec-WebSocket-Key')

		if not key:
			failed = True

		key = key.encode('utf8')

		version = request.getHeader('Sec-WebSocket-Version')

		if not version or version != '13':
			failed = True

		request.setHeader('Sec-WebSocket-Version', '13')

		if failed:
			request.setResponseCode(400)
			return b''

		if self.keyword is not None and self.keyword in request.args:
			lookupKw = self.keyword
		else:
			lookupKw = None

		#request.transport.pauseProducing()

		d = maybeDeferred(self.lookup, lookupKw)
		d.addCallback(self.setupTransaction, request, protocol, key)
		d.addErrback(self.setupError, request)

		return NOT_DONE_YET

	def setupError(self, exc, request):
		# If the lookup for a transaction fails or throws an Exception, return 500 internal serer error
		request.setResponseCode(500)
		request.finish()

	def setupTransaction(self, transaction, request, protocol, key):
		request.setResponseCode(101)

		request.setHeader(b'Upgrade', b'WebSocket')
		request.setHeader(b'Connection', b'Upgrade')
		request.setHeader(b'Sec-WebSocket-Accept', buildAccept(key))

		request.write('')

		transport, request.channel.transport = request.channel.transport, None

		if isinstance(transport, ProtocolWrapper):
			# i.e. TLS is a wrapping protocol
			transport.wrappedProtocol = protocol
		else:
			transport.protocol = protocol

		transaction.adoptWebSocket(protocol)
		protocol.makeConnection(transport)

		transport.resumeProducing()


