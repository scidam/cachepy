Caching results of functions in Python
======================================

.. image:: https://travis-ci.com/scidam/cachepy.svg?branch=dev
    :target: https://travis-ci.com/scidam/cachepy


A caching toolset for Python. It is tested for both
Python 2.7.x and 3.4+ (<3.8).

Features
--------

    * Memory-based and file-based caches;
    * Ability to set the TTL (time-to-live) and NOC (the number of calls) on caches;
    * Encryption of the cached data (symmetric encryption algorithm (RSA) is used);
    * LFU (least frequently used) and MFU (most frequently used) cache-clearing strategies;
    * caches of limited size;

Notes
-----

    - Encryption functionality requires the `PyCryptodome` package to be installed;
    - File-based caches save the cached data in a file; files with cached data should be
      cleaned up manually, if needed.

Examples
--------

.. code-block:: python

    from cachepy import *

    mycache = Cache()
    # save the cached data to memory without encryption

    @mycache
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(2)
    # "Hi, I am called..." will be printed to stdout only once
    # return 4

    my_heavy_function(2)
    # return 4


To store data to a file, one needs to initialize a decorator, as follows:

.. code-block:: python

    # create cache-to-file decorator
    filecache = FileCache('mycache')  # mycache.dat file will be created;
    # `.dat` extension is appended automatically to the filename
    # (depends on the shelve module implementation);

Its behavior is the same as a memory-based one, but all cached data is stored in
the specified file.

One can set up time-to-live (TTL) and/or maximum number of calls (NOC)
for the cached data when the decorator is initialized:

.. code-block:: python

    import time
    from cachepy import *

    cache_with_ttl = Cache(ttl=2)  # ttl given in seconds

    @cache_with_ttl
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    # Hi, I am called... will be printed
    # return 9
    my_heavy_function(3)
    # 'Hi, I am called ...' will not be printed
    # return 9
    time.sleep(2)
    my_heavy_function(3)
    # 'Hi, I am called ...' will be printed again
    # return 9


.. code-block:: python

    cache_with_noc = Cache(noc=2)  # the number-of-calls: noc = 2

    @cache_with_noc
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3) # 'Hi, I am called ...' will not be printed
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again


It is easy to use both `NOC` and `TTL` arguments when defining
a caching decorator:

.. code-block:: python

    cache_with_noc_ttl = Cache(noc=2, ttl=1)

    @cache_with_noc_ttl
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3)  # 'Hi, I am called ...' will not be printed
    my_heavy_function(3)  # 'Hi, I am called ...' will be printed (noc is
    # reached, recompute the func value)
    time.sleep(2)  # get ttl expired
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again

One can encrypt the cached data by providing a non-empty `key` argument as
a password (RSA encryption algorithm is used):

.. code-block:: python

    cache_to_file_ttl_noc = FileCache('mycache',
                                      noc=2, ttl = 2,
                                      key='mypassword')

    @cache_to_file_ttl_noc
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(2) # 'Hi, I am called...' will be printed
    my_heavy_function(2) # 'Hi, I am called...' will not be printed

When `my_heavy_function` is decorated by `cache_to_file_ttl_noc`, as shown
in the example above, the value `2**2 = 4` will be computed and the result of
the computation will be stored in the file named `mycache.dat`. Along
with the result of the computation,  additional information will be stored
in the file `mycache.dat`. The additional information includes:
1) the result's expiration time (computed from the TTL), 
2) NOC and 3) the number of already performed calls of the function being
decorated (`my_heavy_function`).

Encryption is available only if `PyCryptodome` package is installed and the
`key` parameter (a non-empty string representing the password) is passed to the
cache constructor. It also could work with the old PyCrypto package.

If you passed the non-empty `key` parameter to the cache constructor
but `PyCryptodome` was not found, a special warning would be raised in this case
("PyCryptodome not installed. Data will not be encrypted") and
the cache would work as usual but without encryption functionality.


Caching with limitations
------------------------

Standard cache constructors are used to initialize caches of unlimited capacity.
There are also caches of limited capacity.
Such caches are initialized by constructors named `LimitedCache` and `LimitedFileCache`.
These constructors have additional
parameters `cache_size` (the maximum number of items stored in the cache) and
`algorithm` (cache-clearing algorithm). Available `algorithm` values are
`lfu` (default, which stands for least frequently used) and `mfu` (most frequently used).
When `algorithm='lfu'`, then the least frequently used item is removed from the cache,
if it is exhausted. In case of `algorithm='mfu'`, everything behaves the same way,
with the only difference being that the most frequently used item is removed.


Testing
-------

.. code-block:: bash

         python -m  cachepy.test


TODO
----

    * Writing backend for redis server


Log list
--------

    * Version 1.1
    * Version 1.0 (broken installation via pip/pipenv)
    * Version 0.1
        - initial release


Author
------

    Dmitry Kislov <kislov@easydan.com>
