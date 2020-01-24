from distutils.core import setup
setup(
    name = 'amsatapi',
    packages = ['amsatapi'],
    version = '0.1',
    license='MIT',
    description = 'AMSAT API Client for Python',
    author = 'Roger Webb',
    author_email = 'webb.roger@gmail.com',
    url = 'https://github.com/Roger/AmsatApiPython',
    download_url = 'https://github.com/RogerWebb/AmsatApiPython/archive/v_01.tar.gz',
    keywords = ['AMSAT', 'SATELLITE', 'STATUS', 'PASSES'],
    install_requires=[
        'requests'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
