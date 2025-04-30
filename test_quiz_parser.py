import pytest
import pandas as pd
import sys
from io import StringIO, BytesIO  # Use BytesIO for etree.parse with parser
import re
from pathlib import Path
from lxml import etree  # Import etree for direct use if needed

# Import the module to test
# Ensure fixed_quiz_parser.py is in the Python path or same directory
sys.path.append(".")
try:
    from fixed_quiz_parser import parse_quiz_xml_to_dataframe, enhance_quiz_dataframe
except ImportError:
    print("Error: Could not import 'fixed_quiz_parser'. Make sure it's in the path.")
    sys.exit(1)


# Helper to capture stdout
from contextlib import redirect_stdout
import io


class TestQuizParser:

    def test_basic_parsing_with_tag(self):
        """Test parsing simple XML with a TAG element."""
        xml = """
        <QUIZ_BANK topic="Basic Test">
        <QUIZ_ITEM>
        <QUESTION>What is 2+2?</QUESTION>
        <OPTION1 correct="true">4</OPTION1>
        <OPTION2 correct="false">3</OPTION2>
        <OPTION3 correct="false">5</OPTION3>
        <OPTION4 correct="false">22</OPTION4>
        <OPTION5 correct="false">None of the above</OPTION5>
        <TOPIC>Arithmetic</TOPIC>
        <TAG>Basic Math</TAG>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify structure and content including tag
        assert len(df) == 1, "Should have parsed 1 question"
        assert "tag" in df.columns, "DataFrame should have a 'tag' column"
        assert df.iloc[0]["text"] == "What is 2+2?", "Question text mismatch"
        assert len(df.iloc[0]["options"]) == 5, "Should have 5 options"
        assert df.iloc[0]["answerIndex"] == 1, "Answer index should be 1"
        assert df.iloc[0]["topic"] == "Arithmetic", "Topic should be 'Arithmetic'"
        assert df.iloc[0]["tag"] == "Basic Math", "Tag should be 'Basic Math'"
        assert "Skipped 0 questions" in f.getvalue(), "No questions should be skipped"

    def test_basic_parsing_without_tag(self):
        """Test parsing simple XML without a TAG element."""
        xml = """
        <QUIZ_BANK topic="Basic Test No Tag">
        <QUIZ_ITEM>
        <QUESTION>What is the opposite of black?</QUESTION>
        <OPTION1 correct="true">White</OPTION1>
        <OPTION2 correct="false">Gray</OPTION2>
        <OPTION3 correct="false">Dark</OPTION3>
        <OPTION4 correct="false">Color</OPTION4>
        <OPTION5 correct="false">None</OPTION5>
        <TOPIC>Colors</TOPIC>
        <!-- No TAG element -->
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify tag column exists and is empty
        assert len(df) == 1, "Should have parsed 1 question"
        assert "tag" in df.columns, "DataFrame should have a 'tag' column"
        assert df.iloc[0]["tag"] == "", "Tag should be an empty string when missing"
        assert df.iloc[0]["topic"] == "Colors", "Topic should be 'Colors'"
        assert "Skipped 0 questions" in f.getvalue()

    def test_html_content_with_tag(self):
        """Test parsing questions with HTML and a TAG."""
        xml = """
        <QUIZ_BANK topic="Code Blocks">
        <QUIZ_ITEM>
        <QUESTION>
        What will <code>print("Hi")</code> output?
        <pre><code class="language-python"># Example
        print("Hi")</code></pre>
        </QUESTION>
        <OPTION1 correct="true">Hi</OPTION1>
        <OPTION2 correct="false">"Hi"</OPTION2>
        <OPTION3 correct="false">Error</OPTION3>
        <OPTION4 correct="false">None</OPTION4>
        <OPTION5 correct="false">Output: Hi</OPTION5>
        <TOPIC>Python Output</TOPIC>
        <TAG>print function</TAG>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify HTML preservation and tag
        assert len(df) == 1, "Should have parsed 1 question"
        assert "<pre><code" in df.iloc[0]["text"], "HTML should be preserved"
        assert "<code>print(" in df.iloc[0]["text"], "Inline HTML should be preserved"
        assert len(df.iloc[0]["options"]) == 5, "Should have 5 options"
        assert df.iloc[0]["topic"] == "Python Output", "Topic mismatch"
        assert df.iloc[0]["tag"] == "print function", "Tag mismatch"
        assert "Skipped 0 questions" in f.getvalue()

    def test_rejects_item_with_too_few_options_tag_irrelevant(self):
        """Test parser rejects item with < 5 options, regardless of TAG."""
        xml = """
        <QUIZ_BANK topic="Missing Options Test">
        <QUIZ_ITEM>
        <QUESTION>Too few options?</QUESTION>
        <OPTION1 correct="true">Yes</OPTION1>
        <OPTION2 correct="false">No</OPTION2>
        <OPTION3 correct="false">Maybe</OPTION3>
        <!-- Missing OPTION4 and OPTION5 -->
        <TOPIC>Invalid</TOPIC>
        <TAG>Structure Error</TAG>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 0, "DataFrame should be empty"
        assert (
            "Expected 5 options but found 3" in output
        ), "Should log error about option count"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_rejects_item_with_too_many_options_tag_irrelevant(self):
        """Test parser rejects item with > 5 options, regardless of TAG."""
        xml = """
        <QUIZ_BANK topic="Too Many Options Test">
        <QUIZ_ITEM>
        <QUESTION>Too many options?</QUESTION>
        <OPTION1 correct="true">A</OPTION1>
        <OPTION2 correct="false">B</OPTION2>
        <OPTION3 correct="false">C</OPTION3>
        <OPTION4 correct="false">D</OPTION4>
        <OPTION5 correct="false">E</OPTION5>
        <OPTION6 correct="false">F</OPTION6>
        <TOPIC>Invalid</TOPIC>
        <TAG>Structure Error</TAG>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 0, "DataFrame should be empty"
        assert (
            "Expected 5 options but found 6" in output
        ), "Should log error about option count"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_parses_valid_item_skips_invalid_item_checks_tag(self):
        """Test parsing multiple items, checking tag on the valid one."""
        xml = """
        <QUIZ_BANK topic="Mixed Validity Test">
        <QUIZ_ITEM>
        <QUESTION>Valid Question (Item 1)</QUESTION>
        <OPTION1 correct="true">Correct</OPTION1>
        <OPTION2 correct="false">Wrong A</OPTION2>
        <OPTION3 correct="false">Wrong B</OPTION3>
        <OPTION4 correct="false">Wrong C</OPTION4>
        <OPTION5 correct="false">Wrong D</OPTION5>
        <TOPIC>Valid</TOPIC>
        <TAG>First Valid</TAG>
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Invalid Question (Item 2)</QUESTION>
        <OPTION1 correct="true">Correct</OPTION1>
        <OPTION2 correct="false">Wrong X</OPTION2>
        <!-- Missing options 3, 4, 5 -->
        <TOPIC>Invalid</TOPIC>
        <TAG>Not Parsed</TAG>
        </QUIZ_ITEM>
         <QUIZ_ITEM>
        <QUESTION>Another Valid Question (Item 3)</QUESTION>
        <OPTION1 correct="true">Yes</OPTION1>
        <OPTION2 correct="false">No</OPTION2>
        <OPTION3 correct="false">Maybe</OPTION3>
        <OPTION4 correct="false">Always</OPTION4>
        <OPTION5 correct="false">Never</OPTION5>
        <TOPIC>Valid Again</TOPIC>
        <!-- No TAG here -->
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        assert len(df) == 2, "Should have parsed 2 valid questions"
        assert df.iloc[0]["text"] == "Valid Question (Item 1)"
        assert df.iloc[0]["tag"] == "First Valid", "Tag mismatch for first valid item"
        assert df.iloc[1]["text"] == "Another Valid Question (Item 3)"
        assert df.iloc[1]["tag"] == "", "Tag should be empty for third item"
        assert (
            "Expected 5 options but found 2" in output
        ), "Should log error about invalid item"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_malformed_xml_recovery_with_tag(self):
        """Test recovery from malformed XML, checking tag on valid item."""
        # Malformed: Missing closing </QUIZ_ITEM> tag, but content is recoverable
        xml = """
        <QUIZ_BANK topic="Malformed XML">
        <QUIZ_ITEM>
        <QUESTION>Recoverable?</QUESTION>
        <OPTION1 correct="true">H2O</OPTION1>
        <OPTION2 correct="false">CO2</OPTION2>
        <OPTION3 correct="false">NaCl</OPTION3>
        <OPTION4 correct="false">H2SO4</OPTION4>
        <OPTION5 correct="false">CH4</OPTION5>
        <TOPIC>Chemistry</TOPIC>
        <TAG>Recovery Test</TAG>
        <!-- Missing closing tag for QUIZ_ITEM -->
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            # lxml's recover=True should handle this
            df = parse_quiz_xml_to_dataframe(xml)

        assert len(df) == 1, "Should parse 1 question despite malformed XML"
        assert df.iloc[0]["tag"] == "Recovery Test", "Tag should be parsed correctly"
        # Check stdout for parser warnings if needed, but main check is df content
        # print(f.getvalue()) # Uncomment to debug parser output

    def test_mixed_content_with_tag(self):
        """Test parsing mixed content (text/HTML) with a TAG."""
        xml = """
        <QUIZ_BANK topic="Mixed Content">
        <QUIZ_ITEM>
        <QUESTION>
        What is <code>x</code> after <code>x=1</code>?
        </QUESTION>
        <OPTION1 correct="true">1</OPTION1>
        <OPTION2 correct="false">0</OPTION2>
        <OPTION3 correct="false">None</OPTION3>
        <OPTION4 correct="false">Error</OPTION4>
        <OPTION5 correct="false">x</OPTION5>
        <TOPIC>Python Variables</TOPIC>
        <TAG>Assignment</TAG>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        assert len(df) == 1, "Should parse 1 question"
        assert "<code>x</code>" in df.iloc[0]["text"], "Inline code preserved"
        assert df.iloc[0]["tag"] == "Assignment", "Tag mismatch"

    def test_multiple_valid_questions_with_tags(self):
        """Test parsing multiple valid questions with varying tags."""
        xml = """
        <QUIZ_BANK topic="Multiple Questions">
        <QUIZ_ITEM>
        <QUESTION>Question 1</QUESTION>
        <OPTION1 correct="true">Correct 1</OPTION1>
        <OPTION2 correct="false">Wrong 1</OPTION2>
        <OPTION3 correct="false">Wrong 2</OPTION3>
        <OPTION4 correct="false">Wrong 3</OPTION4>
        <OPTION5 correct="false">Wrong 4</OPTION5>
        <TOPIC>Topic 1</TOPIC>
        <TAG>Tag One</TAG>
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Question 2</QUESTION>
        <OPTION1 correct="true">Correct 2</OPTION1>
        <OPTION2 correct="false">Wrong 5</OPTION2>
        <OPTION3 correct="false">Wrong 6</OPTION3>
        <OPTION4 correct="false">Wrong 7</OPTION4>
        <OPTION5 correct="false">Wrong 8</OPTION5>
        <TOPIC>Topic 2</TOPIC>
        <!-- No tag -->
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        assert len(df) == 2, "Should parse 2 questions"
        assert df.iloc[0]["tag"] == "Tag One", "Tag mismatch for Q1"
        assert df.iloc[1]["tag"] == "", "Tag should be empty for Q2"
        assert "Skipped 0 questions" in f.getvalue()

    def test_enhance_dataframe_with_parsed_tag(self):
        """Test enhancing a dataframe that already has a parsed tag."""
        # Create DataFrame simulating parser output (with 'tag' column)
        quiz_data = [
            {
                "text": "Q1",
                "options": ["C", "W1", "W2", "W3", "W4"],
                "answerIndex": 1,
                "topic": "Topic A",
                "tag": "Parsed Tag A",  # Parsed tag exists
                "chapter_no": "",
                "CHAPTER_TITLE": "",
            },
            {
                "text": "Q2",
                "options": ["C", "W1", "W2", "W3", "W4"],
                "answerIndex": 1,
                "topic": "Topic B",
                "tag": "",  # Parsed tag is empty
                "chapter_no": "",
                "CHAPTER_TITLE": "",
            },
        ]
        df = pd.DataFrame(quiz_data)

        # Define enhancement parameters (tag_mapping might overwrite parsed tag)
        tag_mapping = {"Topic A": "Mapped Tag A"}  # Map Topic A, no map for Topic B
        difficulty_levels = {0: "easy", 1: "hard"}
        time_estimates = {0: 30, 1: 90}

        enhanced_df = enhance_quiz_dataframe(
            df,
            tag_mapping=tag_mapping,  # This will overwrite 'Parsed Tag A'
            chapter_no="3",
            chapter_title="Enhancement Test",
            difficulty_levels=difficulty_levels,
            time_estimates=time_estimates,
        )

        # Verify enhancements
        assert "tag" in enhanced_df.columns
        # Check tag mapping overwrite
        assert (
            enhanced_df.iloc[0]["tag"] == "Mapped Tag A"
        ), "Tag should be overwritten by mapping"
        # Check tag remains empty if no mapping and initially empty
        assert enhanced_df.iloc[1]["tag"] == "", "Tag should remain empty if no mapping"

        assert enhanced_df.iloc[0]["chapter_no"] == "3", "Chapter number mismatch"
        assert (
            enhanced_df.iloc[1]["CHAPTER_TITLE"] == "Enhancement Test"
        ), "Chapter title mismatch"
        assert enhanced_df.iloc[0]["difficulty"] == "easy", "Difficulty mismatch Q1"
        assert enhanced_df.iloc[1]["difficulty"] == "hard", "Difficulty mismatch Q2"
        assert enhanced_df.iloc[0]["time_estimate"] == 30, "Time estimate mismatch Q1"
        assert enhanced_df.iloc[1]["time_estimate"] == 90, "Time estimate mismatch Q2"

    def test_no_topic_uses_main_topic_with_tag(self):
        """Test fallback to main topic when QUIZ_ITEM lacks TOPIC but has TAG."""
        xml = """
        <QUIZ_BANK topic="Main Topic Fallback">
        <QUIZ_ITEM>
        <QUESTION>Question without specific topic</QUESTION>
        <OPTION1 correct="true">Correct</OPTION1>
        <OPTION2 correct="false">Wrong 1</OPTION2>
        <OPTION3 correct="false">Wrong 2</OPTION3>
        <OPTION4 correct="false">Wrong 3</OPTION4>
        <OPTION5 correct="false">Wrong 4</OPTION5>
        <!-- No TOPIC element -->
        <TAG>Specific Concept</TAG>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        assert len(df) == 1, "Should parse 1 question"
        assert df.iloc[0]["topic"] == "Main Topic Fallback", "Topic should fall back"
        assert df.iloc[0]["tag"] == "Specific Concept", "Tag should be parsed correctly"
        assert "Skipped 0 questions" in f.getvalue()


# Run the tests if the script is executed directly
if __name__ == "__main__":
    # Allows running tests with: python test_quiz_parser.py
    print("Running tests using pytest.main()...")
    pytest.main(["-v", __file__])
