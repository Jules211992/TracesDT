import json
import math
import time
from copy import deepcopy
from pathlib import Path

from phases.P04_agent_action_space.agent.action_precondition_gate_v1 import (
    determine_eligible_actions,
)


ROOT = Path(__file__).resolve().parents[3]

P07 = (
    ROOT /
    "phases/P07_safeguard"
)

P04 = (
    ROOT /
    "phases/P04_agent_action_space"
)

THRESHOLDS_FILE = (
    P07 /
    "protocol/p07_safeguard_thresholds_v1.json"
)

ACTION_SPACE_FILE = (
    P04 /
    "actions/action_space_v1.json"
)


PHYSICAL_ACTIONS = {
    f"ACT{i:02d}"
    for i in range(1, 9)
}

ALL_ACTIONS = {
    f"ACT{i:02d}"
    for i in range(1, 11)
}


def _finite(value):
    try:
        return math.isfinite(
            float(value)
        )
    except Exception:
        return False


def _normalise_xmeas(values):
    if isinstance(values, dict):
        return {
            str(key):
                float(value)
            for key, value
            in values.items()
        }

    if isinstance(values, (list, tuple)):
        if len(values) != 41:
            raise ValueError(
                "XMEAS list must contain 41 values"
            )

        return {
            f"XMEAS({i})":
                float(
                    values[
                        i - 1
                    ]
                )
            for i in range(
                1,
                42
            )
        }

    raise TypeError(
        "Unsupported XMEAS representation"
    )


def _normalise_xmv(values):
    if isinstance(values, dict):
        return {
            str(key):
                float(value)
            for key, value
            in values.items()
        }

    if isinstance(values, (list, tuple)):
        if len(values) != 12:
            raise ValueError(
                "XMV list must contain 12 values"
            )

        return {
            f"XMV({i})":
                float(
                    values[
                        i - 1
                    ]
                )
            for i in range(
                1,
                13
            )
        }

    raise TypeError(
        "Unsupported XMV representation"
    )


def _numeric_match(
    observed,
    reference,
    tolerance,
):
    observed = float(
        observed
    )

    reference = float(
        reference
    )

    limit = (
        float(tolerance)
        * max(
            1.0,
            abs(
                reference
            ),
        )
    )

    return (
        abs(
            observed
            - reference
        )
        <= limit
    )


class P07Safeguard:
    def __init__(self):
        self.thresholds = json.loads(
            THRESHOLDS_FILE.read_text()
        )

        self.action_catalog = json.loads(
            ACTION_SPACE_FILE.read_text()
        )

        self.actions_by_id = {
            action["id"]:
                action
            for action
            in self.action_catalog[
                "actions"
            ]
        }

        if (
            set(
                self.actions_by_id
            )
            != ALL_ACTIONS
        ):
            raise RuntimeError(
                "Frozen P04 action catalog changed"
            )

        if (
            self.thresholds[
                "status"
            ]
            != "FROZEN_BEFORE_P07_OUTCOMES"
        ):
            raise RuntimeError(
                "P07 thresholds are not frozen"
            )


    def _state_validation(
        self,
        twin_xmeas,
        twin_xmv,
    ):
        failures = []

        if len(
            twin_xmeas
        ) != 41:
            failures.append(
                "XMEAS_COUNT"
            )

        if len(
            twin_xmv
        ) != 12:
            failures.append(
                "XMV_DT_COUNT"
            )

        for key, value in (
            twin_xmeas.items()
        ):
            if not _finite(
                value
            ):
                failures.append(
                    f"NONFINITE_{key}"
                )

        for key, value in (
            twin_xmv.items()
        ):
            if not _finite(
                value
            ):
                failures.append(
                    f"NONFINITE_{key}"
                )

        critical = (
            self.thresholds[
                "state_validation"
            ][
                "critical_variables"
            ]
        )

        for _, cfg in (
            critical.items()
        ):
            xkey = cfg[
                "xmeas"
            ]

            if xkey not in twin_xmeas:
                failures.append(
                    f"MISSING_{xkey}"
                )
                continue

            value = float(
                twin_xmeas[
                    xkey
                ]
            )

            low = cfg[
                "critical_low"
            ]

            high = cfg[
                "critical_high"
            ]

            if (
                low is not None
                and value
                < float(low)
            ):
                failures.append(
                    f"CRITICAL_LOW_{xkey}"
                )

            if (
                high is not None
                and value
                > float(high)
            ):
                failures.append(
                    f"CRITICAL_HIGH_{xkey}"
                )

        return {
            "passed":
                len(
                    failures
                ) == 0,

            "failures":
                failures,
        }


    def _temporal_consistency(
        self,
        metadata,
    ):
        failures = []

        required = [
            "sequence",
            "sim_time_s",
            "source_send_monotonic_ns",
            "twin_receive_monotonic_ns",
            "previous_sequence",
            "previous_sim_time_s",
            "previous_source_send_monotonic_ns",
        ]

        for key in required:
            if key not in metadata:
                failures.append(
                    f"MISSING_{key}"
                )

        if failures:
            return {
                "passed":
                    False,

                "failures":
                    failures,
            }

        sequence = int(
            metadata[
                "sequence"
            ]
        )

        previous_sequence = int(
            metadata[
                "previous_sequence"
            ]
        )

        sim_time = float(
            metadata[
                "sim_time_s"
            ]
        )

        previous_sim_time = float(
            metadata[
                "previous_sim_time_s"
            ]
        )

        source_ns = int(
            metadata[
                "source_send_monotonic_ns"
            ]
        )

        previous_source_ns = int(
            metadata[
                "previous_source_send_monotonic_ns"
            ]
        )

        if (
            sequence
            != previous_sequence
            + 1
        ):
            failures.append(
                "SEQUENCE_DISCONTINUITY"
            )

        if not math.isclose(
            sim_time
            - previous_sim_time,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            failures.append(
                "SIM_TIME_DISCONTINUITY"
            )

        if (
            source_ns
            <= previous_source_ns
        ):
            failures.append(
                "SOURCE_TIMESTAMP_NONMONOTONIC"
            )

        return {
            "passed":
                len(
                    failures
                ) == 0,

            "failures":
                failures,
        }


    def _freshness(
        self,
        metadata,
    ):
        receive_ns = int(
            metadata[
                "twin_receive_monotonic_ns"
            ]
        )

        source_ns = int(
            metadata[
                "source_send_monotonic_ns"
            ]
        )

        age_ms = (
            receive_ns
            - source_ns
        ) / 1_000_000.0

        maximum = float(
            self.thresholds[
                "freshness"
            ][
                "maximum_age_ms"
            ]
        )

        passed = (
            age_ms >= 0.0
            and age_ms <= maximum
        )

        return {
            "passed":
                passed,

            "age_ms":
                age_ms,

            "maximum_age_ms":
                maximum,

            "failures":
                []
                if passed
                else [
                    "STALE_OR_INVALID_TWIN"
                ],
        }


    def _validate_reference(
        self,
        safety_reference,
    ):
        failures = []

        if not isinstance(
            safety_reference,
            dict,
        ):
            return {
                "passed":
                    False,

                "failures": [
                    "REFERENCE_UNAVAILABLE"
                ],
            }

        for key in [
            "sequence",
            "xmeas",
            "xmv",
        ]:
            if key not in safety_reference:
                failures.append(
                    f"REFERENCE_MISSING_{key}"
                )

        if failures:
            return {
                "passed":
                    False,

                "failures":
                    failures,
            }

        try:
            xmeas = _normalise_xmeas(
                safety_reference[
                    "xmeas"
                ]
            )

            xmv = _normalise_xmv(
                safety_reference[
                    "xmv"
                ]
            )
        except Exception:
            return {
                "passed":
                    False,

                "failures": [
                    "REFERENCE_SCHEMA_INVALID"
                ],
            }

        required_xmeas = {
            "XMEAS(7)",
            "XMEAS(8)",
            "XMEAS(9)",
            "XMEAS(12)",
            "XMEAS(15)",
        }

        required_xmv = {
            "XMV(6)",
            "XMV(4)",
            "XMV(10)",
            "XMV(7)",
            "XMV(8)",
        }

        if not required_xmeas.issubset(
            xmeas
        ):
            failures.append(
                "REFERENCE_CRITICAL_XMEAS_MISSING"
            )

        if not required_xmv.issubset(
            xmv
        ):
            failures.append(
                "REFERENCE_CRITICAL_XMV_MISSING"
            )

        for key in required_xmeas:
            if (
                key in xmeas
                and not _finite(
                    xmeas[
                        key
                    ]
                )
            ):
                failures.append(
                    f"REFERENCE_NONFINITE_{key}"
                )

        for key in required_xmv:
            if (
                key in xmv
                and not _finite(
                    xmv[
                        key
                    ]
                )
            ):
                failures.append(
                    f"REFERENCE_NONFINITE_{key}"
                )

        return {
            "passed":
                len(
                    failures
                ) == 0,

            "failures":
                failures,

            "xmeas":
                xmeas,

            "xmv":
                xmv,
        }


    def _physical_consistency(
        self,
        twin_xmeas,
        twin_xmv,
        reference_xmeas,
        reference_xmv,
    ):
        failures = []

        tolerance = float(
            self.thresholds[
                "physical_consistency"
            ][
                "absolute_relative_numeric_tolerance"
            ]
        )

        critical = (
            self.thresholds[
                "state_validation"
            ][
                "critical_variables"
            ]
        )

        for _, cfg in (
            critical.items()
        ):
            xkey = cfg[
                "xmeas"
            ]

            ukey = cfg[
                "associated_xmv"
            ]

            if not _numeric_match(
                twin_xmeas[
                    xkey
                ],
                reference_xmeas[
                    xkey
                ],
                tolerance,
            ):
                failures.append(
                    f"XMEAS_MISMATCH_{xkey}"
                )

            if not _numeric_match(
                twin_xmv[
                    ukey
                ],
                reference_xmv[
                    ukey
                ],
                tolerance,
            ):
                failures.append(
                    f"XMV_MISMATCH_{ukey}"
                )

        return {
            "passed":
                len(
                    failures
                ) == 0,

            "failures":
                failures,
        }


    def _authorization(
        self,
        action_id,
        candidate_command,
    ):
        failures = []

        if (
            action_id
            not in self.actions_by_id
        ):
            return {
                "passed":
                    False,

                "failures": [
                    "UNKNOWN_ACTION_ID"
                ],
            }

        frozen_command = deepcopy(
            self.actions_by_id[
                action_id
            ][
                "executable_command"
            ]
        )

        if (
            candidate_command
            != frozen_command
        ):
            failures.append(
                "COMMAND_NOT_FROZEN_CATALOG"
            )

        return {
            "passed":
                len(
                    failures
                ) == 0,

            "failures":
                failures,

            "frozen_command":
                frozen_command,
        }


    def evaluate(
        self,
        original_proposal,
        candidate_command,
        twin_state,
        safety_reference,
        metadata,
    ):
        start_ns = (
            time.monotonic_ns()
        )

        original_copy = deepcopy(
            original_proposal
        )

        action_id = (
            original_proposal.get(
                "action_id"
            )
            if isinstance(
                original_proposal,
                dict,
            )
            else None
        )

        try:
            twin_xmeas = (
                _normalise_xmeas(
                    twin_state[
                        "xmeas"
                    ]
                )
            )

            twin_xmv = (
                _normalise_xmv(
                    twin_state[
                        "xmv_dt"
                    ]
                )
            )

            twin_schema_valid = True

        except Exception:
            twin_xmeas = {}
            twin_xmv = {}
            twin_schema_valid = False


        if twin_schema_valid:
            state_validation = (
                self._state_validation(
                    twin_xmeas,
                    twin_xmv,
                )
            )
        else:
            state_validation = {
                "passed":
                    False,

                "failures": [
                    "TWIN_SCHEMA_INVALID"
                ],
            }


        temporal = (
            self._temporal_consistency(
                metadata
            )
        )

        freshness = (
            self._freshness(
                metadata
            )
        )

        reference_validation = (
            self._validate_reference(
                safety_reference
            )
        )


        same_sequence = False
        reference_gate = None

        physical_consistency = {
            "passed":
                False,

            "failures": [
                "REFERENCE_UNAVAILABLE"
            ],
        }


        if reference_validation[
            "passed"
        ]:
            same_sequence = (
                int(
                    safety_reference[
                        "sequence"
                    ]
                )
                == int(
                    metadata[
                        "sequence"
                    ]
                )
            )

            if not same_sequence:
                reference_validation[
                    "passed"
                ] = False

                reference_validation[
                    "failures"
                ].append(
                    "REFERENCE_SEQUENCE_MISMATCH"
                )

            else:
                reference_gate = (
                    determine_eligible_actions(
                        self.action_catalog,
                        reference_validation[
                            "xmeas"
                        ],
                        uncertain=False,
                    )
                )

                if twin_schema_valid:
                    physical_consistency = (
                        self._physical_consistency(
                            twin_xmeas,
                            twin_xmv,
                            reference_validation[
                                "xmeas"
                            ],
                            reference_validation[
                                "xmv"
                            ],
                        )
                    )


        authorization = (
            self._authorization(
                action_id,
                candidate_command,
            )
        )


        compromise_detected = bool(
            not state_validation[
                "passed"
            ]
            or not temporal[
                "passed"
            ]
            or not freshness[
                "passed"
            ]
            or not physical_consistency[
                "passed"
            ]
        )


        decision = None
        execution_action = None
        correction_action = None
        decision_reason = None


        if not reference_validation[
            "passed"
        ]:
            decision = "ESCALATE"
            decision_reason = (
                "safety_reference_unavailable_or_invalid"
            )

        elif (
            reference_gate[
                "decision"
            ]
            == "ESCALATE_ELIGIBILITY"
        ):
            decision = "ESCALATE"
            decision_reason = (
                "independent_reference_ambiguous"
            )

        elif action_id == "ACT09":
            decision = "ESCALATE"
            decision_reason = (
                "original_agent_requested_human_escalation"
            )

        elif not authorization[
            "passed"
        ]:
            decision = "BLOCK"
            decision_reason = (
                "proposal_or_command_not_authorized"
            )

        else:
            matched = (
                reference_gate[
                    "matched_physical_action_ids"
                ]
            )

            if action_id in PHYSICAL_ACTIONS:
                if matched == [
                    action_id
                ]:
                    decision = "EXECUTE"
                    execution_action = (
                        action_id
                    )
                    decision_reason = (
                        "original_physical_action_"
                        "independently_confirmed"
                    )

                elif matched == []:
                    decision = "BLOCK"
                    decision_reason = (
                        "original_physical_action_"
                        "not_independently_justified"
                    )

                elif len(
                    matched
                ) == 1:
                    decision = "CORRECT"
                    correction_action = (
                        matched[0]
                    )
                    execution_action = (
                        matched[0]
                    )
                    decision_reason = (
                        "single_different_safe_"
                        "physical_action_confirmed"
                    )

                else:
                    decision = "ESCALATE"
                    decision_reason = (
                        "independent_reference_ambiguous"
                    )

            elif action_id == "ACT10":
                if matched == []:
                    decision = "EXECUTE"
                    execution_action = (
                        "ACT10"
                    )
                    decision_reason = (
                        "no_action_independently_confirmed"
                    )

                elif len(
                    matched
                ) == 1:
                    decision = "CORRECT"
                    correction_action = (
                        matched[0]
                    )
                    execution_action = (
                        matched[0]
                    )
                    decision_reason = (
                        "single_required_physical_"
                        "response_confirmed"
                    )

                else:
                    decision = "ESCALATE"
                    decision_reason = (
                        "independent_reference_ambiguous"
                    )

            else:
                decision = "BLOCK"
                decision_reason = (
                    "unknown_or_unsupported_proposal"
                )


        corrected_command = None

        if (
            decision == "CORRECT"
            and correction_action
            in self.actions_by_id
        ):
            corrected_command = deepcopy(
                self.actions_by_id[
                    correction_action
                ][
                    "executable_command"
                ]
            )


        end_ns = (
            time.monotonic_ns()
        )

        return {
            "phase":
                "P07",

            "safeguard":
                "Independent Safety Reference Safeguard",

            "original_agent_proposal":
                original_copy,

            "original_agent_proposal_preserved":
                original_copy
                == original_proposal,

            "original_action_id":
                action_id,

            "decision":
                decision,

            "decision_reason":
                decision_reason,

            "execution_candidate_action":
                execution_action,

            "correction_action":
                correction_action,

            "corrected_command":
                corrected_command,

            "digital_compromise_detected":
                compromise_detected,

            "checks": {
                "State_Validation":
                    state_validation,

                "Temporal_Consistency":
                    temporal,

                "Freshness":
                    freshness,

                "Physical_Consistency":
                    physical_consistency,

                "Action_Safety": {
                    "reference_gate":
                        reference_gate,
                },

                "Authorization":
                    authorization,

                "Reference_Validation":
                    reference_validation,

                "same_sequence_reference":
                    same_sequence,
            },

            "safeguard_start_monotonic_ns":
                start_ns,

            "safeguard_end_monotonic_ns":
                end_ns,

            "safeguard_latency_ns":
                end_ns
                - start_ns,

            "safeguard_latency_ms":
                (
                    end_ns
                    - start_ns
                ) / 1_000_000.0,

            "fabric":
                False,

            "ipfs":
                False,

            "oracle":
                False,
        }
