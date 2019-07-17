from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='mkgfdv',
      version='0.1',
      description='Multimodal Knowledge Graph Functional Dependency Validator',
      author='WX Wilcke',
      author_email='w.x.wilcke@vu.nl',
      license='GPL3',
      install_requires=[
          "rdflib == 4.2.1"
      ],
      packages=['mkgfdv', 'mkgfdv.mkgfd'],
      include_package_data=True)
