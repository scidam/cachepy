from setuptools import setup

README_FILE = 'README.rst'
with open(README_FILE, 'r') as d:
    desc = d.read()


setup(name='cachepy',
      packages=['.'],
      version='0.1',
      description='Caching results of function executions in Python',
      keywords='caching, python, cache to file, caching callables',
      long_description=desc,
      include_package_data=True,
      author='Dmitry Kislov',
      author_email='kislov@easydan.com',
      url='https://github.com/scidam/cachepy',
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development',
        'Intended Audience :: Developers'
          ],
      )
