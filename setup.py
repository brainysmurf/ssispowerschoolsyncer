from distutils.core import setup
setup(
    name = "SSIS PowerSchool & Moodle Syncer",
    packages = ['psmdlsyncer', 'psmdlsyncer.utils'],
    version = "1.5",
    description = "Comprehensive Syncing Solution for Moodle and PowerSchool",
    author = "Adam Morris",
    author_email = "amorris@mistermorris.com",
    keywords = ["moodle"],
    requires = ['py-postgresql > (1.1.0)'],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        ],
    long_description = """\
TODO: DESCRIBE THIS!

This version requires Python 3 or later.
"""
)
