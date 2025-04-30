# XML Quiz Parser for Django Quiz Application

## Overview

This package provides tools for parsing structured XML quiz content into a format compatible with Django-based quiz applications. The `parse_quiz_xml_to_dataframe` function converts XML quiz questions into pandas DataFrames that can be easily imported into a database or processed for web display.

## Features

- Parse XML-formatted quiz questions with options, correct answers, and topics
- Support for HTML content within questions, including code blocks
- Robust error handling that continues processing even when individual questions have issues
- Metadata enhancement with tags, difficulty levels, and time estimates
- Chapter and section organization support
- Extensive test suite to ensure reliability

## Installation

### Requirements

- Python 3.6+
- pandas
- lxml

### Install Dependencies

```bash
pip install pandas lxml pytest
```

## Usage

### Basic Parsing

```python
from quiz_parser import parse_quiz_xml_to_dataframe

# Parse quiz content from a string
with open('your_quiz.xml', 'r') as f:
    xml_content = f.read()

df = parse_quiz_xml_to_dataframe(
    xml_content,
    chapter_no="1",
    chapter_title="Introduction to Python"
)

# Review the parsed questions
print(f"Parsed {len(df)} questions")
print(df.head())
```

### Adding Metadata

```python
from quiz_parser import enhance_quiz_dataframe

# Define metadata
tag_mapping = {
    "Basic Operations": "arithmetic",
    "Control Flow": "flow-control"
}
difficulty_levels = {0: "easy", 1: "medium", 2: "hard"}
time_estimates = {0: 30, 1: 60, 2: 120}  # seconds

# Enhance the DataFrame with metadata
enhanced_df = enhance_quiz_dataframe(
    df,
    tag_mapping=tag_mapping,
    difficulty_levels=difficulty_levels,
    time_estimates=time_estimates
)
```

### Expected XML Format

```xml
<QUIZ_BANK topic="Main Topic">
  <QUIZ_ITEM>
    <QUESTION>
      What is 2+2?
    </QUESTION>
    <OPTION1 correct="true">4</OPTION1>
    <OPTION2 correct="false">3</OPTION2>
    <OPTION3 correct="false">5</OPTION3>
    <OPTION4 correct="false">22</OPTION4>
    <OPTION5 correct="false">None of the above</OPTION5>
    <TOPIC>Arithmetic</TOPIC>
  </QUIZ_ITEM>
  <!-- More QUIZ_ITEM elements... -->
</QUIZ_BANK>
```

Key requirements:
- Each question must have 5 options
- OPTION1 is always the correct answer
- TOPIC is optional (falls back to the main QUIZ_BANK topic)
- HTML tags are preserved in questions and options

## Key Features and Fixes

### Error Handling Principle: "Don't throw the baby out with the bathwater"

One of the core principles of the parser is robust error handling that:

1. **Discards problematic questions** rather than failing the entire process
2. **Logs detailed error messages** for each skipped question
3. **Continues processing** valid questions even when some have issues
4. **Provides summary statistics** about successful and failed parsing

This approach ensures that even if a few questions in a large quiz bank have formatting issues, you'll still get results for all the valid questions.

### XML Parsing Improvements

The parser includes several fixes and improvements over earlier versions:

1. **Mismatched tags handling**: Fixes common issues like `<OPTION3>...</OPTION4>` automatically
2. **HTML preservation**: Properly retains code blocks and other HTML formatting in questions
3. **Resilient parsing**: Recovers from malformed XML when possible
4. **Flexible option handling**: Fills in missing options with empty strings to maintain format consistency
5. **Tag normalization**: Ensures consistent casing and formatting of XML tags

### Data Structure

The parser outputs a pandas DataFrame with these columns:

- `text`: The question text with any HTML preserved
- `options`: A list of 5 option strings
- `answerIndex`: Always 1 (for OPTION1, per specified format)
- `topic`: The question's topic or the main quiz bank topic
- `chapter_no`: Chapter number (if provided)
- `CHAPTER_TITLE`: Chapter title (if provided)

Additional columns added by `enhance_quiz_dataframe`:

- `tag`: Standardized topic tag based on mapping
- `difficulty`: Question difficulty level
- `time_estimate`: Estimated time to answer (in seconds)

## Common Issues and Solutions

### Problematic XML Formatting

If you encounter parsing errors, check for:

1. **Mismatched option tags**: Like `<OPTION3>...</OPTION4>`
2. **Unclosed tags**: Make sure all XML tags are properly closed
3. **HTML entity issues**: Use proper XML entities (`&lt;`, `&gt;`, etc.)
4. **Unexpected characters**: Some special characters may need encoding

The parser will attempt to handle these issues automatically, but severe XML problems may still cause questions to be skipped.

### Missing Options

All questions should have exactly 5 options. The parser will:

1. Add empty strings for missing options (up to 5)
2. Skip questions with major option issues
3. Log warnings about missing options

### HTML Content

Code blocks and other HTML are supported in questions and options:

```xml
<QUESTION>
  What will this code output?
  <pre><code class="language-python">
  print("Hello" + " World")
  </code></pre>
</QUESTION>
```

The HTML formatting will be preserved in the output DataFrame.

## Running Tests

A comprehensive test suite is included to verify parser functionality:

```bash
# Run all tests
pytest test_quiz_parser.py -v

# Run a specific test
pytest test_quiz_parser.py::TestQuizParser::test_html_content -v

# Run with coverage
pytest --cov=quiz_parser test_quiz_parser.py --cov-report term-missing
```

