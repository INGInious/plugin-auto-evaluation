#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   @author 2019 Ludovic Taffin
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

""" A plugin that allow students to autoevaluate their work """

import os
import web

from inginious.frontend.pages.utils import INGIniousAuthPage

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


def course_menu(course, template_helper):
    """ Displays the link to the board on the course page, if the plugin is activated for this course """
    return str(template_helper.get_custom_renderer(PATH_TO_PLUGIN + '/templates/', layout=False).course_menu(course))


class StaticMockPage(object):
    def GET(self, path):
        if not os.path.abspath(PATH_TO_PLUGIN) in os.path.abspath(os.path.join(PATH_TO_PLUGIN, path)):
            raise web.notfound()

        try:
            with open(os.path.join(PATH_TO_PLUGIN, "static", path), 'rb') as file:
                return file.read()
        except:
            raise web.notfound()

    def POST(self, path):
        return self.GET(path)


class EvaluationBoardCourse(INGIniousAuthPage):
    def GET_AUTH(self, courseid):
        course = self.course_factory.get_course(courseid)
        return self.template_helper.get_custom_renderer(PATH_TO_PLUGIN + "/templates/").autoevaluation_index(course)


def init(plugin_manager, _, _2, config):
    """ Init the plugin """
    page_pattern_course = r'/evaluation/([a-z0-9A-Z\-_]+)'
    plugin_manager.add_page(page_pattern_course, EvaluationBoardCourse)
    plugin_manager.add_page('/plugins/evaluation/static/(.+)', StaticMockPage)
    plugin_manager.add_hook('course_menu', course_menu)
