import time

class ClassTypeData:
    def __init__(self):
        self.parentClass = None
        self.childClass = None
        self.file_path: str = ""
        self.package_name: str = ""
        self.line: int = -1
        self.column: int = -1
        self.prefixes: list = []

    def set_child_class(self, child):
        self.childClass = child

    def set_parent_class(self, parent):
        self.parentClass = parent

    def set_file_path(self, file_path: str):
        self.file_path = file_path

    def set_package_name(self, name: str):
        self.package_name = name

    def set_line(self, line: int):
        self.line = line

    def set_column(self, column: int):
        self.column = column

    def set_prefixes(self, prefix_list: list):
        self.prefixes = prefix_list

    def get_long_name(self) -> str:
        return self.package_name + "." + self.childClass.getText()

    def get_type(self) -> str:
        return "extends" + " " + self.parentClass

    def get_name(self) -> str:
        return str(self.childClass.IDENTIFIER())

    def get_contents(self) -> str:
        return self.childClass.getText()

    def get_prefixes(self) -> list:
        return self.prefixes