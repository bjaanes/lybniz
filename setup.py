#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup

data_files = [('share/applications',['lybniz.desktop']),('share/pixmaps',['images/lybniz.png'])]

setup(
        name = 'lybniz',
        version = '1.0.1',
        description = 'Graph Plotter',
        author = 'Thomas Führinger, Sam Tygier',
        author_email = 'ThomasFuhringer@Yahoo.com, samtygier@yahoo.co.uk',
	contact = 'Sam Tygier',
	contact_email = 'samtygier@yahoo.co.uk',
        url = 'http://lybniz2.sourceforge.net/',
        scripts = ['lybniz.py'],
        data_files = data_files,
       license = 'BSD',
        )

