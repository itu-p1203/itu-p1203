#!/usr/bin/env python3
"""
Copyright 2017-2018 Deutsche Telekom AG, Technische Universität Berlin, Technische
Universität Ilmenau, LM Ericsson

Permission is hereby granted, free of charge, to use the software for research
purposes.

Any other use of the software, including commercial use, merging, publishing,
distributing, sublicensing, and/or selling copies of the Software, is
forbidden. For a commercial license, please contact the respective rights
holders of the standards ITU-T Rec. P.1203, ITU-T Rec. P.1203.1, ITU-T Rec.
P.1203.2, and ITU-T Rec. P.1203.3. See https://www.itu.int/en/ITU-T/ipr/Pages/default.aspx
for more information.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os

import numpy as np


def execute_trees(features, path):
    res_all = []
    for fn in os.listdir(path):
        if fn.endswith(".csv") and fn.startswith("tree"):
            tree_matrix = np.genfromtxt(
                os.path.join(path, fn), delimiter=",", dtype=float
            )
            res = execute_tree(features, tree_matrix)
            res_all.append(res)
    res_mean = np.mean(res_all, axis=0)
    return res_mean


def execute_tree(features, tree_matrix):
    def recurse_execute(node_id):
        feature_id = int(tree_matrix[node_id][1])
        feature_thres = tree_matrix[node_id][2]
        left_child = int(tree_matrix[node_id][3])
        right_child = int(tree_matrix[node_id][4])

        if feature_id == -1:
            return feature_thres
        elif features[feature_id] < feature_thres:
            return recurse_execute(left_child)
        else:
            return recurse_execute(right_child)

    return recurse_execute(0)


def scale_moses(sec_mos, num_splits):
    mos_samples = []
    total_duration = len(sec_mos)
    split_duration = 1.0 * total_duration / num_splits
    previous_mos = 0
    previous_time = 0

    for i in range(total_duration):
        if previous_time + 1 >= split_duration:
            mos = (
                (previous_time * previous_mos)
                + (split_duration - previous_time) * sec_mos[i]
            ) / split_duration
            mos_samples.append(mos)
            previous_mos = sec_mos[i]
            previous_time = previous_time + 1 - split_duration
        else:
            previous_mos = ((previous_mos * previous_time) + sec_mos[i] * 1) / (
                previous_time + 1
            )
            previous_time += 1

    while len(mos_samples) < num_splits:
        mos_samples.append(previous_mos)

    return mos_samples


def get_rebuf_stats(l_buff, p_buff, duration):
    if not p_buff or (len(p_buff) == 1 and p_buff[0] == 0):
        return [0, 0, 0, 0, duration]
    else:
        events = []
        index = 0
        for b in p_buff:
            if b != 0:
                events.append((b, l_buff[index]))
            index += 1
        num_rebuf = len(events)
        len_rebuf = sum(e[1] for e in events)
        num_rebuf_per_length = 1.0 * num_rebuf / duration
        len_rebuf_per_length = 1.0 * len_rebuf / duration
        time_of_last_rebuf = duration - events[-1][0]
        return [
            num_rebuf,
            len_rebuf,
            num_rebuf_per_length,
            len_rebuf_per_length,
            time_of_last_rebuf,
        ]


def calculate(O21, O22, l_buff, p_buff, duration):
    if len(l_buff) and len(p_buff):
        if p_buff[0] == 0:
            initial_buffering_length = l_buff[0]
        else:
            initial_buffering_length = 0
    else:
        initial_buffering_length = 0
    rebuf_stats = get_rebuf_stats(l_buff, p_buff, duration)
    rebuf_stats[1] = 1.0 * initial_buffering_length / 3.0 + rebuf_stats[1]
    rebuf_stats[3] = 1.0 * initial_buffering_length / duration / 3.0 + rebuf_stats[3]

    O21_rounded = np.around(O21, decimals=3)
    O22_rounded = np.around(O22, decimals=3)
    sec_moses_feature_video = scale_moses(O22_rounded, 3)
    sec_moses_feature_audio = scale_moses(O21_rounded, 2)
    sec_mos_stat = np.percentile(O22_rounded, [1, 5, 10]).tolist()

    tree_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "trees"))

    rf_score = execute_trees(
        np.array(
            (
                rebuf_stats
                + sec_moses_feature_video
                + sec_mos_stat
                + sec_moses_feature_audio
                + [duration]
            )
        ).astype("float64"),
        path=tree_path,
    )
    return rf_score
