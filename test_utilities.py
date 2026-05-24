import sys
import types

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