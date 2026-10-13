from copy import deepcopy

from phases.P07_safeguard.scripts.safeguard_v1 import (
    P07Safeguard,
)


DIAGNOSTIC_CHECKS = {
    "state_validation": "State_Validation",
    "physical_consistency": "Physical_Consistency",
    "temporal_consistency": "Temporal_Consistency",
    "freshness": "Freshness",
}

ENFORCEMENT_CHECKS = {
    "action_safety",
    "authorization",
}

ALL_CHECKS = set(DIAGNOSTIC_CHECKS) | ENFORCEMENT_CHECKS


class P07SafeguardV3(P07Safeguard):
    """
    Final two-output safeguard policy.

    z_t: compromise alarm derived from diagnostic checks.
    d_t: execution decision derived from the independent safety
         reference, action safety, and authorization.
    """

    def evaluate(
        self,
        original_proposal,
        candidate_command,
        twin_state,
        safety_reference,
        metadata,
        disabled_checks=None,
    ):
        disabled = set(disabled_checks or [])

        unknown = disabled - ALL_CHECKS
        if unknown:
            raise ValueError(
                f"Unknown disabled checks: {sorted(unknown)}"
            )

        raw = super().evaluate(
            original_proposal=original_proposal,
            candidate_command=candidate_command,
            twin_state=twin_state,
            safety_reference=safety_reference,
            metadata=metadata,
        )

        action_id = (
            original_proposal.get("action_id")
            if isinstance(original_proposal, dict)
            else None
        )

        frozen_command = None
        if action_id in self.actions_by_id:
            frozen_command = deepcopy(
                self.actions_by_id[
                    action_id
                ]["executable_command"]
            )

        action_safety_result = super().evaluate(
            original_proposal=original_proposal,
            candidate_command=(
                frozen_command
                if frozen_command is not None
                else candidate_command
            ),
            twin_state=twin_state,
            safety_reference=safety_reference,
            metadata=metadata,
        )

        checks = raw["checks"]

        diagnostic_failures = {
            name: not bool(checks[label]["passed"])
            for name, label in DIAGNOSTIC_CHECKS.items()
        }

        active_diagnostic_failures = sorted(
            name
            for name, failed in diagnostic_failures.items()
            if failed and name not in disabled
        )

        compromise_alarm = bool(
            active_diagnostic_failures
        )

        reference_passed = bool(
            checks["Reference_Validation"]["passed"]
        )

        authorization_passed = bool(
            checks["Authorization"]["passed"]
        )

        if not reference_passed:
            decision = "ESCALATE"
            effective_action = None
            correction_action = None
            corrected_command = None
            reason = "safety_reference_unavailable_or_invalid"
            enforcement_source = "reference_validation"

        elif action_id == "ACT09":
            decision = "ESCALATE"
            effective_action = None
            correction_action = None
            corrected_command = None
            reason = "original_agent_requested_human_escalation"
            enforcement_source = "agent_escalation"

        elif (
            "authorization" not in disabled
            and not authorization_passed
        ):
            decision = "BLOCK"
            effective_action = None
            correction_action = None
            corrected_command = None
            reason = "proposal_or_command_not_authorized"
            enforcement_source = "authorization"

        elif "action_safety" in disabled:
            if action_id not in self.actions_by_id:
                decision = "BLOCK"
                effective_action = None
                reason = "unknown_or_unsupported_proposal"
                enforcement_source = "proposal_schema"
            else:
                decision = "EXECUTE"
                effective_action = action_id
                reason = (
                    "action_safety_disabled_for_offline_ablation"
                )
                enforcement_source = "none"

            correction_action = None
            corrected_command = None

        else:
            decision = action_safety_result["decision"]
            effective_action = action_safety_result[
                "execution_candidate_action"
            ]
            correction_action = action_safety_result[
                "correction_action"
            ]
            corrected_command = action_safety_result[
                "corrected_command"
            ]
            reason = action_safety_result["decision_reason"]
            enforcement_source = (
                "action_safety"
                if decision != "EXECUTE"
                else "action_safety_confirmed"
            )

        result = deepcopy(raw)

        result.update({
            "phase": "R03C",
            "safeguard": "TRACES-DT Safeguard v3",
            "safeguard_version": "3.0",
            "compromise_alarm": compromise_alarm,
            "compromise_alarm_symbol": int(compromise_alarm),
            "diagnostic_failures": diagnostic_failures,
            "active_diagnostic_failures":
                active_diagnostic_failures,
            "decision": decision,
            "execution_candidate_action": effective_action,
            "correction_action": correction_action,
            "corrected_command": corrected_command,
            "decision_reason": reason,
            "enforcement_source": enforcement_source,
            "execute_with_alarm": (
                decision == "EXECUTE"
                and compromise_alarm
            ),
            "disabled_checks": sorted(disabled),
            "physical_execution_performed": False,
        })

        return result
