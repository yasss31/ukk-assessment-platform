"""
app/services/rubric_engine.py - Mesin Penghitung & Evaluator Rubrik Penilaian
"""
from typing import List, Dict, Tuple
from app.models.schemas import RubricProfile, IndicatorResult, IndicatorStatus


class RubricEngine:
    @staticmethod
    def calculate_score(indicators_eval: List[IndicatorResult], profile: RubricProfile) -> Tuple[float, int, int, int, int, int]:
        """
        Menghitung nilai akhir secara transparan berdasarkan bobot masing-masing indikator.
        Returns: (final_score, pass_count, fail_count, skip_count, error_count, warning_count)
        """
        pass_count = 0
        fail_count = 0
        skip_count = 0
        error_count = 0
        warning_count = 0

        total_weight = 0.0
        earned_weighted_score = 0.0

        ind_weights = {ind.code: ind.weight for ind in profile.indicators}

        for res in indicators_eval:
            weight = ind_weights.get(res.code, res.weight or 1.0)
            res.weight = weight

            if res.status == IndicatorStatus.PASS:
                pass_count += 1
                total_weight += weight
                res.score = 1.0 * weight
                earned_weighted_score += res.score
            elif res.status == IndicatorStatus.FAIL:
                fail_count += 1
                total_weight += weight
                res.score = 0.0
            elif res.status == IndicatorStatus.WARNING:
                warning_count += 1
                total_weight += weight
                res.score = 0.5 * weight  # Setengah bobot untuk warning
                earned_weighted_score += res.score
            elif res.status == IndicatorStatus.ERROR:
                error_count += 1
                total_weight += weight
                res.score = 0.0
            elif res.status == IndicatorStatus.SKIP:
                skip_count += 1
                res.score = 0.0
                # SKIP tidak mengurangi penyebut total bobot aktif jika penilaian opsional

        if total_weight > 0:
            final_score = round((earned_weighted_score / total_weight) * 100.0, 1)
        else:
            final_score = 0.0

        return final_score, pass_count, fail_count, skip_count, error_count, warning_count
