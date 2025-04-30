import pytest
import pandas as pd
import sys
from io import StringIO, BytesIO  # Use BytesIO for etree.parse with parser
import re
from pathlib import Path
from lxml import etree  # Import etree for direct use if needed

# Import the module to test
# This assumes the fixed parser is saved as fixed_quiz_parser.py
sys.path.append(".")
from fixed_quiz_parser import parse_quiz_xml_to_dataframe, enhance_quiz_dataframe


# Helper to capture stdout
from contextlib import redirect_stdout
import io


class TestQuizParser:

    def test_basic_parsing(self):
        """Test parsing a simple, well-formed XML quiz with 5 options."""
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
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify dataframe structure and content
        assert len(df) == 1, "Should have parsed 1 question"
        assert (
            df.iloc[0]["text"] == "What is 2+2?"
        ), "Question text not correctly parsed"
        assert df.iloc[0]["options"][0] == "4", "First option should be '4'"
        assert len(df.iloc[0]["options"]) == 5, "Should have exactly 5 options"
        assert df.iloc[0]["answerIndex"] == 1, "Answer index should be 1"
        assert df.iloc[0]["topic"] == "Arithmetic", "Topic should be 'Arithmetic'"
        assert (
            "Skipped 0 questions" in f.getvalue()
        )  # Ensure no warnings/errors for valid case

    def test_html_content(self):
        """Test parsing questions with HTML code blocks (valid 5 options)."""
        xml = """
        <QUIZ_BANK topic="Code Blocks">
        <QUIZ_ITEM>
        <QUESTION>
        What will this code output?
        <pre><code class="language-python">
        print("Hello" + " World")
        </code></pre>
        </QUESTION>
        <OPTION1 correct="true">Hello World</OPTION1>
        <OPTION2 correct="false">HelloWorld</OPTION2>
        <OPTION3 correct="false">Error</OPTION3>
        <OPTION4 correct="false">None</OPTION4>
        <OPTION5 correct="false">Hello + World</OPTION5>
        <TOPIC>String Concatenation</TOPIC>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify HTML content is preserved
        assert len(df) == 1, "Should have parsed 1 question"
        assert "<pre><code" in df.iloc[0]["text"], "HTML tags should be preserved"
        assert (
            'print("Hello" + " World")' in df.iloc[0]["text"]
        ), "Code content should be preserved"
        assert len(df.iloc[0]["options"]) == 5, "Should have exactly 5 options"
        assert "Skipped 0 questions" in f.getvalue()

    def test_rejects_item_with_too_few_options(self):
        """Test parser rejects QUIZ_ITEM with less than 5 options."""
        xml = """
        <QUIZ_BANK topic="Missing Options Test">
        <QUIZ_ITEM>
        <QUESTION>What is the capital of France?</QUESTION>
        <OPTION1 correct="true">Paris</OPTION1>
        <OPTION2 correct="false">London</OPTION2>
        <OPTION3 correct="false">Berlin</OPTION3>
        <OPTION4 correct="false">Rome</OPTION4> 
        <!-- Missing OPTION5 -->
        <TOPIC>Geography</TOPIC>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        # Verify item was rejected
        assert len(df) == 0, "DataFrame should be empty as the only item was invalid"
        assert (
            "Expected 5 options but found 4" in output
        ), "Should log error about missing options"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_rejects_item_with_too_many_options(self):
        """Test parser rejects QUIZ_ITEM with more than 5 options."""
        xml = """
        <QUIZ_BANK topic="Too Many Options Test">
        <QUIZ_ITEM>
        <QUESTION>What element has symbol O?</QUESTION>
        <OPTION1 correct="true">Oxygen</OPTION1>
        <OPTION2 correct="false">Osmium</OPTION2>
        <OPTION3 correct="false">Gold</OPTION3>
        <OPTION4 correct="false">Hydrogen</OPTION4> 
        <OPTION5 correct="false">Oganesson</OPTION5>
        <OPTION6 correct="false">EXTRA OPTION!</OPTION6> 
        <TOPIC>Chemistry</TOPIC>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        # Verify item was rejected
        assert len(df) == 0, "DataFrame should be empty as the only item was invalid"
        assert (
            "Expected 5 options but found 6" in output
        ), "Should log error about extra options"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_parses_valid_item_skips_invalid_item(self):
        """Test parsing multiple items where one is valid and one is invalid."""
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
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Invalid Question with 6 options (Item 2)</QUESTION>
        <OPTION1 correct="true">Correct</OPTION1>
        <OPTION2 correct="false">Wrong X</OPTION2>
        <OPTION3 correct="false">Wrong Y</OPTION3>
        <OPTION4 correct="false">Wrong Z</OPTION4> 
        <OPTION5 correct="false">Wrong W</OPTION5>
        <OPTION6 correct="false">EXTRA!</OPTION6> 
        <TOPIC>Invalid</TOPIC>
        </QUIZ_ITEM>
         <QUIZ_ITEM>
        <QUESTION>Another Valid Question (Item 3)</QUESTION>
        <OPTION1 correct="true">Yes</OPTION1>
        <OPTION2 correct="false">No</OPTION2>
        <OPTION3 correct="false">Maybe</OPTION3>
        <OPTION4 correct="false">Always</OPTION4>
        <OPTION5 correct="false">Never</OPTION5>
        <TOPIC>Valid Again</TOPIC>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        output = f.getvalue()
        # Verify correct items parsed, invalid skipped
        assert len(df) == 2, "Should have parsed exactly 2 valid questions"
        assert df.iloc[0]["text"] == "Valid Question (Item 1)"
        assert df.iloc[1]["text"] == "Another Valid Question (Item 3)"
        assert (
            "Expected 5 options but found 6" in output
        ), "Should log error about the invalid item"
        assert "Skipped 1 questions" in output, "Should report 1 skipped question"

    def test_malformed_xml_recovery(self):
        """Test recovery from generally malformed XML (still requires 5 options if item parsed)."""
        # Malformed: Missing closing </QUIZ_BANK> tag, but the item itself is valid (5 options)
        xml = """
        <QUIZ_BANK topic="Malformed XML">
        <QUIZ_ITEM>
        <QUESTION>What is water made of?</QUESTION>
        <OPTION1 correct="true">H2O</OPTION1>
        <OPTION2 correct="false">CO2</OPTION2>
        <OPTION3 correct="false">NaCl</OPTION3>
        <OPTION4 correct="false">H2SO4</OPTION4>
        <OPTION5 correct="false">CH4</OPTION5>
        <TOPIC>Chemistry</TOPIC>
        </QUIZ_ITEM>
        <!-- Missing closing tag for QUIZ_BANK -->
        some extra text
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify parser recovers and parses the valid item
        assert len(df) == 1, "Should have parsed 1 question despite malformed XML"
        assert (
            df.iloc[0]["text"] == "What is water made of?"
        ), "Question text should be parsed correctly"
        assert len(df.iloc[0]["options"]) == 5, "Parsed item should have 5 options"

    def test_mixed_content(self):
        """Test parsing XML with mixed content (text and elements) - valid 5 options."""
        xml = """
        <QUIZ_BANK topic="Mixed Content">
        <QUIZ_ITEM>
        <QUESTION>
        Consider this function:
        <pre><code class="language-python">
        def greet(name):
            return f"Hello, {name}!"
        </code></pre>
        What will <code>greet("World")</code> return?
        </QUESTION>
        <OPTION1 correct="true">Hello, World!</OPTION1>
        <OPTION2 correct="false">Hello World</OPTION2>
        <OPTION3 correct="false">Hello, {name}!</OPTION3>
        <OPTION4 correct="false">Error</OPTION4>
        <OPTION5 correct="false">None</OPTION5>
        <TOPIC>Python f-strings</TOPIC>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify mixed content handling
        assert len(df) == 1, "Should have parsed 1 question"
        assert "<pre><code" in df.iloc[0]["text"], "Block code tag should be preserved"
        assert (
            "<code>greet(" in df.iloc[0]["text"]
        ), "Inline code tag should be preserved"
        assert len(df.iloc[0]["options"]) == 5, "Should have exactly 5 options"

    def test_multiple_valid_questions(self):
        """Test parsing multiple questions, all valid."""
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
        </QUIZ_ITEM>
        <QUIZ_ITEM>
        <QUESTION>Question 2</QUESTION>
        <OPTION1 correct="true">Correct 2</OPTION1>
        <OPTION2 correct="false">Wrong 5</OPTION2>
        <OPTION3 correct="false">Wrong 6</OPTION3>
        <OPTION4 correct="false">Wrong 7</OPTION4>
        <OPTION5 correct="false">Wrong 8</OPTION5>
        <TOPIC>Topic 2</TOPIC>
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify multiple questions handling
        assert len(df) == 2, "Should have parsed 2 questions"
        assert (
            df.iloc[0]["text"] == "Question 1"
        ), "First question text should be correct"
        assert (
            df.iloc[1]["text"] == "Question 2"
        ), "Second question text should be correct"
        assert (
            df.iloc[0]["topic"] == "Topic 1" and df.iloc[1]["topic"] == "Topic 2"
        ), "Topics should be correct"
        assert "Skipped 0 questions" in f.getvalue()

    def test_enhance_dataframe(self):
        """Test enhancing the dataframe with metadata."""
        # Create a simple dataframe (as output by the parser)
        quiz_data = [
            {
                "text": "Test question",
                "options": ["Correct", "Wrong 1", "Wrong 2", "Wrong 3", "Wrong 4"],
                "answerIndex": 1,
                "topic": "Test Topic",
                "chapter_no": "",
                "CHAPTER_TITLE": "",
            }
        ]
        df = pd.DataFrame(quiz_data)

        # Define enhancement parameters
        tag_mapping = {"Test Topic": "test-tag"}
        difficulty_levels = {0: "hard"}
        time_estimates = {0: 120}

        # Enhance the dataframe
        enhanced_df = enhance_quiz_dataframe(
            df,
            tag_mapping=tag_mapping,
            chapter_no="2",
            chapter_title="Test Chapter",
            difficulty_levels=difficulty_levels,
            time_estimates=time_estimates,
        )

        # Verify enhancements
        assert (
            "tag" in enhanced_df.columns and enhanced_df.iloc[0]["tag"] == "test-tag"
        ), "Tag mapping should be applied"
        assert enhanced_df.iloc[0]["chapter_no"] == "2", "Chapter number should be set"
        assert (
            enhanced_df.iloc[0]["CHAPTER_TITLE"] == "Test Chapter"
        ), "Chapter title should be set"
        assert (
            "difficulty" in enhanced_df.columns
            and enhanced_df.iloc[0]["difficulty"] == "hard"
        ), "Difficulty should be set"
        assert (
            "time_estimate" in enhanced_df.columns
            and enhanced_df.iloc[0]["time_estimate"] == 120
        ), "Time estimate should be set"

    def test_no_topic_uses_main_topic(self):
        """Test fallback to main topic when QUIZ_ITEM lacks TOPIC (valid 5 options)."""
        xml = """
        <QUIZ_BANK topic="Main Topic">
        <QUIZ_ITEM>
        <QUESTION>Question without specific topic</QUESTION>
        <OPTION1 correct="true">Correct</OPTION1>
        <OPTION2 correct="false">Wrong 1</OPTION2>
        <OPTION3 correct="false">Wrong 2</OPTION3>
        <OPTION4 correct="false">Wrong 3</OPTION4>
        <OPTION5 correct="false">Wrong 4</OPTION5>
        <!-- No TOPIC element -->
        </QUIZ_ITEM>
        </QUIZ_BANK>
        """
        f = io.StringIO()
        with redirect_stdout(f):
            df = parse_quiz_xml_to_dataframe(xml)

        # Verify main topic fallback
        assert len(df) == 1, "Should have parsed 1 question"
        assert (
            df.iloc[0]["topic"] == "Main Topic"
        ), "Topic should fall back to main topic"
        assert len(df.iloc[0]["options"]) == 5, "Should have exactly 5 options"
        assert "Skipped 0 questions" in f.getvalue()


# Run the tests if the script is executed directly
if __name__ == "__main__":
    # Allows running tests with: python test_quiz_parser.py
    # Note: Capturing stdout might behave differently when run this way vs. pytest CLI
    print("Running tests using pytest.main()...")
    pytest.main(["-v", __file__])
