# Quiz Bank Generation Prompt

I need you to create a multiple-choice quiz bank based on the content provided to you with this prompt. This quiz bank will be automatically parsed and imported into a Django application, so strict adherence to the specified format is essential.

## Output Format

Generate multiple-choice questions in the following XML format:

```xml
<QUIZ_BANK topic="[MAIN TOPIC OF CONTENT]">

<QUIZ_ITEM>
<QUESTION>
[Question text goes here - can be multiple lines]
</QUESTION>
<OPTION1 correct="true">
[Correct answer - always place the correct answer as OPTION1]
</OPTION1>
<OPTION2 correct="false">
[Incorrect answer]
</OPTION2>
<OPTION3 correct="false">
[Incorrect answer]
</OPTION3>
<OPTION4 correct="false">
[Incorrect answer]
</OPTION4>
<OPTION5 correct="false">
[Incorrect answer]
</OPTION5>
<TOPIC>[General subtopic or concept area]</TOPIC>
<TAG>[Specific concept or keyword being tested]</TAG>
</QUIZ_ITEM>

<!-- Add more QUIZ_ITEM blocks for additional questions -->

</QUIZ_BANK>
```

## Important Requirements

1.  **XML Structure**:

    - Use exactly the tags shown above: `<QUIZ_BANK>`, `<QUIZ_ITEM>`, `<QUESTION>`, `<OPTION1>`, `<OPTION2>`, `<OPTION3>`, `<OPTION4>`, `<OPTION5>`, `<TOPIC>`, `<TAG>`.
    - Always properly close all tags.
    - Keep the hierarchy consistent (`QUIZ_BANK` > `QUIZ_ITEM` > individual elements).
    - Include the `correct="true"` attribute only for `OPTION1`.
    - Include the `correct="false"` attribute for `OPTION2`, `OPTION3`, `OPTION4`, and `OPTION5`.

2.  **Question Content**:

    - Create as many substantive questions as possible that test understanding, not just recall.
    - Focus primarily on conceptual understanding rather than trivial code implementation details.
    - Use your judgment on when to include code examples in the `<QUESTION>` – only use them when they truly help illustrate a concept, not for their own sake. Keep code examples concise.

3.  **Answer Options**:

    - ALWAYS place the correct answer as `OPTION1` with `correct="true"`. Shuffling will be handled later during post-processing.
    - All other options (`OPTION2` to `OPTION5`) MUST be incorrect with `correct="false"`.
    - Make incorrect options plausible but clearly wrong.
    - Ensure each question has exactly 5 options (one correct, four incorrect).
    - **Crucially, avoid long or multi-line code snippets within `<OPTION>` tags.** Keep options concise, especially for mobile readability. Short inline code references (e.g., `<code>MyClass.method()</code>`, `<code>htmx-swap</code>`) are acceptable, but complex code blocks are not suitable for options.

4.  **Code Content Handling (within `<QUESTION>`)**:

    - Format all code snippets using proper HTML tags:
      - Use `<pre><code class="language-XXX">...</code></pre>` for multi-line blocks (replace XXX with the language name, e.g., python, javascript, html).
      - Use `<code>...</code>` for inline code references.
      - Preserve indentation exactly.
    - Keep code examples concise and focused, especially considering mobile device readability.
    - Aim for clarity over complexity in code samples.

5.  **Topic and Tagging**:
    - `<TOPIC>`: Use a **general** category for the question (e.g., "Django ORM", "HTMX Basics", "Cloud Security", "JavaScript Events"). Keep these relatively broad (2-4 words). Be consistent across similar general areas.
    - `<TAG>`: Use a **specific** keyword or concept being tested in the question (e.g., "QuerySet Slicing", "htmx-trigger", "IAM Roles", "Event Listener"). Keep these concise (1-3 words). This tag helps in fine-grained analysis.

## Example Question (for programming content)

```xml
<QUIZ_ITEM>
<QUESTION>
Consider the following Django ORM query. What does it retrieve?

<pre><code class="language-python">
from myapp.models import Product

# Assume Product has 'name' and 'price' fields
products = Product.objects.filter(price__gt=100).order_by('-name')[:5]
</code></pre>
</QUESTION>
<OPTION1 correct="true">
The first 5 products with a price greater than 100, ordered by name descending.
</OPTION1>
<OPTION2 correct="false">
All products with a price greater than 100, ordered by name ascending.
</OPTION2>
<OPTION3 correct="false">
The first 5 products regardless of price, ordered by name descending.
</OPTION3>
<OPTION4 correct="false">
Products named 'product 1' through 'product 5' with a price over 100.
</OPTION4>
<OPTION5 correct="false">
An error because slicing cannot be combined with ordering.
</OPTION5>
<TOPIC>Django ORM</TOPIC>
<TAG>QuerySet Filtering Ordering Slicing</TAG>
</QUIZ_ITEM>
```

## Example Question (for conceptual content)

```xml
<QUIZ_ITEM>
<QUESTION>
In HTMX, what is the primary purpose of the <code>hx-swap</code> attribute?
</QUESTION>
<OPTION1 correct="true">
To specify how the response content should be placed into the DOM.
</OPTION1>
<OPTION2 correct="false">
To define which event triggers the AJAX request.
</OPTION2>
<OPTION3 correct="false">
To indicate the target element that will receive the response content.
</OPTION3>
<OPTION4 correct="false">
To set the HTTP method (GET, POST, etc.) for the request.
</OPTION4>
<OPTION5 correct="false">
To add CSS classes to the element after the request completes.
</OPTION5>
<TOPIC>HTMX Basics</TOPIC>
<TAG>hx-swap attribute</TAG>
</QUIZ_ITEM>
```

## Content to Create Quiz Questions From:
--- START_OF_CONTENT ---
[CONTENT_PLACEHOLDER]
--- END_OF_CONTENT ---
## Additional Guidelines

1.  **Balance of Question Types**:
    - Prioritize conceptual understanding questions over code-heavy questions.
    - Use code examples sparingly in questions and only when they genuinely clarify a concept.
    - **Avoid code entirely in answer options**, except for very short inline references (like function names, attributes, or simple expressions).
2.  **Quiz Difficulty Balance**:
    - Include a mix of basic comprehension (30%), application (50%), and analysis (20%) questions.
    - Ensure questions test meaningful understanding rather than trivial details.
3.  **Accessibility Considerations**:
    - Keep language clear and concise.
    - Minimize unnecessary jargon.
    - Focus on small, illustrative examples if code is used in the question.
4.  **Topic/Tag Strategy**:
    - Ensure the `<TOPIC>` provides a useful general grouping.
    - Ensure the `<TAG>` accurately reflects the specific point being tested.

Remember, the structure must be exactly as specified so it can be automatically parsed without errors. Do not add additional tags, attributes, or formatting outside of the HTML code formatting tags mentioned above.
