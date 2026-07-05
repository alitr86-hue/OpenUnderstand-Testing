"""
test_utilities.py — Industrial-grade tests for ClassTypeData (openunderstand.utils.utilities)

Reviewer feedback addressed (PR #72, m-zakeri):
  "I do not see any real test data. Here, the test data are Java projects."
  "Use specific tests containing Java projects to test a reference kind
   or entity kind completely."
  "There is no real test data here!"

Fix: every test that exercises `childClass` now feeds ClassTypeData a REAL
ClassDeclarationContext produced by parsing a REAL .java file with the
project's actual ANTLR-generated parser (gen/javaLabeled/JavaParserLabeled),
via the ParseTreeWalker/Listener pipeline the project itself uses in
openunderstand/analysis_passes/extends_implicit_couple_coupleby.py and
openunderstand/metrics/main.py. No hand-rolled dummy objects remain for
anything that models parsed Java source.

Java fixtures live in test_data/java_samples/ and cover:
  - a normal class with no superclass          (SimpleClass.java)
  - a normal class with a real 'extends'       (AnimalDog.java)
  - a generic class                            (GenericBox.java)
  - extends + implements together              (CalculatorImpl.java)
  - a class with no package declaration        (NoPackageClass.java)
  - two classes in one file / parent-child use  (MultiClassFile.java)
  - a syntactically malformed file              (MalformedClass.java)
"""

import os
import sys
import time

import pytest
from hypothesis import given, strategies as st

# Make the real ANTLR-generated parser importable exactly the way the
# project itself imports it ("from gen.javaLabeled... import ...").
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_OPENUNDERSTAND_PKG_DIR = os.path.join(_PROJECT_ROOT, "openunderstand")
for _p in (_PROJECT_ROOT, _OPENUNDERSTAND_PKG_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from openunderstand.utils.utilities import ClassTypeData
from java_parsing_helpers import parse_java_file

JAVA_SAMPLES_DIR = os.path.join(_PROJECT_ROOT, "test_data", "java_samples")


def java_sample(filename: str) -> str:
    return os.path.join(JAVA_SAMPLES_DIR, filename)


# ---------------------------------------------------------------------------
# Normal behavior — real Java source, no inheritance
# ---------------------------------------------------------------------------

def test_class_declaration_from_real_java_file():
    """A real class parsed from a real .java file yields correct name/contents."""
    result = parse_java_file(java_sample("SimpleClass.java"))
    ctx = result.first_class_ctx

    obj = ClassTypeData()
    obj.set_package_name(result.package_name)
    obj.set_child_class(ctx)

    assert obj.get_name() == "SimpleClass"
    assert "value" in obj.get_contents()


def test_long_name_uses_full_class_body_not_just_identifier():
    """
    FAULT DISCOVERED VIA REAL TEST DATA (reported in Part 6):

    get_long_name() is implemented as
        self.package_name + "." + self.childClass.getText()
    but ctx.getText() returns the ENTIRE class body text (Java source with
    whitespace stripped), not just the class identifier. With the old
    DummyChild mock (getText() -> "Child"), this bug was invisible because
    the mock happened to return a short, identifier-like string. With a
    REAL parsed class it is obvious: get_long_name() does NOT return a
    normal qualified name at all.

    This test documents the ACTUAL (buggy) behavior so a regression is
    caught, and demonstrates exactly the failure mode the code reviewer
    was trying to prevent by rejecting mock-based test data.
    """
    result = parse_java_file(java_sample("GenericBox.java"))
    ctx = result.first_class_ctx

    obj = ClassTypeData()
    obj.set_package_name(result.package_name)
    obj.set_child_class(ctx)

    long_name = obj.get_long_name()
    expected_qualified_name = "com.example.util.Box"

    assert long_name == "com.example.util." + ctx.getText()
    assert long_name != expected_qualified_name
    assert long_name.startswith("com.example.util.classBox")


# ---------------------------------------------------------------------------
# Parent-child / inheritance relationships (the "reference kind" the
# reviewer specifically asked to see fully exercised)
# ---------------------------------------------------------------------------

def test_extends_reference_from_real_java_file():
    """AnimalDog.java really contains 'class Dog extends Animal' — verify it end to end."""
    result = parse_java_file(java_sample("AnimalDog.java"))
    ctx = result.first_class_ctx
    real_superclass = result.superclass_of(ctx)

    obj = ClassTypeData()
    obj.set_package_name(result.package_name)
    obj.set_child_class(ctx)
    obj.set_parent_class(real_superclass)

    assert real_superclass == "Animal"
    assert obj.get_name() == "Dog"
    assert obj.get_type() == "extends Animal"
    # NOTE: get_long_name() does not return a clean qualified name (see the
    # dedicated fault-documentation test); it embeds the full class body.
    assert obj.get_long_name().startswith("com.example.zoo.classDog")


def test_extends_and_implements_together():
    """CalculatorImpl.java extends AbstractCalculator AND implements Operable."""
    result = parse_java_file(java_sample("CalculatorImpl.java"))
    ctx = result.first_class_ctx
    real_superclass = result.superclass_of(ctx)

    obj = ClassTypeData()
    obj.set_package_name(result.package_name)
    obj.set_child_class(ctx)
    obj.set_parent_class(real_superclass)

    assert real_superclass == "AbstractCalculator"
    assert obj.get_type() == "extends AbstractCalculator"
    assert obj.get_name() == "CalculatorImpl"


def test_no_extends_clause_has_no_real_superclass():
    """SimpleClass.java has no 'extends' at all — the parser must report that honestly."""
    result = parse_java_file(java_sample("SimpleClass.java"))
    ctx = result.first_class_ctx

    assert result.superclass_of(ctx) is None


def test_parent_child_relationship_across_two_real_classes():
    """
    MultiClassFile.java contains two real classes in one file:
    'Helper' and 'MainClass extends Helper'. Validate the relationship
    using the actual parsed contexts for BOTH classes, not stand-ins.
    """
    result = parse_java_file(java_sample("MultiClassFile.java"))
    assert len(result.class_contexts) == 2

    helper_ctx, main_ctx = result.class_contexts

    helper_data = ClassTypeData()
    helper_data.set_package_name(result.package_name)
    helper_data.set_child_class(helper_ctx)

    main_data = ClassTypeData()
    main_data.set_package_name(result.package_name)
    main_data.set_child_class(main_ctx)
    main_data.set_parent_class(result.superclass_of(main_ctx))

    assert helper_data.get_name() == "Helper"
    assert main_data.get_name() == "MainClass"
    assert main_data.get_type() == "extends Helper"
    assert main_data.parentClass == helper_data.get_name()


# ---------------------------------------------------------------------------
# Edge cases with real (but unusual) Java source
# ---------------------------------------------------------------------------

def test_class_with_no_package_declaration():
    """NoPackageClass.java has no 'package' line at all — a real, valid edge case."""
    result = parse_java_file(java_sample("NoPackageClass.java"))
    ctx = result.first_class_ctx

    obj = ClassTypeData()
    obj.set_package_name(result.package_name)  # will be ""
    obj.set_child_class(ctx)

    assert result.package_name == ""
    assert obj.get_name() == "NoPackageClass"
    # get_long_name concatenates package + "." + full class body text even
    # when the package is empty, per the current (buggy) implementation.
    assert obj.get_long_name().startswith(".classNoPackageClass")


def test_generic_class_identifier_ignores_type_parameters():
    """Box<T> — IDENTIFIER() must return just 'Box', not 'Box<T>'."""
    result = parse_java_file(java_sample("GenericBox.java"))
    ctx = result.first_class_ctx

    obj = ClassTypeData()
    obj.set_child_class(ctx)

    assert obj.get_name() == "Box"


# ---------------------------------------------------------------------------
# Malformed / unresolved input — the reviewer explicitly asked for this
# ---------------------------------------------------------------------------

def test_malformed_java_file_reports_real_syntax_errors():
    """
    MalformedClass.java is missing a semicolon and a closing brace.
    The real parser must surface real syntax errors instead of silently
    producing a well-formed-looking tree.
    """
    result = parse_java_file(java_sample("MalformedClass.java"))

    assert len(result.syntax_errors) > 0
    assert any("no viable alternative" in e or "extraneous input" in e
               for e in result.syntax_errors)


def test_malformed_java_file_class_identifier_still_recoverable():
    """
    Even with syntax errors elsewhere in the file, ANTLR's error recovery
    still lets us retrieve the class name that WAS parsed correctly —
    this documents the tool's actual (partial) recovery behavior rather
    than assuming a crash.
    """
    result = parse_java_file(java_sample("MalformedClass.java"))
    ctx = result.first_class_ctx

    obj = ClassTypeData()
    obj.set_child_class(ctx)

    assert obj.get_name() == "MalformedClass"


def test_unresolved_superclass_name_is_still_captured_as_text():
    """
    OpenUnderstand does not resolve 'Animal' to a compiled type (no
    classpath/semantic resolution) — it only has the token text. This
    test documents that an unresolved/unknown superclass is still
    captured faithfully as raw text, which is the correct and expected
    behavior for a lexical/syntactic analysis tool.
    """
    result = parse_java_file(java_sample("AnimalDog.java"))
    ctx = result.first_class_ctx

    # "Animal" is never defined anywhere in this project — it is an
    # unresolved/unknown entity from OpenUnderstand's point of view.
    assert result.superclass_of(ctx) == "Animal"


# ---------------------------------------------------------------------------
# Independent-instance / multi-pass style checks, now using real contexts
# ---------------------------------------------------------------------------

def test_independent_instances_with_real_contexts():
    """Two ClassTypeData instances fed from two different real files don't interfere."""
    result_a = parse_java_file(java_sample("SimpleClass.java"))
    result_b = parse_java_file(java_sample("AnimalDog.java"))

    obj_a = ClassTypeData()
    obj_a.set_package_name(result_a.package_name)
    obj_a.set_child_class(result_a.first_class_ctx)

    obj_b = ClassTypeData()
    obj_b.set_package_name(result_b.package_name)
    obj_b.set_child_class(result_b.first_class_ctx)

    assert obj_a.get_name() == "SimpleClass"
    assert obj_b.get_name() == "Dog"
    assert obj_a.get_long_name() != obj_b.get_long_name()


def test_replace_child_class_with_two_real_classes():
    """set_child_class can be re-pointed from one real parsed class to another."""
    result = parse_java_file(java_sample("MultiClassFile.java"))
    helper_ctx, main_ctx = result.class_contexts

    obj = ClassTypeData()
    obj.set_child_class(helper_ctx)
    assert obj.get_name() == "Helper"

    obj.set_child_class(main_ctx)
    assert obj.get_name() == "MainClass"


def test_multi_pass_reparse_is_stable():
    """Parsing the same real file twice (simulating a second analysis pass)
    must yield equivalent results both times."""
    first_pass = parse_java_file(java_sample("CalculatorImpl.java"))
    second_pass = parse_java_file(java_sample("CalculatorImpl.java"))

    assert first_pass.first_class_ctx.getText() == second_pass.first_class_ctx.getText()
    assert first_pass.package_name == second_pass.package_name


# ---------------------------------------------------------------------------
# Field-level unit tests (no Java source involved — these were already
# testing plain Python attribute assignment correctly, so they're kept)
# ---------------------------------------------------------------------------

def test_package_name():
    obj = ClassTypeData()
    obj.set_package_name("com.example")
    assert obj.package_name == "com.example"


def test_parent_class():
    obj = ClassTypeData()
    obj.set_parent_class("Parent")
    assert obj.parentClass == "Parent"


@given(st.text())
def test_package_name_property(package_name):
    """Property-based test for package name (Hypothesis)."""
    obj = ClassTypeData()
    obj.set_package_name(package_name)
    assert obj.package_name == package_name


def test_differential_behavior_validation():
    """Differential testing — two instances fed the SAME real class must agree."""
    result = parse_java_file(java_sample("SimpleClass.java"))
    ctx = result.first_class_ctx

    reference_obj = ClassTypeData()
    reference_obj.set_package_name(result.package_name)
    reference_obj.set_child_class(ctx)

    candidate_obj = ClassTypeData()
    candidate_obj.set_package_name(result.package_name)
    candidate_obj.set_child_class(ctx)

    assert reference_obj.get_long_name() == candidate_obj.get_long_name()
    assert reference_obj.get_name() == candidate_obj.get_name()


def test_performance_package_assignment():
    """Performance regression test."""
    start = time.perf_counter()
    for _ in range(10000):
        obj = ClassTypeData()
        obj.set_package_name("com.performance.test")
    end = time.perf_counter()
    assert (end - start) < 5


def test_package_name_empty_string():
    obj = ClassTypeData()
    obj.set_package_name("")
    assert obj.package_name == ""


def test_package_name_very_long():
    obj = ClassTypeData()
    long_package = "com." + "example." * 50 + "app"
    obj.set_package_name(long_package)
    assert obj.package_name == long_package


def test_parent_class_multiple_updates():
    obj = ClassTypeData()
    obj.set_parent_class("Parent1")
    assert obj.parentClass == "Parent1"
    obj.set_parent_class("Parent2")
    assert obj.parentClass == "Parent2"


def test_prefixes_setter_and_getter():
    obj = ClassTypeData()
    obj.set_prefixes(["public", "static"])
    assert obj.get_prefixes() == ["public", "static"]


def test_line_and_column_from_real_context():
    """set_line/set_column normally come from ctx.start.line — verify with real data."""
    result = parse_java_file(java_sample("AnimalDog.java"))
    ctx = result.first_class_ctx

    obj = ClassTypeData()
    obj.set_line(ctx.start.line)
    obj.set_column(ctx.start.column)

    assert obj.line == ctx.start.line
    assert obj.line > 0
    assert obj.column >= 0
