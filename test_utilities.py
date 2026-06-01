import sys
import types
import time
from hypothesis import given, strategies as st

# Mock missing dependency
gen_module = types.ModuleType("gen")
java_module = types.ModuleType("javaLabeled")


class DummyParser:
    pass


java_module.JavaParserLabeled = DummyParser
gen_module.javaLabeled = java_module

sys.modules["gen"] = gen_module
sys.modules["gen.javaLabeled"] = java_module

from openunderstand.utils.utilities import ClassTypeData


def test_package_name():
    obj = ClassTypeData()
    obj.set_package_name("com.example")
    assert obj.package_name == "com.example"


def test_parent_class():
    obj = ClassTypeData()
    obj.set_parent_class("Parent")
    assert obj.parentClass == "Parent"


def test_child_class():
    obj = ClassTypeData()

    class DummyChild:
        def getText(self):
            return "Child"

    obj.set_child_class(DummyChild())
    assert obj.childClass.getText() == "Child"


def test_long_name():
    obj = ClassTypeData()
    obj.set_package_name("com.test")

    class DummyChild:
        def getText(self):
            return "Child"

    obj.set_child_class(DummyChild())
    assert obj.get_long_name() == "com.test.Child"


def test_multiple_children():
    obj = ClassTypeData()

    class DummyChild:
        def getText(self):
            return "Node"

    child1 = DummyChild()
    child2 = DummyChild()

    obj.set_child_class(child1)
    obj.set_child_class(child2)

    assert obj.childClass.getText() == "Node"


def test_full_class_data():
    obj = ClassTypeData()

    obj.set_package_name("com.full")
    obj.set_parent_class("BaseParent")

    class DummyChild:
        def getText(self):
            return "FullChild"

    child = DummyChild()
    obj.set_child_class(child)

    assert obj.package_name == "com.full"
    assert obj.parentClass == "BaseParent"
    assert obj.childClass.getText() == "FullChild"
    assert obj.get_long_name() == "com.full.FullChild"


def test_replace_child_class():
    obj = ClassTypeData()

    class ChildA:
        def getText(self):
            return "A"

    class ChildB:
        def getText(self):
            return "B"

    obj.set_child_class(ChildA())
    assert obj.childClass.getText() == "A"

    obj.set_child_class(ChildB())
    assert obj.childClass.getText() == "B"


@given(st.text())
def test_package_name_property(package_name):
    """Property-based test for package name"""
    obj = ClassTypeData()
    obj.set_package_name(package_name)
    assert obj.package_name == package_name


def test_differential_behavior_validation():
    """Differential testing - comparing two instances"""
    reference_obj = ClassTypeData()
    candidate_obj = ClassTypeData()

    reference_obj.set_package_name("com.reference")
    candidate_obj.set_package_name("com.reference")

    assert reference_obj.package_name == candidate_obj.package_name


def test_performance_package_assignment():
    """Performance regression test"""
    start = time.perf_counter()

    for _ in range(10000):
        obj = ClassTypeData()
        obj.set_package_name("com.performance.test")

    end = time.perf_counter()
    execution_time = end - start

    assert execution_time < 5


def test_package_name_empty_string():
    """Test setting empty package name"""
    obj = ClassTypeData()
    obj.set_package_name("")
    assert obj.package_name == ""


def test_package_name_very_long():
    """Test setting very long package name"""
    obj = ClassTypeData()
    long_package = "com." + "example." * 50 + "app"
    obj.set_package_name(long_package)
    assert obj.package_name == long_package


def test_package_name_with_numbers():
    """Test package name with numbers"""
    obj = ClassTypeData()
    obj.set_package_name("com.example2024.module1")
    assert obj.package_name == "com.example2024.module1"


def test_parent_class_empty_string():
    """Test setting empty parent class"""
    obj = ClassTypeData()
    obj.set_parent_class("")
    assert obj.parentClass == ""


def test_parent_class_multiple_updates():
    """Test updating parent class multiple times"""
    obj = ClassTypeData()
    obj.set_parent_class("Parent1")
    assert obj.parentClass == "Parent1"
    obj.set_parent_class("Parent2")
    assert obj.parentClass == "Parent2"
    obj.set_parent_class("Parent3")
    assert obj.parentClass == "Parent3"


def test_package_name_deep_nesting():
    """Test deeply nested package names"""
    obj = ClassTypeData()
    deep_package = "org.springframework.boot.autoconfigure.web.servlet.error"
    obj.set_package_name(deep_package)
    assert obj.package_name == deep_package


def test_independent_instances():
    """Test that multiple instances don't interfere"""
    obj1 = ClassTypeData()
    obj2 = ClassTypeData()

    obj1.set_package_name("com.instance1")
    obj2.set_package_name("com.instance2")

    assert obj1.package_name == "com.instance1"
    assert obj2.package_name == "com.instance2"


def test_parent_class_special_characters():
    """Test parent class with special characters"""
    obj = ClassTypeData()
    obj.set_parent_class("Parent$Class_123")
    assert obj.parentClass == "Parent$Class_123"


def test_multiple_sequential_operations():
    """Test multiple sequential operations on same object"""
    obj = ClassTypeData()

    obj.set_package_name("com.first")
    assert obj.package_name == "com.first"

    obj.set_package_name("com.second")
    assert obj.package_name == "com.second"

    obj.set_parent_class("ParentClass")
    assert obj.parentClass == "ParentClass"

    class DummyChild:
        def getText(self):
            return "ChildClass"

    obj.set_child_class(DummyChild())
    assert obj.childClass.getText() == "ChildClass"

    long_name = obj.get_long_name()
    assert "ChildClass" in long_name


def test_child_class_none():
    """Test getting child class when none set"""
    obj = ClassTypeData()
    if hasattr(obj, 'childClass'):
        result = obj.childClass
        assert result is None or hasattr(result, 'getText')


def test_long_name_without_package():
    """Test long name when package is not set"""
    obj = ClassTypeData()

    class DummyChild:
        def getText(self):
            return "OnlyChild"

    obj.set_child_class(DummyChild())
    long_name = obj.get_long_name()
    assert "OnlyChild" in long_name


def test_long_name_empty_package():
    """Test long name with empty package"""
    obj = ClassTypeData()
    obj.set_package_name("")

    class DummyChild:
        def getText(self):
            return "TestClass"

    obj.set_child_class(DummyChild())
    long_name = obj.get_long_name()
    assert "TestClass" in long_name