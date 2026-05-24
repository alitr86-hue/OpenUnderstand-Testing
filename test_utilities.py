import sys
import types

# Mock module for missing dependency
gen_module = types.ModuleType("gen")
java_module = types.ModuleType("javaLabeled")

class DummyParser:
    pass

java_module.JavaParserLabeled = DummyParser
gen_module.javaLabeled = java_module

sys.modules["gen"] = gen_module
sys.modules["gen.javaLabeled"] = java_module

from openunderstand.utils.utilities import ClassTypeData


class DummyClass:
    def getText(self):
        return "ChildClass"


def test_set_parent_class():
    obj = ClassTypeData()
    obj.set_parent_class("ParentClass")

    assert obj.parentClass == "ParentClass"


def test_set_child_class():
    obj = ClassTypeData()
    child = DummyClass()

    obj.set_child_class(child)

    assert obj.childClass == child


def test_get_long_name():
    obj = ClassTypeData()

    obj.set_package_name("com.test")
    obj.set_child_class(DummyClass())

    assert obj.get_long_name() == "com.test.ChildClass"


def test_get_type():
    obj = ClassTypeData()

    obj.set_parent_class("BaseClass")

    assert obj.get_type() == "extends BaseClass"