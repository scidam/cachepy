import os
from setuptools import setup





README_FILE = 'README.rst'

setup(name='cachepy',
      packages=['cachepy'],
      version='0.1',
      description='Caching results of callables in Python',
      keywords='cache, python, cache to file, caching callables, caching',
      long_description=open(README_FILE).read(),
      include_package_data=True,
      author='Dmitry E. Kislov',
      author_email='kislov@easydan.com',
      url='https://github.com/scidam/cmsplugin-nvd3',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: Site Management',
          'Topic :: Multimedia :: Graphics :: Presentation'
          ],
      )
