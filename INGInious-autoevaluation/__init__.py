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
from math import ceil, floor

from flask import send_from_directory
from inginious.frontend.pages.utils import INGIniousPage, INGIniousAuthPage

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


def course_menu(course, template_helper):
    """ Displays the link to the board on the course page, if the plugin is activated for this course """
    return template_helper.render("course_menu.html", template_folder=PATH_TO_PLUGIN + '/templates/', course=course)


class StaticMockPage(INGIniousPage):
    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

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
        try:
            index = means.index(cu_course_mean)
        except ValueError:
            index = 0
        ranking = size_means - index
        ranking = str(ranking) + "/" + str(size_means)
        all_stud_course_mean = round(tasks_score[2] / (count_registered_students * tasks_score[1])) \
            if tasks_score[1] > 0 and count_registered_students > 0 else 0

        return self.template_helper.render("autoevaluation_index.html", template_folder=PATH_TO_PLUGIN + "/templates/",
                                           course=course, personnal_grade=cu_course_mean, all_grade=all_stud_course_mean,
                                           success_per_task=completeness_per_task, task_ids=str(",".join(list(tasks.keys()))),
                                           tasks_not_resolved=_take(5, cu_not_resolved_taskids.items()),
                                           task_names=task_names, best_mean=best_mean, median=median, ranking=ranking)


def init(plugin_manager, _, _2, config):
    """ Init the plugin """
    plugin_manager.add_page('/evaluation/<courseid>', EvaluationBoardCourse.as_view("evaluationboardcoursepage"))
    plugin_manager.add_page('/plugins/evaluation/static/<path:path>', StaticMockPage)
    plugin_manager.add_hook('course_menu', course_menu)
