from setuptools import setup

setup(
    name='pycgroup',
    version='1.0.0',
    py_modules=['pycgroup'],
    license='MIT',
    author='Huang Shaobo',
    author_email='shaobohuang.1998@gmail.com',
    description='A Python wrapper for cgroup',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.6',
)
