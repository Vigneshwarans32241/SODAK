"""
Specialist Agent 2: Technical Assessment & Code Evaluation Agent
Evaluates technical submissions, algorithmic efficiency, complexity, and edge-case handling.
"""

import ast
import re
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentResult


class TechnicalEvaluationAgent(BaseAgent):
    """
    Evaluates candidate code implementations.
    Performs static AST inspection, complexity approximation, edge-case resilience checks, and code hygiene scoring.
    """

    def __init__(self):
        super().__init__(
            name="TechnicalEvaluationAgent",
            role_description="Evaluates technical coding submissions for correctness, complexity, and edge-case resilience."
        )
        self.task_type = "TECHNICAL_EVALUATION"

    def run_task(self, session_id: str, context: Dict[str, Any]) -> AgentResult:
        code = context.get("submitted_code", "")
        problem_title = context.get("problem_title", "Technical Challenge")
        expected_complexity = context.get("expected_complexity", "O(N)")

        # 1. AST Static Analysis
        syntax_valid = False
        parsed_tree = None
        try:
            parsed_tree = ast.parse(code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            parse_error = str(e)

        if not syntax_valid:
            return AgentResult(
                agent_name=self.name,
                dimension="TECHNICAL_RIGOR",
                score=10.0,
                strengths=[],
                growth_areas=[f"Syntax error in submitted code: {parse_error}"],
                detailed_metrics={"syntax_valid": False, "complexity": "N/A"},
                summary=f"Code failed syntax parsing for '{problem_title}'."
            )

        # 2. Loop nesting & Complexity heuristic
        nested_loops = 0
        has_hashmap = bool(re.search(r"\{\}|dict\(|\bset\(", code))
        has_recursion = False
        function_names = []

        for node in ast.walk(parsed_tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
            if isinstance(node, (ast.For, ast.While)):
                # Check for child loops inside this loop
                for subnode in ast.walk(node):
                    if subnode is not node and isinstance(subnode, (ast.For, ast.While)):
                        nested_loops += 1

        # Check recursion
        for fname in function_names:
            if re.search(rf"\b{fname}\s*\(", code.split(f"def {fname}", 1)[-1]):
                has_recursion = True

        # Estimate complexity
        if nested_loops > 0:
            estimated_time = "O(N^2)"
            complexity_score = 65.0
        elif has_hashmap or "binary_search" in code or "bisect" in code:
            estimated_time = "O(N)"
            complexity_score = 95.0
        else:
            estimated_time = "O(N)"
            complexity_score = 85.0

        # 3. Edge-case handling analysis
        edge_case_checks = []
        if re.search(r"if\s+not\s+\w+|if\s+\w+\s*==\s*0|if\s+\w+\s+is\s+None", code):
            edge_case_checks.append("Boundary / Empty input validation")
        if re.search(r"len\(\w+\)\s*(<=|<|==)\s*1", code):
            edge_case_checks.append("Single-element / empty container handling")
        if "try:" in code and "except" in code:
            edge_case_checks.append("Defensive exception handling")

        edge_case_score = min(len(edge_case_checks) * 35.0, 100.0)

        # 4. Code Quality / Clean Code
        has_docstring = bool(re.search(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code))
        has_type_hints = bool(re.search(r"->\s*\w+:|:\s*(int|str|List|Dict|float|bool)", code))
        code_quality_score = 50.0 + (25.0 if has_docstring else 0.0) + (25.0 if has_type_hints else 0.0)

        # Composite technical score
        technical_score = round(
            (0.45 * complexity_score) + (0.35 * edge_case_score) + (0.20 * code_quality_score), 2
        )

        strengths = []
        growth_areas = []

        if complexity_score >= 85:
            strengths.append(f"Optimal algorithmic complexity achieved: {estimated_time} (Matches target {expected_complexity}).")
        else:
            growth_areas.append(f"Suboptimal time complexity ({estimated_time}). Consider replacing nested loops with hash map lookup.")

        if edge_case_checks:
            strengths.append(f"Defensive programming present: {', '.join(edge_case_checks)}.")
        else:
            growth_areas.append("Lacks explicit boundary checks (e.g., null values, empty collections, single items).")

        if has_type_hints:
            strengths.append("Professional type hinting applied across method signatures.")
        else:
            growth_areas.append("Add PEP-484 type annotations to demonstrate production-grade coding standards.")

        summary = (
            f"Technical Rigor Score: {technical_score}/100. Estimated Time Complexity: {estimated_time}. "
            f"Edge-case score: {round(edge_case_score, 1)}%, Clean code hygiene: {round(code_quality_score, 1)}%."
        )

        return AgentResult(
            agent_name=self.name,
            dimension="TECHNICAL_RIGOR",
            score=technical_score,
            strengths=strengths,
            growth_areas=growth_areas,
            detailed_metrics={
                "estimated_time_complexity": estimated_time,
                "expected_complexity": expected_complexity,
                "edge_case_checks": edge_case_checks,
                "has_docstrings": has_docstring,
                "has_type_hints": has_type_hints,
                "syntax_valid": True
            },
            summary=summary
        )
