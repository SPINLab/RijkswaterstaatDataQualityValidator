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
      url='https://gitlab.com/wxwilcke/mkgfdv',
      install_requires=[
          "rdflib == 4.2.1"
      ],
      dependency_links=['git+https://gitlab.com/wxwilcke/mkgfd.git@master#egg=mkgfd'],
      packages=['mkgfdv'],
      include_package_data=True)
