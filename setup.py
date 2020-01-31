# -*- coding: utf-8 -*-
#
#   Author 2020 Ludovic Taffin
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#   Auto-evaluation plugin for INGInious

from setuptools import setup,find_packages

retval = setup(
    name='INGInious-autoevaluation',
    version="0.1",
    author="Ludovic Taffin",
    author_email = "ludovic.taffin@uclouvain.be",
    packages=find_packages(),
    url="http://www.uclouvain.be",
    license = "GNU",
    description="A plugin for INGInious to let stduents auto evaluate themselves",
    include_package_data=True,

)

