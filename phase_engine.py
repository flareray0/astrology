"""USCS supplement phase utilities.

既存占星術ロジックを置換せず、補助評価として使う軽量モジュール。
"""

from __future__ import annotations

import cmath
import math


def normalize_deg(angle: float) -> float:
    """角度を [0, 360) に正規化する。"""
    return float(angle) % 360.0


def deg_to_rad(angle: float) -> float:
    """度をラジアンへ変換する。"""
    return math.radians(normalize_deg(angle))


def longitude_to_phase(angle_deg: float) -> complex:
    """黄経を単位円上の複素位相へ写像する。"""
    return cmath.exp(1j * deg_to_rad(angle_deg))


def phase_difference_deg(a_deg: float, b_deg: float) -> float:
    """2点の最短位相差（0〜180度）を返す。"""
    diff = abs(normalize_deg(a_deg) - normalize_deg(b_deg))
    return min(diff, 360.0 - diff)


def phase_alignment_score(a_deg: float, b_deg: float) -> float:
    """位相整合スコア [0,1]。1は同相、0は逆相。"""
    delta_rad = math.radians(phase_difference_deg(a_deg, b_deg))
    return max(0.0, min(1.0, (1.0 + math.cos(delta_rad)) / 2.0))


def phase_resonance_pair(a_deg: float, b_deg: float) -> float:
    """2天体の共鳴強度 [0,1]。

    cos(Δθ) は同相/逆相の符号を持ち解釈しやすい一方、
    ここでは「強度」を扱うため、位相ベクトル和の規格化ノルムを採用する。
    abs(z1 + z2) / 2 は同相で1、逆相で0となる。
    """
    z1 = longitude_to_phase(a_deg)
    z2 = longitude_to_phase(b_deg)
    return abs(z1 + z2) / 2.0


def phase_resonance_triple(a_deg: float, b_deg: float, c_deg: float) -> float:
    """3天体の干渉・共鳴強度 [0,1]。"""
    z1 = longitude_to_phase(a_deg)
    z2 = longitude_to_phase(b_deg)
    z3 = longitude_to_phase(c_deg)
    return abs(z1 + z2 + z3) / 3.0
