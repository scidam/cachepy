
Intro
*****

Caching results of callables in Python.


Features
========

   * Storing cached data either on disk or in memory

   * Setting up time-to-live and the number of function calls for
     your cache

   * Encryption of cached data (symmetric encryption (RSA) algorithm used)


Note
====

   * Encryption functionality requires *pycrypto* package.

   * When using cache-to-file functionality you have to to clean up
     (if needed) created file(s) manually


Examples
========

::

   from cachepy import *

   mycache = Cache() # cache to memory without encryption

   @mycache
   def my_heavy_function(x):
       """Performs heavy computations"""
       print('Hi, I am called...')
       return x**2

   my_heavy_function(2)
   # "Hi, I am called..." will be printed to stdout only once
   my_heavy_function(2)

*memcache* -- is decorator obtained via wildcard importing from
cachepy. It is fully equivalent to *mycache* in the example above.

To store data to file, you need to create decorator as follows: ::

   # create cache-to-file decorator
   filecache = Cache('mycache.dat')

Its behaviour is the same as a memory-based one.

One can set up time-to-live and/or maximum number of getting cached
data on a decorator creation: ::

   import time
   from cachepy import *
   # or from cachepy import Cache

   cache_with_ttl = Cache(ttl=2) # ttl given in seconds

   @cache_with_ttl
   def my_heavy_function(x):
       """Performs heavy computations"""
       print('Hi, I am called...')
       return x**2

   my_heavy_function(3)
   my_heavy_function(3) # This will not print 'Hi, I am called ...'
   time.sleep(2)
   my_heavy_function(3) # 'Hi, I am called ...' will be printed again

   cache_with_noc = Cache(noc=2) # Number-of-calls = 2

   @cache_with_noc
   def my_heavy_function(x):
       """Performs heavy computations"""
       print('Hi, I am called...')
       return x**2

   my_heavy_function(3)
   my_heavy_function(3) # This will not print 'Hi, I am called ...'
   my_heavy_function(3) # 'Hi, I am called ...' will be printed again

One can set up both *noc* and *ttl* arguments on a cache decorator: ::

   cache_with_noc_ttl = Cache(noc=2, ttl=1)

   @cache_with_noc_ttl
   def my_heavy_function(x):
       """Performs heavy computations"""
       print('Hi, I am called...')
       return x**2

   my_heavy_function(3)
   my_heavy_function(3) # This will not print 'Hi, I am called ...'
   my_heavy_function(3) # This will print 'Hi, I am called ...'
   time.sleep(2) # get ttl to be expired
   my_heavy_function(3) # This will print 'Hi, I am called ...'

One can encrypt cached data by providing non-empty *key* argument as a
password (RSA algo is used): ::

   cache_to_file_ttl_noc = Cache('mycache.dat',
                                  noc=2, ttl = 2, key='mypassword')

   @cache_to_file_ttl_noc
   def my_heavy_function(x):
       """Performs heavy computations"""
       print('Hi, I am called...')
       return x**2

   my_heavy_function(2) # Will print 'Hi, I am called...'
   my_heavy_function(2) # Will not print 'Hi, I am called...'

Calling *my_heavy_function* decorated by *cache_to_file_ttl_noc* will
store *4* (result of computations) in the file *mycache.dat*; along
with the result of computations, additional info will be stored (and
encrypted by the RSA algo with the password *mypassword*): result
expiration  time (computed from ttl), noc and the number of performed
calls of the decorated function (*my_heavy_function*). Data will not
be encrypted, if *pycrypto* package isn't installed. If you pass non-
empty *key* parameter to the  *Cache* constructor, a warning will
occurred ("Pycrypto not installed. Data isn't encrypted"); In this
case, cache will work without encryption functionality.


Testing
=======

The code tested (and works as expected) in **Python > 2.7.x** and **Python > 3.4.x**.

      python -m  cachepy.test


TODO
====

   * Writing backend for redis server

   * Testing in Python 3.x causes Error 11?!

*Code author: Dmitry Kislov <kislov@easydan.com>*
