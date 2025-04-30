# Running the Quiz Parser and Tests

This guide explains how to set up and run both the quiz parser script and its tests.

## Setup

1. First, save the fixed quiz parser script as `fixed_quiz_parser.py`:

```bash
# Copy the code from the "Fixed Quiz Parser" artifact and save it as fixed_quiz_parser.py
```

2. Save the test script as `test_quiz_parser.py`:

```bash
# Copy the code from the "Quiz Parser Tests" artifact and save it as test_quiz_parser.py
```

3. Install required dependencies:

```bash
pip install pytest pandas lxml
```

## Running the Script

To run the quiz parser script directly:

```bash
python fixed_quiz_parser.py
```

This will execute the example at the bottom of the script (which parses a simple quiz about Python addition).

To use the parser with your own XML:

```python
from fixed_quiz_parser import parse_quiz_xml_to_dataframe

# Read XML from a file
with open('your_quiz.xml', 'r') as f:
    xml_content = f.read()

# Parse the XML
df = parse_quiz_xml_to_dataframe(
    xml_content, 
    chapter_no="1", 
    chapter_title="Your Chapter Title"
)

# Print the parsed quiz
print(df)
```

## Running the Tests

### Method 1: Run all tests

```bash
pytest test_quiz_parser.py -v
```

The `-v` flag gives verbose output showing each test that runs.

### Method 2: Run the tests from the test file itself

```bash
python test_quiz_parser.py
```

### Method 3: Run a specific test

```bash
pytest test_quiz_parser.py::TestQuizParser::test_html_content -v
```

### Method 4: Run tests with coverage report

```bash
pip install pytest-cov
pytest --cov=fixed_quiz_parser test_quiz_parser.py --cov-report term-missing
```

## Understanding Test Results

The tests check if the parser handles:

1. Basic well-formed XML quizzes
2. HTML and code blocks in questions
3. Missing options
4. Malformed XML with recovery
5. Mixed content (text and HTML elements)
6. Multiple questions in one XML
7. Metadata enhancement functionality
8. Fallback to main topic when specific topic is missing

A successful test run will show all tests passing. If any test fails, the output will show exactly which assertion failed and why, making it easy to debug.

## Comparing with the Original Parser

If you want to compare with the original parser:

1. Fix and save the original parser script (remove duplicates and fix the broken code)
2. Modify the import line in the test script to import from the original parser module
3. Run the tests against the original parser
4. Compare the results with the tests against the fixed parser

This will give you a clear indication of which issues were fixed and if any tests still fail with the original parser.
