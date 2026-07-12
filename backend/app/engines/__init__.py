"""Deterministic advisory engines — the system of record for every number.

Pure functions over FI-JSON and the config YAMLs; no I/O on the hot path, no
network, no LLM. The narrator renders these outputs into prose but can never
alter them (the determinism boundary, architecture §5).
"""
