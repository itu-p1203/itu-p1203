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

from itertools import groupby

import numpy as np

from . import log
from .errors import P1203StandaloneError
from . import rfmodel
from . import utils


logger = log.setup_custom_logger('itu_p1203')


class P1203Pq(object):

    COEFFS = {
        "c_ref7": 0.48412879,
        "c_ref8": 10,
        "av1": -0.00069084,
        "av2": 0.15374283,
        "av3": 0.97153861,
        "av4": 0.02461776,
        "amd_1_a_threshold": 2.0,
        "t1": 0.00666620027943848,
        "t2": 0.0000404018840273729,
        "t3": 0.156497800436237,
        "t4": 0.143179744942738,
        "t5": 0.0238641564518876,
        "c1": 1.87403625,
        "c2": 7.85416481,
        "c23": 0.01853820,
        "s1": 9.35158684,
        "s2": 0.91890815,
        "s3": 11.0567558,
        "amd_1_a1": -0.066667,
        "amd_1_a2": 2.0,
        "comp1": 0.67756080,
        "comp2": -8.05533303,
        "comp3": 0.17332553,
        "comp4": -0.01035647,
        "f1": 0.02833052,
        "f2": 0.98117059
    }

    def __init__(
        self,
        O21,
        O22,
        l_buff=[],
        p_buff=[],
        device="pc",
        coeffs={},
        amendment_1_audiovisual=False,
        amendment_1_stalling=False,
        amendment_1_app_2=False
    ):
        """Initialize P.1203 model

        Initialize the model with variables extracted from input JSON file

        Arguments:
            O21 {list} -- list of O21 scores
            O22 {list} -- list of O22 scores
            l_buff {list} -- durations of buffering events [default: []]]
            p_buff {list} -- locations of buffering events in media time (in seconds) [default: []]]
            device {str} -- pc or mobile
            coeffs {dict} -- model coefficients, will overwrite defaults if same key is used [default: {}]
            amendment_1_audiovisual {bool} -- enable the fix from Amendment 1, Clause 8.2 (default: False)
            amendment_1_stalling {bool} -- enable the fix from Amendment 1, Clause 8.4 (default: False)
            amendment_1_app_2 {bool} -- enable the simplified model from Amendment 1, Appendix 2 (default: False),
                                        ensuring compatibility with P.1204.3
        """
        self.O21 = np.array(O21)
        self.O22 = np.array(O22)
        self.device = device

        self.amendment_1_audiovisual = amendment_1_audiovisual
        self.amendment_1_stalling = amendment_1_stalling
        self.amendment_1_app_2 = amendment_1_app_2

        # if one of the two is empty, choose the longer one
        self.has_audio = bool(len(self.O21))
        self.has_video = bool(len(self.O22))

        # filter out stalling events happening outside of media range
        if self.has_audio:
            max_dur = min(len(O21), len(O22))
        else:
            max_dur = len(O22)
        self.l_buff = []
        self.p_buff = []

        for l, p in zip(l_buff, p_buff):
            if p > max_dur:
                logger.warning("Excluding stalling event at position " + str(p) + ", since it is outside of media range (0, " + str(max_dur) + ")")
                continue
            if l == 0:
                logger.warning("Excluding stalling event at position " + str(p) + ", since it has zero duration")
                continue
            self.l_buff.append(l)
            self.p_buff.append(p)

        self.coeffs = {**self.COEFFS, **coeffs}

    def _calc_stalling_impact(self, num_stalls, total_stall_len, duration, avg_stall_interval):
        # Eq. 29
        stalling_impact = np.exp(-num_stalls / self.coeffs["s1"]) * \
            np.exp(-total_stall_len / duration / self.coeffs["s2"]) * \
            np.exp(-avg_stall_interval / duration / self.coeffs["s3"])
        return stalling_impact

    def _calc_stalling_features(self, duration):
        # Clause 8.1.1.1
        # calculate weighted total stalling length
        total_stall_len = sum(
            [l_buff * utils.exponential(1, self.coeffs["c_ref7"], 0, self.coeffs["c_ref8"], duration - p_buff)
             for p_buff, l_buff in zip(self.p_buff, self.l_buff)]
        )
        # calculate average stalling interval
        avg_stall_interval = 0
        num_stalls = len(self.l_buff)
        if num_stalls > 1:
            avg_stall_interval = sum([b - a for a, b in zip(self.p_buff, self.p_buff[1:])]) / (len(self.l_buff) - 1)

        return total_stall_len, num_stalls, avg_stall_interval

    def _calc_video_quality_change_rate(self, duration):
        # Clause 8.1.2.3
        vid_qual_change_rate = float(0)
        for i in range(1, duration):
            diff = self.O22[i] - self.O22[i-1]
            if diff > 0.2 or diff < -0.2:
                vid_qual_change_rate += 1
        vid_qual_change_rate = vid_qual_change_rate / duration
        return vid_qual_change_rate

    def calculate(self):
        """
        Calculate O46 and other diagnostic values according to P.1203.3

        Returns a dict:
            {
                "O23": O23,
                "O34": O34.tolist(),
                "O35": float(O35),
                "O46": float(O46)
            }
        """
        # ---------------------------------------------------------------------
        # Clause 3.2.2
        O21_len = len(self.O21)
        O22_len = len(self.O22)

        if not self.has_video:
            raise P1203StandaloneError("O22 has no scores; Pq model is not valid without video.")

        if not self.has_audio:
            duration = O22_len
            logger.warning("O21 has no scores, will assume constant high quality audio.")
            self.O21 = np.full(duration, 5.0)
        else:
            # else truncate the duration to the shorter of both streams
            if O21_len > O22_len:
                duration = O22_len
            else:
                duration = O21_len

        total_stall_len, num_stalls, avg_stall_interval = self._calc_stalling_features(duration)

        # ---------------------------------------------------------------------
        # Clause 8.1.2.2
        vid_qual_spread = max(self.O22) - min(self.O22)

        # ---
        vid_qual_change_rate = self._calc_video_quality_change_rate(duration)

        # ---------------------------------------------------------------------
        q_dir_changes_longest, q_dir_changes_tot = self._calc_qdir()

        # ---------------------------------------------------------------------
        O34, O35_baseline = self._calc_034_035_baseline(duration)

        # ---------------------------------------------------------------------
        if self.amendment_1_app_2:
            O35 = O35_baseline
        else:
            # Clause 8.1.2.1
            O34_diff = list(O34)
            for i in range(duration):
                # Eq. 5
                w_diff = utils.exponential(1, self.coeffs["c1"], 0, self.coeffs["c2"], duration-i-1)
                O34_diff[i] = (O34[i] - O35_baseline) * w_diff

            # Eq. 6
            neg_perc = np.percentile(O34_diff, 10, method='linear')
            # Eq. 7
            negative_bias = np.maximum(0, -neg_perc) * self.coeffs["c23"]

            osc_comp = self._calc_and_test_osc(duration, q_dir_changes_longest, q_dir_changes_tot, vid_qual_spread)

            # Eq. 26
            adapt_comp = 0
            adapt_test = (q_dir_changes_longest / duration) < 0.25
            if adapt_test:
                adapt_comp = np.maximum(0.0, np.minimum(self.coeffs["comp3"] * vid_qual_spread * vid_qual_change_rate + self.coeffs["comp4"], 0.5))

            # Eq. 18
            O35 = O35_baseline - negative_bias - osc_comp - adapt_comp

        # ---------------------------------------------------------------------
        stalling_impact = self._calc_stalling_impact(num_stalls, total_stall_len, duration, avg_stall_interval)
        # Eq. 31
        O23 = 1 + 4 * stalling_impact

        # ---------------------------------------------------------------------
        # Eq. 28
        mos = 1.0 + (O35 - 1.0) * stalling_impact

        # ---------------------------------------------------------------------
        # Eq. 28
        rf_score = rfmodel.calculate(self.O21, self.O22, self.l_buff, self.p_buff, duration)
        O46 = 0.75 * np.maximum(np.minimum(mos, 5), 1) + 0.25 * rf_score

        if self.amendment_1_stalling:
            q_fac = min(max(self.coeffs["amd_1_a1"] * total_stall_len + self.coeffs["amd_1_a2"], 0), 1)
            O46 = 1 + (O46 - 1) * q_fac

        # Eq. 30
        O46 = self.coeffs["f1"] + self.coeffs["f2"] * O46

        return {
            "O23": O23,
            "O34": O34.tolist(),
            "O35": float(O35),
            "O46": float(O46)
        }

    def _calc_034_035_baseline(self, duration):
        # Eq. 19-21
        O35_denominator = O35_numerator = 0
        O34 = np.zeros(duration)
        for t in range(duration):
            O34[t] = np.maximum(np.minimum(
                self.coeffs["av1"] + self.coeffs["av2"] * self.O21[t] + self.coeffs["av3"] * self.O22[t] + self.coeffs[
                    "av4"] * self.O21[t] * self.O22[t],
                5), 1)

            if self.amendment_1_audiovisual:
                # Eq. 17a
                O34[t] = (1 - max(0, self.coeffs["amd_1_a_threshold"] - self.O21[t])) * (O34[t] - 1) + 1

            temp = O34[t]
            w1 = self.coeffs["t1"] + self.coeffs["t2"] * np.exp((t / float(duration)) / self.coeffs["t3"])
            w2 = self.coeffs["t4"] - self.coeffs["t5"] * temp

            O35_numerator += w1 * w2 * temp
            O35_denominator += w1 * w2
        O35_baseline = O35_numerator / O35_denominator
        return O34, O35_baseline

    def _calc_and_test_osc(self, duration, q_dir_changes_longest, q_dir_changes_tot, vid_qual_spread):
        # ---------------------------------------------------------------------
        # Clause 8.3
        # Eq. 24
        osc_comp = 0
        osc_test = ((q_dir_changes_longest / duration) < 0.25) and (q_dir_changes_longest < 30)
        if osc_test:
            # Eq. 27
            q_diff = np.maximum(0.0, 1 + np.log10(vid_qual_spread + 0.001))
            # Eq. 23
            osc_comp = np.maximum(0.0, np.minimum(
                q_diff * np.exp(self.coeffs["comp1"] * q_dir_changes_tot + self.coeffs["comp2"]), 1.5))
        return osc_comp

    def _calc_qdir(self):
        # Clause 8.1.2.4 and 8.1.2.5
        QC = []
        ma_order = 5
        ma_kernel = np.ones(ma_order) / ma_order
        padding_beg = np.asarray([self.O22[0]] * (ma_order - 1))
        padding_end = np.asarray([self.O22[-1]] * (ma_order - 1))
        padded_O22 = np.append(np.append(padding_beg, self.O22), padding_end)
        ma_filtered = np.convolve(padded_O22, ma_kernel, mode='valid').tolist()
        step = 3
        for current_score, next_score in zip(ma_filtered[0::step], ma_filtered[step::step]):
            thresh = 0.2
            if (next_score - current_score) > thresh:
                QC.append(1)
            elif -thresh < (next_score - current_score) < thresh:
                QC.append(0)
            else:
                QC.append(-1)
        lens = []
        for index, val in enumerate(QC):
            if val != 0:
                if lens and lens[-1][1] != val:
                    lens.append([index, val])
                if not lens:
                    lens.append([index, val])
        if lens:
            lens.insert(0, [0, 0])
            lens.append([len(QC), 0])
            distances = [b[0] - a[0] for a, b in zip(lens, lens[1:])]
            longest_period = max(distances) * step
        else:
            longest_period = len(QC) * step
        q_dir_changes_longest = longest_period
        q_dir_changes_tot = sum(1 for k, g in groupby([s for s in QC if s != 0]))
        return q_dir_changes_longest, q_dir_changes_tot
