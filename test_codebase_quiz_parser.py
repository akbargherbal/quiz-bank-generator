# test_codebase_quiz_parser.py

import pytest
import pandas as pd
import sys
from io import StringIO
import re
from contextlib import redirect_stdout
import io

# Import the specific function to test
# Ensure fixed_quiz_parser.py is in the Python path or same directory
try:
    # Assuming the new function is added to fixed_quiz_parser.py
    from fixed_quiz_parser import parse_codebase_quiz_xml_to_dataframe
except ImportError:
    print(
        "Error: Could not import 'parse_codebase_quiz_xml_to_dataframe' from 'fixed_quiz_parser'."
    )
    print("Make sure the function exists in fixed_quiz_parser.py and the file is accessible.")
    sys.exit(1)


class TestCodebaseQuizParser:

    def test_basic_parsing_with_path(self):
        """Test parsing simple XML with QUESTION, OPTIONS, TOPIC, TAG, and PATH."""
        xml = """
        <QUIZ_BANK topic="Basic Codebase Test">
        <QUIZ_ITEM>
        <QUESTION>What is `git status`?</QUESTION>
        <OPTION1 correct="true">Shows working tree status</OPTION1>
        <OPTION2 correct="false">Commits changes</OPTION2>
        <OPTION3 correct="false">Pushes changes</OPTION3>
        <OPTION4 correct="false">Pulls changes</OPTION4>
        <OPTION5 correct="false">Creates a branch</OPTION5>
        <TOPIC>Version Control</TOPIC>
        <TAG>Git Basics</TAG>
        <PATH>src/utils/git_helpers.py</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        # Verify structure and content including path
        assert len(df) == 1, "Should have parsed 1 question"
        assert "path" in df.columns, "DataFrame should have a 'path' column"
        assert df.iloc[0]["text"] == "What is `git status`?", "Question text mismatch"
        assert len(df.iloc[0]["options"]) == 5, "Should have 5 options"
        assert df.iloc[0]["answerIndex"] == 1, "Answer index should be 1"
        assert df.iloc[0]["topic"] == "Version Control", "Topic mismatch"
        assert df.iloc[0]["tag"] == "Git Basics", "Tag mismatch"
        assert df.iloc[0]["path"] == "src/utils/git_helpers.py", "Path mismatch"
        assert "Skipped 0 questions" in f.getvalue(), "No questions should be skipped"

    def test_parsing_item_missing_path(self):
        """Test parsing an item missing the PATH element."""
        xml = """
        <QUIZ_BANK topic="Missing Path Test">
        <QUIZ_ITEM>
        <QUESTION>Question without path?</QUESTION>
        <OPTION1 correct="true">Yes</OPTION1>
        <OPTION2 correct="false">No</OPTION2>
        <OPTION3 correct="false">Maybe</OPTION3>
        <OPTION4 correct="false">Maybe Not</OPTION4>
        <OPTION5 correct="false">Definitely Not</OPTION5>
        <TOPIC>Structure Test</TOPIC>
        <TAG>Missing Element</TAG>
        <!-- No PATH element -->
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 1, "Should have parsed 1 question"
        assert "path" in df.columns, "DataFrame should have a 'path' column"
        assert df.iloc[0]["path"] == "", "Path should be empty string when missing"
        assert "missing the <PATH> element" in output, "Should log warning about missing PATH"
        assert "Skipped 0 questions" in output, "Should not skip for missing PATH"

    def test_html_content_with_path(self):
        """Test parsing questions with HTML code blocks and a PATH."""
        xml = """
        <QUIZ_BANK topic="Code Blocks">
        <QUIZ_ITEM>
        <QUESTION>
        What does this Python code do?
        <pre><code class="language-python">
        def greet(name):
            print(f"Hello, {name}!")
        </code></pre>
        Related to <code>main.py</code>.
        </QUESTION>
        <OPTION1 correct="true">Defines a function to greet someone</OPTION1>
        <OPTION2 correct="false">Prints "Hello, name!"</OPTION2>
        <OPTION3 correct="false">Causes a syntax error</OPTION3>
        <OPTION4 correct="false">Defines a class</OPTION4>
        <OPTION5 correct="false">Imports a module</OPTION5>
        <TOPIC>Python Functions</TOPIC>
        <TAG>Function Definition</TAG>
        <PATH>src/app/main.py</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        # Verify HTML preservation and path
        assert len(df) == 1, "Should have parsed 1 question"
        assert "<pre><code" in df.iloc[0]["text"], "HTML block should be preserved"
        assert "<code>main.py</code>" in df.iloc[0]["text"], "Inline HTML preserved"
        assert df.iloc[0]["path"] == "src/app/main.py", "Path mismatch"
        assert "Skipped 0 questions" in f.getvalue()

    def test_case_insensitivity(self):
        """Test parsing with lowercase and mixed-case tags."""
        xml = """
        <quiz_bank topic="Case Test">
        <quiz_item>
        <QUESTION>Case insensitive parsing?</QUESTION>
        <option1 correct="True">Yes</option1> <!-- Mixed case attribute value -->
        <option2 correct="false">no</option2>
        <OPTION3 correct="False">maybe</OPTION3> <!-- Mixed case tag -->
        <option4 correct="false">sometimes</option4>
        <option5 correct="false">never</option5>
        <Topic>XML Parsing</Topic> <!-- Mixed case tag -->
        <tag>Robustness</tag>
        <path>src/parser/core.py</path>
        </quiz_item>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 1, "Should parse 1 question with mixed case tags"
        assert df.iloc[0]["text"] == "Case insensitive parsing?", "Question text mismatch"
        assert df.iloc[0]["topic"] == "XML Parsing", "Topic mismatch"
        assert df.iloc[0]["tag"] == "Robustness", "Tag mismatch"
        assert df.iloc[0]["path"] == "src/parser/core.py", "Path mismatch"
        # Check for potential warnings about correct attributes due to case, but should parse
        # assert "correct='true' attribute" not in output # This might be too strict depending on warning logic
        assert "Skipped 0 questions" in output

    def test_rejects_item_with_too_few_options(self):
        """Test parser rejects item with < 5 options."""
        xml = """
        <QUIZ_BANK topic="Missing Options Test">
        <QUIZ_ITEM>
        <QUESTION>Too few options?</QUESTION>
        <OPTION1 correct="true">Yes</OPTION1>
        <OPTION2 correct="false">No</OPTION2>
        <OPTION3 correct="false">Maybe</OPTION3>
        <OPTION4 correct="false">Perhaps</OPTION4>
        <!-- Missing OPTION5 -->
        <TOPIC>Invalid Structure</TOPIC>
        <TAG>Option Count Error</TAG>
        <PATH>src/test/invalid.py</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 0, "DataFrame should be empty"
        assert (
            "Expected 5 options but found 4" in output
        ), "Should log error about option count"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_rejects_item_with_too_many_options(self):
        """Test parser rejects item with > 5 options."""
        xml = """
        <QUIZ_BANK topic="Too Many Options Test">
        <QUIZ_ITEM>
        <QUESTION>Too many options?</QUESTION>
        <OPTION1 correct="true">A</OPTION1>
        <OPTION2 correct="false">B</OPTION2>
        <OPTION3 correct="false">C</OPTION3>
        <OPTION4 correct="false">D</OPTION4>
        <OPTION5 correct="false">E</OPTION5>
        <OPTION6 correct="false">F</OPTION6> <!-- Extra option -->
        <TOPIC>Invalid Structure</TOPIC>
        <TAG>Option Count Error</TAG>
        <PATH>src/test/invalid.py</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 0, "DataFrame should be empty"
        assert (
            "Expected 5 options but found 6" in output
        ), "Should log error about option count"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_rejects_item_with_non_sequential_options(self):
        """Test parser rejects item with 5 options but wrong numbers (e.g., duplicates)."""
        xml = """
        <QUIZ_BANK topic="Non-Sequential Options Test">
        <QUIZ_ITEM>
        <QUESTION>Duplicate or wrong option numbers?</QUESTION>
        <OPTION1 correct="true">A</OPTION1>
        <OPTION2 correct="false">B</OPTION2>
        <OPTION2 correct="false">C</OPTION2> <!-- Duplicate OPTION2 -->
        <OPTION4 correct="false">D</OPTION4>
        <OPTION5 correct="false">E</OPTION5>
        <TOPIC>Invalid Structure</TOPIC>
        <TAG>Option Number Error</TAG>
        <PATH>src/test/invalid_options.py</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 0, "DataFrame should be empty"
        # The exact error message might depend on which check fails first (count vs. numbers)
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"
        # Check for a message indicating the numbers weren't 1-5
        assert "not exactly OPTION1-5" in output or "Expected 5 options" in output


    def test_parses_valid_skips_invalid(self):
        """Test parsing multiple items, skipping invalid ones."""
        xml = """
        <QUIZ_BANK topic="Mixed Validity Test">
        <QUIZ_ITEM>
        <QUESTION>Valid Question 1</QUESTION>
        <OPTION1 correct="true">Correct</OPTION1>
        <OPTION2 correct="false">W1</OPTION2>
        <OPTION3 correct="false">W2</OPTION3>
        <OPTION4 correct="false">W3</OPTION4>
        <OPTION5 correct="false">W4</OPTION5>
        <TOPIC>Valid</TOPIC>
        <TAG>First</TAG>
        <PATH>src/valid/one.py</PATH>
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Invalid Question (Too few options)</QUESTION>
        <OPTION1 correct="true">A</OPTION1>
        <OPTION2 correct="false">B</OPTION2>
        <TOPIC>Invalid</TOPIC>
        <TAG>Error</TAG>
        <PATH>src/invalid/two.py</PATH>
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Valid Question 2 (Missing Path)</QUESTION>
        <OPTION1 correct="true">Yes</OPTION1>
        <OPTION2 correct="false">No</OPTION2>
        <OPTION3 correct="false">Maybe</OPTION3>
        <OPTION4 correct="false">Maybe Not</OPTION4>
        <OPTION5 correct="false">Okay</OPTION5>
        <TOPIC>Valid</TOPIC>
        <TAG>Second</TAG>
        <!-- No Path -->
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 2, "Should have parsed 2 valid questions"
        assert df.iloc[0]["text"] == "Valid Question 1"
        assert df.iloc[0]["path"] == "src/valid/one.py"
        assert df.iloc[1]["text"] == "Valid Question 2 (Missing Path)"
        assert df.iloc[1]["path"] == ""
        assert (
            "Expected 5 options but found 2" in output
        ), "Should log error about invalid item"
        assert "missing the <PATH> element" in output, "Should log warning about missing path"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"


    def test_malformed_xml_recovery_with_path(self):
        """Test recovery from slightly malformed XML."""
        # Malformed: Missing closing </QUIZ_ITEM> tag, but content might be recoverable by lxml
        xml = """
        <QUIZ_BANK topic="Malformed XML Recovery">
        <QUIZ_ITEM>
            <QUESTION>Can this be recovered?</QUESTION>
            <OPTION1 correct="true">Hope so</OPTION1>
            <OPTION2 correct="false">Nope</OPTION2>
            <OPTION3 correct="false">Maybe</OPTION3>
            <OPTION4 correct="false">Doubtful</OPTION4>
            <OPTION5 correct="false">50/50</OPTION5>
            <TOPIC>Parsing</TOPIC>
            <TAG>Recovery</TAG>
            <PATH>src/recovery/test.xml</PATH>
        <!-- Missing closing </QUIZ_ITEM> tag -->
        <QUIZ_ITEM>
            <QUESTION>Second item ok?</QUESTION>
            <OPTION1 correct="true">Yes</OPTION1>
            <OPTION2 correct="false">No</OPTION2>
            <OPTION3 correct="false">Maybe</OPTION3>
            <OPTION4 correct="false">Maybe Not</OPTION4>
            <OPTION5 correct="false">Okay</OPTION5>
            <TOPIC>Parsing</TOPIC>
            <TAG>Second Item</TAG>
            <PATH>src/recovery/test2.xml</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            # lxml's recover=True should attempt to handle this
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        # Recovery behavior can be complex. Check if at least the second, well-formed item parses.
        # The first one might or might not be recovered depending on lxml's strategy.
        # A less brittle test might check that *at least one* item is parsed.
        assert len(df) >= 1, "Should parse at least one question despite malformed XML"
        if len(df) > 0:
            # Check the path of the successfully parsed item(s)
             assert all(p.startswith("src/recovery/") for p in df["path"] if p), "Path check on recovered items"
        # Check stdout for parser errors/warnings if needed
        # print(f.getvalue()) # Uncomment to debug parser output


    def test_empty_xml_input(self):
        """Test parsing an empty string."""
        xml = ""
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert df.empty, "DataFrame should be empty for empty input"
        assert "Input XML content was empty" in output, "Should warn about empty input"


    def test_xml_with_no_items(self):
        """Test parsing XML with QUIZ_BANK but no QUIZ_ITEMs."""
        xml = """
        <QUIZ_BANK topic="Empty Bank Test">
        <!-- No items here -->
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert df.empty, "DataFrame should be empty"
        assert "No <QUIZ_ITEM> elements found" in output, "Should warn about no items"
        assert "Skipped 0 questions" in output # No items were processed/skipped


    def test_attribute_checks(self):
        """Test warnings for incorrect 'correct' attributes."""
        xml = """
        <QUIZ_BANK topic="Attribute Check">
        <QUIZ_ITEM>
        <QUESTION>Option 1 missing correct='true'</QUESTION>
        <OPTION1 correct="false">Wrong attr</OPTION1> <!-- Incorrect -->
        <OPTION2 correct="false">Ok</OPTION2>
        <OPTION3 correct="false">Ok</OPTION3>
        <OPTION4 correct="false">Ok</OPTION4>
        <OPTION5 correct="false">Ok</OPTION5>
        <TOPIC>Attributes</TOPIC>
        <TAG>Correctness</TAG>
        <PATH>path1.py</PATH>
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Option 2 missing correct='false'</QUESTION>
        <OPTION1 correct="true">Ok</OPTION1>
        <OPTION2 correct="true">Wrong attr</OPTION2> <!-- Incorrect -->
        <OPTION3 correct="false">Ok</OPTION3>
        <OPTION4 correct="false">Ok</OPTION4>
        <OPTION5 correct="false">Ok</OPTION5>
        <TOPIC>Attributes</TOPIC>
        <TAG>Correctness</TAG>
        <PATH>path2.py</PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 2, "Should still parse both questions"
        assert "Warning: OPTION1" in output and "missing or incorrect correct='true'" in output
        assert "Warning: OPTION2" in output and "missing or incorrect correct='false'" in output
        assert "Skipped 0 questions" in output # Warnings don't cause skips


    def test_whitespace_in_path(self):
        """Test that leading/trailing whitespace is trimmed from PATH content."""
        xml = """
        <QUIZ_BANK topic="Whitespace Test">
        <QUIZ_ITEM>
        <QUESTION>Path with whitespace?</QUESTION>
        <OPTION1 correct="true">Trimmed</OPTION1>
        <OPTION2 correct="false">Kept</OPTION2>
        <OPTION3 correct="false">Error</OPTION3>
        <OPTION4 correct="false">None</OPTION4>
        <OPTION5 correct="false">Maybe</OPTION5>
        <TOPIC>Parsing Details</TOPIC>
        <TAG>Whitespace Trim</TAG>
        <PATH>  src/whitespace/test.py  </PATH>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_codebase_quiz_xml_to_dataframe(xml)

        assert len(df) == 1, "Should parse 1 question"
        assert df.iloc[0]["path"] == "src/whitespace/test.py", "Whitespace should be trimmed from path"


# Run the tests if the script is executed directly
if __name__ == "__main__":
    print("Running tests for parse_codebase_quiz_xml_to_dataframe using pytest.main()...")
    # Run tests in the current file
    pytest.main(["-v", __file__])