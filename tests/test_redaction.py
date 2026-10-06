from __future__ import annotations

from gsa_compliance_robot.redaction import RedactionListener, register_secret


class TestScrubDefaultPatterns:
    def setup_method(self):
        # Reset class-level state between tests so registrations don't leak.
        RedactionListener._extra_literals.clear()
        RedactionListener._extra_patterns.clear()

    def test_masks_github_classic_pat(self):
        text = "token=ghp_" + "a" * 36
        assert "ghp_" not in RedactionListener._scrub(text)
        assert "***REDACTED***" in RedactionListener._scrub(text)

    def test_masks_github_app_tokens(self):
        for prefix in ("ghu_", "ghs_", "ghr_"):
            text = f"{prefix}" + "b" * 25
            scrubbed = RedactionListener._scrub(text)
            assert prefix not in scrubbed

    def test_masks_fine_grained_pat(self):
        text = "github_pat_" + "c" * 25
        scrubbed = RedactionListener._scrub(text)
        assert "github_pat_" not in scrubbed

    def test_masks_jwt(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        scrubbed = RedactionListener._scrub(f"Authorization: Bearer {jwt}")
        assert jwt not in scrubbed

    def test_masks_bearer_header_preserving_prefix(self):
        text = "Bearer " + "x" * 30
        scrubbed = RedactionListener._scrub(text)
        assert scrubbed.startswith("Bearer ")
        assert "x" * 30 not in scrubbed

    def test_masks_aws_access_key(self):
        text = "AKIA" + "A" * 16
        scrubbed = RedactionListener._scrub(text)
        assert "AKIA" not in scrubbed

    def test_leaves_safe_text_untouched(self):
        text = "This is a perfectly safe log line with no secrets."
        assert RedactionListener._scrub(text) == text

    def test_non_string_input_passed_through(self):
        assert RedactionListener._scrub(None) is None
        assert RedactionListener._scrub(123) == 123


class TestRegisterSecret:
    def setup_method(self):
        RedactionListener._extra_literals.clear()
        RedactionListener._extra_patterns.clear()

    def test_registers_and_masks_literal(self):
        register_secret("supersecretvalue123")
        scrubbed = RedactionListener._scrub("the value is supersecretvalue123 here")
        assert "supersecretvalue123" not in scrubbed

    def test_short_values_not_registered(self):
        register_secret("short")
        assert "short" not in RedactionListener._extra_literals

    def test_empty_value_not_registered(self):
        register_secret("")
        assert len(RedactionListener._extra_literals) == 0

    def test_instance_register_secret_keyword(self):
        listener = RedactionListener()
        listener.register_secret("anotherlongsecretvalue")
        scrubbed = RedactionListener._scrub("prefix anotherlongsecretvalue suffix")
        assert "anotherlongsecretvalue" not in scrubbed


class TestRegisterPattern:
    def setup_method(self):
        RedactionListener._extra_literals.clear()
        RedactionListener._extra_patterns.clear()

    def test_custom_pattern_is_masked(self):
        listener = RedactionListener()
        listener.register_pattern(r"CUSTOM-[0-9]{6}")
        scrubbed = RedactionListener._scrub("ticket id CUSTOM-123456 reported")
        assert "CUSTOM-123456" not in scrubbed

    def test_duplicate_pattern_not_added_twice(self):
        listener = RedactionListener()
        listener.register_pattern(r"DUP-[0-9]+")
        listener.register_pattern(r"DUP-[0-9]+")
        assert len(RedactionListener._extra_patterns) == 1
