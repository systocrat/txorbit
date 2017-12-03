from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.web.server import Site

from txorbit.resource import WebSocketResource
from txorbit.transaction import WSProtocol, Transaction
from twisted.internet.defer import setDebugging

class EchoProtocol(WSProtocol):
	def dataReceived(self, ws, data, isBinary):
		print(data)
		if isBinary:
			ws.sendBinary(data)
		else:
			ws.sendText(data)


if __name__ == '__main__':
	tx = Transaction(EchoProtocol)

	site = Site(WebSocketResource(lambda s: tx))

	setDebugging(True)
	endpoint = TCP4ServerEndpoint(reactor, 8900, interface='0.0.0.0')
	endpoint.listen(site)

	reactor.run()