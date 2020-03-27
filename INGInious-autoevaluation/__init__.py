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
import json
import os
import web
from math import ceil, floor

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

        def _take(n, iterable):
            from itertools import islice
            "Return first n items of the iterable as a list"
            return list(islice(iterable, n))

        cu_username = self.user_manager.session_username()
        course = self.course_factory.get_course(courseid)
        tasks = course.get_tasks()
        task_names = {}
        tasks_score = [0.0, 0.0, 0.0]
        completeness_per_task = {}
        user_tasks = self.database.user_tasks.find(
            {"username": cu_username, "courseid": course.get_id(), "taskid": {"$in": list(tasks.keys())}})
        registered_students = (self.user_manager.get_course_registered_users(course, False))
        count_registered_students = len(registered_students)
        all_students_user_tasks = self.database.user_tasks.find(
            {"username": {"$in": registered_students}, "courseid": course.get_id(),
             "taskid": {"$in": list(tasks.keys())}})
        completed_taskids_current_user = list(self.database.user_tasks.find(
            {"username": cu_username, "courseid": course.get_id(), "grade": 100,
             "taskid": {"$in": list(tasks.keys())}}, {"taskid": 1, "_id": 0}))
        completed_taskids_current_user = [dic_value['taskid'] for dic_value in completed_taskids_current_user]

        for taskid, task in tasks.items():
            tasks_score[1] += task.get_grading_weight()
            task_names[taskid] = task.get_name(self.user_manager.session_language())
        for user_task in user_tasks:
            weighted_score = user_task["grade"] * tasks[user_task["taskid"]].get_grading_weight()
            tasks_score[0] += weighted_score
        users_info = self.user_manager.get_course_caches(None, course)
        means = sorted([value["grade"] for key, value in users_info.items()])
        best_mean = max(means)
        median = 0
        size_means = len(means)
        if size_means % 2 == 0:
            # pair
            floor_i = size_means / 2
            ceil_i = floor_i + 1
            floor_val = means[int(floor_i - 1)]
            ceil_val = means[int(ceil_i - 1)]
            median = (floor_val + ceil_val) / 2
        else:
            # impair
            i = (size_means + 1) / 2
            median = means[int(i - 1)]

        cu_not_resolved_taskids = {}
        sorted_completeness_per_task = {k: v for k, v in
                                        sorted(completeness_per_task.items(), reverse=True, key=lambda item: item[1])}



        for user_task in all_students_user_tasks:
            if user_task["grade"] == 100:
                if user_task["taskid"] in completeness_per_task:
                    completeness_per_task[user_task["taskid"]] += 1
                else:
                    completeness_per_task[user_task["taskid"]] = 1
            tasks_score[2] += user_task["grade"] * tasks[user_task["taskid"]].get_grading_weight()
            if user_task["taskid"] not in completed_taskids_current_user:
                if user_task["taskid"] not in cu_not_resolved_taskids:
                    cu_not_resolved_taskids[user_task["taskid"]] = user_task["grade"] * tasks[
                    user_task["taskid"]].get_grading_weight()
                else:
                    cu_not_resolved_taskids[user_task["taskid"]] += user_task["grade"] * tasks[
                        user_task["taskid"]].get_grading_weight()
        for elem in cu_not_resolved_taskids:
            cu_not_resolved_taskids[elem] = cu_not_resolved_taskids[elem] / len(users_info)

        cu_course_mean = round(tasks_score[0] / tasks_score[1]) if tasks_score[1] > 0 else 0
        ranking = size_means - means.index(cu_course_mean)
        ranking = str(ranking) + "/" + str(size_means)
        all_stud_course_mean = round(tasks_score[2] / (count_registered_students * tasks_score[1])) \
            if tasks_score[1] > 0 and count_registered_students > 0 else 0

        return self.template_helper.get_custom_renderer(PATH_TO_PLUGIN + "/templates/") \
            .autoevaluation_index(course,
                                  cu_course_mean,
                                  all_stud_course_mean,
                                  completeness_per_task,
                                  str(",".join(list(tasks.keys()))),
                                  _take(5, cu_not_resolved_taskids.items()),
                                  task_names,
                                  best_mean,
                                  median,
                                  ranking)


def init(plugin_manager, _, _2, config):
    """ Init the plugin """
    page_pattern_course = r'/evaluation/([a-z0-9A-Z\-_]+)'
    plugin_manager.add_page(page_pattern_course, EvaluationBoardCourse)
    plugin_manager.add_page('/plugins/evaluation/static/(.+)', StaticMockPage)
    plugin_manager.add_hook('course_menu', course_menu)
