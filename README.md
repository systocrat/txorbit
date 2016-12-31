# Orbit

Orbit is a transactional WebSockets library written in Python. Built on top of the Twisted networking engine, Orbit can support high user load and can be used within even non-Python applications. With Twisted Web's WSGI features, Orbit can seamlessly integrate with almost any given Python web framework, although the examples in this repository use Flask.

Orbit was written to fill a gap in current WebSocket frameworks. Many current libraries are not able to flawlessly relay the results of long-running or concurrent operations to N amount of users, regardless of user interruption. A plus of using Orbit is access to the vast array of networking tools that Twisted leaves at your disposal.  
  
It would be wise to get familiar with Twisted before using this library, as there can be many "gotchas" associated with using Twisted and libraries that don't use Twisted as their networking backend. SQLAlchemy's ORM is a good example of this, as it forcibly blocks the main thread during its usage. Alchimia is a library that circumvents that using the SQLAlchemy engine-based query system with Twisted's deferToThread mechanism, but unfortunately the ORM can't be used. Another good example is the requests library, for which the Twisted maintainers have written treq for HTTP requests.  

