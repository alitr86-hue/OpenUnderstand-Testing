"""
java_parsing_helpers.py

Bridges real .java source files into real ANTLR parse-tree contexts,
so tests can feed genuine JavaParserLabeled.ClassDeclarationContext
objects into ClassTypeData instead of hand-rolled dummy/mock objects.

This module intentionally mirrors the exact parsing pipeline used by
the OpenUnderstand project itself (see openunderstand/metrics/main.py
and openunderstand/analysis_passes/extends_implicit_couple_coupleby.py):

    FileStream -> JavaLexer -> CommonTokenStream -> JavaParserLabeled
    -> compilationUnit() -> ParseTreeWalker -> Listener

Requires the real ANTLR-generated parser package (gen/javaLabeled/...)
to be present on the Python path, and antlr4-python3-runtime==4.9.1
installed (see requirements.txt).
"""

from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener

from gen.javaLabeled.JavaLexer import JavaLexer
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


class CollectingErrorListener(ErrorListener):
    """Collects ANTLR syntax errors instead of just printing them to stderr."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"line {line}:{column} {msg}")


class ClassDeclarationCollector(JavaParserLabeledListener):
    """
    Walks a real Java parse tree and records:
      - the package name (if any),
      - every top-level/nested class declaration context encountered,
      - for each class, whether it has a real 'extends' clause and,
        if so, the real superclass name straight from the source.
    """

    def __init__(self):
        self.package_name = ""
        self.class_contexts = []          # list of ClassDeclarationContext
        self.superclass_names = {}        # ctx -> superclass name (or None)

    def enterPackageDeclaration(self, ctx):
        self.package_name = ctx.getText().replace("package", "").replace(";", "")

    def enterClassDeclaration(self, ctx):
        self.class_contexts.append(ctx)
        if ctx.EXTENDS() is not None and ctx.typeType() is not None:
            self.superclass_names[ctx] = ctx.typeType().getText()
        else:
            self.superclass_names[ctx] = None


class JavaParseResult:
    """Convenience wrapper around a parsed real .java file."""

    def __init__(self, package_name, class_contexts, superclass_names, syntax_errors):
        self.package_name = package_name
        self.class_contexts = class_contexts
        self.superclass_names = superclass_names
        self.syntax_errors = syntax_errors

    @property
    def first_class_ctx(self):
        if not self.class_contexts:
            raise ValueError("No class declarations were found in this Java file.")
        return self.class_contexts[0]

    def superclass_of(self, ctx):
        return self.superclass_names.get(ctx)


def parse_java_file(file_path: str) -> JavaParseResult:
    """
    Parses a real .java file with the project's real ANTLR-generated
    JavaParserLabeled and returns every class declaration context found,
    plus any real syntax errors reported by the parser.
    """
    stream = FileStream(file_path, encoding="utf8")
    lexer = JavaLexer(stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParserLabeled(token_stream)

    error_listener = CollectingErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    tree = parser.compilationUnit()

    collector = ClassDeclarationCollector()
    walker = ParseTreeWalker()
    walker.walk(collector, tree)

    return JavaParseResult(
        package_name=collector.package_name,
        class_contexts=collector.class_contexts,
        superclass_names=collector.superclass_names,
        syntax_errors=error_listener.errors,
    )
