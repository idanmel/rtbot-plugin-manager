from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='rtbot_plugin_manager',
      version='0.1',
      description='Plugin Manager For RTBot',
      long_description=readme(),
      classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='plugin manager',
      url='https://github.com/idanmel/rtbot-plugin-manager',
      author='Henrik Heimbuerger & Idan Melamed',
      author_email='idanmel@gmail.com',
      license='MIT',
      packages=['rtbot_plugin_manager'],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      zip_safe=False)
