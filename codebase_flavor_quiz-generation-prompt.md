# Quiz Bank Generation Prompt (from Codebase Analysis)

## Goal Context

Over the past two years, I've built many projects using a method I refer to as "Vibe Coding." This approach involves giving an AI/LLM a general idea for an application and letting it lead the development process, often using frameworks or libraries I'm initially unfamiliar with. My role becomes largely iterative: feeding error messages and logs back to the LLM and adjusting the generated code until, through trial and error, the application works.

While this Vibe Coding method has successfully produced functional applications, it has left gaps in my fundamental understanding of the underlying programming concepts used within those specific projects.

To address this, I need you to act as a learning tool generator. You will be provided with the codebase of a specific project built using this method. Your task is to analyze the code and generate a targeted quiz bank to help me review and solidify my understanding of the concepts *actually implemented* in that project.

This quiz bank will be automatically parsed and imported into a Django application, so strict adherence to the specified XML format below is essential.

## Task: Analyze Code and Generate Quiz Bank

1.  **Analyze the Provided Codebase:** Carefully examine the structure, files, imports, and code patterns within the provided project codebase. Identify the specific programming concepts, libraries (e.g., `django-crispy-forms`, `requests`), framework features (e.g., Django Function-Based Views, specific QuerySet methods, React Hooks), and language features (e.g., Python decorators, JavaScript async/await) that are *actively used*. For each concept identified, note the primary file path(s) where it is implemented or demonstrated.
2.  **Generate Customized Quiz Bank:** Based *only* on the concepts identified during your analysis, create a multiple-choice quiz bank using the precise XML format specified below. Focus exclusively on the technologies and patterns present in *this specific codebase*. If a concept (like Class-Based Views or a particular library) is not used in the provided code, do *not* generate questions about it. Each question generated must be linked to a relevant file path from the codebase using the `<PATH>` tag.

## Output Format

Generate multiple-choice questions in the following XML format. The `topic` attribute in `QUIZ_BANK` should reflect the project or main technology being analyzed (e.g., "Django Project X Concepts", "React Component Library Usage").

```xml
<QUIZ_BANK topic="[Codebase Concept Review: Identify Project/Technology]">

<QUIZ_ITEM>
<QUESTION>
[Question text goes here - can be multiple lines. Focus on general concepts found in the code.]
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
<TOPIC>[General concept area derived from code, e.g., "Django ORM", "React State Management", "Python Error Handling"]</TOPIC>
<TAG>[Specific concept/keyword from code being tested, e.g., "QuerySet Filtering", "useState Hook", "Try-Except Block"]</TAG>
<PATH>[Relative file path where the concept is illustrated, e.g., src/myapp/views.py]</PATH>
</QUIZ_ITEM>

</QUIZ_BANK>
```

## Important Requirements (Inherited from Original Template)

1.  **XML Structure**:
    * Use exactly the tags shown: `<QUIZ_BANK>`, `<QUIZ_ITEM>`, `<QUESTION>`, `<OPTION1>`, `<OPTION2>`, `<OPTION3>`, `<OPTION4>`, `<OPTION5>`, `<TOPIC>`, `<TAG>`, and `<PATH>`.
    * Properly close all tags. Maintain hierarchy (`QUIZ_ITEM` contains `QUESTION`, `OPTION`s, `TOPIC`, `TAG`, and `PATH`).
    * `correct="true"` only for `OPTION1`. `correct="false"` for `OPTION2`-`OPTION5`.
    * The `<PATH>` tag must contain the relative file path (from the root of the provided codebase) that best illustrates the concept being tested in the `<QUESTION>`. Example: `src/product/models.py`.

2.  **Question Content**:
    * Generate questions testing understanding of the concepts *as they are used or relevant to the provided code*.
    * **Crucially: Frame questions to test the *general understanding* of the concept identified (e.g., "What is the purpose of Django's `ForeignKey` field?") rather than asking about specific implementation details within the file mentioned in `<PATH>` (e.g., avoid "In `models.py`, what does the `product` field link to?"). The question must be answerable *without* referring to the specific code file; the `<PATH>` tag is only for optional reference.**
    * Prioritize conceptual understanding over trivial implementation details, but ensure relevance to the codebase.
    * Use code examples *from or inspired by the codebase* in `<QUESTION>` sparingly, only when essential to illustrate a general concept found within the project. **Keep examples concise, as lengthy code blocks can be difficult to read and understand on smaller mobile screens.** Format using `<pre><code class="language-XXX">...</code></pre>` or `<code>...</code>`. Preserve indentation.

3.  **Answer Options**:
    * Correct answer is ALWAYS `OPTION1`. Shuffling handled later.
    * Options `OPTION2`-`OPTION5` MUST be incorrect but plausible.
    * Exactly 5 options per question.
    * **Crucially, avoid long or multi-line code snippets within `<OPTION>` tags.** Keep options concise. Short inline code references (e.g., `<code>MyClass.method()</code>`, `<code>useState</code>`) are acceptable.

4.  **Topic and Tagging**:
    * `<TOPIC>`: Use a **general** category relevant to the concepts found in the code (e.g., "Django Models", "React Component Lifecycle", "API Integration"). Be consistent.
    * `<TAG>`: Use a **specific** keyword or concept from the code being tested (e.g., "ForeignKey Field", "useEffect Hook", "JSON Parsing"). Be specific.

5.  **Balance and Difficulty**:
    * Aim for a mix of basic comprehension (what does this concept *do*?), application (how might this concept be used *in this context*?), and analysis (why was this approach likely chosen *here*?) questions, all grounded in the provided code.
    * Test meaningful understanding relevant to the project's implementation.


Remember, the primary goal is to generate learning material directly relevant to the specific codebase provided, using the exact XML structure (including the `<PATH>` tag) for automated parsing, and ensuring questions test general concepts in a self-contained manner.

## Codebase to Analyze:

--- START_OF_CODEBASE ---
[CODEBASE_PLACEHOLDER]
--- END_OF_CODEBASE ---