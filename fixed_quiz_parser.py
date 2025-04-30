import pandas as pd
from lxml import etree
from io import StringIO
import re


def parse_quiz_xml_to_dataframe(xml_content, chapter_no=None, chapter_title=None):
    """
    Parse XML quiz content and convert it to a pandas DataFrame compatible with import_quiz_bank.py
    Enforces that each QUIZ_ITEM must contain exactly 5 OPTION elements.

    Args:
        xml_content (str): XML string from LLM containing quiz questions
        chapter_no (str, optional): Chapter number to associate with all questions
        chapter_title (str, optional): Chapter title to associate with all questions

    Returns:
        pd.DataFrame: DataFrame ready for import_quiz_bank.py
    """
    # Clean up potential XML issues
    # Remove any text before the first tag and after the last tag
    xml_content = re.sub(r"^.*?<QUIZ_BANK", "<QUIZ_BANK", xml_content, flags=re.DOTALL)
    xml_content = re.sub(
        r"</QUIZ_BANK>.*?$", "</QUIZ_BANK>", xml_content, flags=re.DOTALL
    )

    # Parse the XML
    try:
        # Use encoding='utf-8' to handle potential special characters robustly
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)
        # Check if parsing recovered completely or resulted in a minimal tree
        if (
            root is None
            or len(root) == 0
            and not xml_content.strip().startswith("<QUIZ_BANK")
        ):
            raise ValueError("Root element not found or empty after parsing.")
    except Exception as e:
        print(f"Initial XML parsing error: {e}")
        # Attempt more aggressive recovery (less common now with explicit encoding)
        xml_content = re.sub(r"<\?xml.*?\?>", "", xml_content)
        xml_content = f"<ROOT>{xml_content}</ROOT>"
        try:
            parser = etree.XMLParser(recover=True, encoding="utf-8")
            root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)
            if root is None:
                raise ValueError("Root element is None after recovery attempt.")
        except Exception as e_rec:
            print(f"Failed to parse XML even after recovery attempts: {e_rec}")
            return pd.DataFrame()

    # Prepare data structure
    quiz_data = []
    skipped_count = 0

    # Find all QUIZ_ITEM elements relative to the root
    # Adjust XPath if recovery added a <ROOT> element
    base_xpath = ".//" if root.tag != "ROOT" else "/ROOT/"
    quiz_items = root.xpath(f"{base_xpath}QUIZ_ITEM")

    # Extract main topic if available (adjusting for potential <ROOT>)
    main_topic_element = root if root.tag == "QUIZ_BANK" else root.find("./QUIZ_BANK")
    main_topic = (
        main_topic_element.get("topic", "") if main_topic_element is not None else ""
    )

    for item_index, item in enumerate(quiz_items):
        question_snippet = "[Question identification failed]"  # Default snippet
        try:
            # Extract question text first for better error logging
            question_element = item.find("./QUESTION")
            if question_element is None:
                print(
                    f"Warning: QUIZ_ITEM index {item_index} has no QUESTION element. Skipping."
                )
                skipped_count += 1
                continue

            # Convert question element to string including all children/HTML tags
            question_html = etree.tostring(
                question_element, encoding="unicode", method="html"
            )
            question_match = re.search(
                r"<QUESTION\b[^>]*>(.*?)</QUESTION>",
                question_html,
                re.DOTALL | re.IGNORECASE,
            )
            if question_match:
                question = question_match.group(1).strip()
            else:  # Fallback attempts
                question = "".join(question_element.itertext()).strip()
                if not question:
                    question = "".join(
                        etree.tostring(child, encoding="unicode", method="html")
                        for child in question_element
                    )

            question_snippet = question[:70].strip()  # Update snippet for logging

            # --- START: Check for Exactly 5 Options ---
            option_elements_found = item.xpath(
                './*[re:match(local-name(), "^OPTION[1-5]$", "i")]',
                namespaces={"re": "http://exslt.org/regular-expressions"},
            )
            all_option_tags = item.xpath('./*[starts-with(local-name(), "OPTION")]')

            if len(all_option_tags) != 5:
                print(
                    f"Error: Expected 5 options but found {len(all_option_tags)} for question '{question_snippet}...'. Skipping this item."
                )
                skipped_count += 1
                continue
            # Check if they are specifically OPTION1 to OPTION5 (case-insensitive tag check)
            option_numbers_found = {
                int(re.search(r"\d+", opt.tag).group())
                for opt in all_option_tags
                if re.search(r"\d+", opt.tag)
            }
            if option_numbers_found != {1, 2, 3, 4, 5}:
                print(
                    f"Error: Found 5 OPTION tags, but they are not numbered 1-5 (found {sorted(list(option_numbers_found))}) for question '{question_snippet}...'. Skipping this item."
                )
                skipped_count += 1
                continue
            # --- END: Check for Exactly 5 Options ---

            # Extract options (we know OPTION1-5 exist from the check above)
            options = []
            correct_index = 1

            for i in range(1, 6):
                # Find OPTIONi case-insensitively
                option_element = item.xpath(
                    f'./*[re:match(local-name(), "OPTION{i}", "i")]',
                    namespaces={"re": "http://exslt.org/regular-expressions"},
                )[0]

                # Convert option element to string including any HTML
                option_html = etree.tostring(
                    option_element, encoding="unicode", method="html"
                )
                tag_name = (
                    option_element.tag
                )  # Get the actual tag name (might be Option1, option1 etc)
                option_match = re.search(
                    rf"<{tag_name}\b[^>]*>(.*?)</{tag_name}>",
                    option_html,
                    re.DOTALL | re.IGNORECASE,
                )

                if option_match:
                    option_text = option_match.group(1).strip()
                else:  # Fallback attempts
                    option_text = "".join(option_element.itertext()).strip()
                    if not option_text:
                        option_text = "".join(
                            etree.tostring(child, encoding="unicode", method="html")
                            for child in option_element
                        )

                options.append(option_text)

                # Simple check: Option 1 should have correct="true" (case-insensitive)
                if i == 1 and str(option_element.get("correct", "")).lower() != "true":
                    print(
                        f"Warning: OPTION1 for question '{question_snippet}...' is missing correct='true' attribute or it's not set to 'true'."
                    )

            # Extract topic (case-insensitive)
            topic_element = item.xpath(
                './*[re:match(local-name(), "TOPIC", "i")]/text()',
                namespaces={"re": "http://exslt.org/regular-expressions"},
            )
            topic = "".join(topic_element).strip() if topic_element else main_topic

            quiz_data.append(
                {
                    "text": question,
                    "options": options,
                    "answerIndex": correct_index,
                    "topic": topic,
                    "chapter_no": chapter_no or "",
                    "CHAPTER_TITLE": chapter_title or "",
                }
            )

        except Exception as e:
            print(f"Error processing question '{question_snippet}...': {e}")
            skipped_count += 1
            continue

    df = pd.DataFrame(quiz_data)

    print(f"Successfully parsed {len(df)} questions.")
    # --- MODIFIED PART ---
    # Always print the skipped count, even if it's zero.
    print(
        f"Skipped {skipped_count} questions due to errors (e.g., incorrect option count)."
    )
    # --- END MODIFIED PART ---

    return df


# --- enhance_quiz_dataframe function remains unchanged ---
def enhance_quiz_dataframe(
    df,
    tag_mapping=None,
    chapter_no=None,
    chapter_title=None,
    difficulty_levels=None,
    time_estimates=None,
):
    """
    Enhance the quiz DataFrame with additional metadata

    Args:
        df (pd.DataFrame): Original quiz DataFrame
        tag_mapping (dict, optional): Mapping from topic to standardized tags
        chapter_no (str, optional): Chapter number to set for all questions
        chapter_title (str, optional): Chapter title to set for all questions
        difficulty_levels (dict, optional): Mapping from question index to difficulty level
        time_estimates (dict, optional): Mapping from question index to estimated completion time

    Returns:
        pd.DataFrame: Enhanced DataFrame
    """
    enhanced_df = df.copy()

    if chapter_no is not None:
        enhanced_df["chapter_no"] = chapter_no
    if chapter_title is not None:
        enhanced_df["CHAPTER_TITLE"] = chapter_title

    if tag_mapping is not None and "topic" in enhanced_df.columns:
        enhanced_df["tag"] = enhanced_df["topic"].map(lambda x: tag_mapping.get(x, x))
    if difficulty_levels is not None:
        enhanced_df["difficulty"] = enhanced_df.index.map(
            lambda i: difficulty_levels.get(i, "medium")
        )
    if time_estimates is not None:
        enhanced_df["time_estimate"] = enhanced_df.index.map(
            lambda i: time_estimates.get(i, 60)
        )
    return enhanced_df


# --- Example usage remains unchanged ---
if __name__ == "__main__":
    # Example XML content (would come from LLM)
    xml_content_good = """
    <QUIZ_BANK topic="Python Basics">
    <QUIZ_ITEM>
    <QUESTION>
    What will be the output of the following code?
    
    <pre><code class="language-python">
    x = 5
    y = 10
    print(x + y)
    </code></pre>
    </QUESTION>
    <OPTION1 correct="true">
    15
    </OPTION1>
    <OPTION2 correct="false">
    510
    </OPTION2>
    <OPTION3 correct="false">
    Error
    </OPTION3>
    <OPTION4 correct="false">
    None
    </OPTION4>
    <OPTION5 correct="false">
    5 + 10
    </OPTION5>
    <TOPIC>Basic Operations</TOPIC>
    </QUIZ_ITEM>
    </QUIZ_BANK>
    """

    xml_content_bad_options = """
    <QUIZ_BANK topic="Problematic Quiz">
     <QUIZ_ITEM>
    <QUESTION>This question is valid and has 5 options.</QUESTION>
    <OPTION1 correct="true">Correct</OPTION1>
    <OPTION2 correct="false">Wrong A</OPTION2>
    <OPTION3 correct="false">Wrong B</OPTION3>
    <OPTION4 correct="false">Wrong C</OPTION4>
    <OPTION5 correct="false">Wrong D</OPTION5>
    <TOPIC>Valid Question</TOPIC>
    </QUIZ_ITEM>
    <QUIZ_ITEM>
    <QUESTION>This question has too few options.</QUESTION>
    <OPTION1 correct="true">Correct</OPTION1>
    <OPTION2 correct="false">Wrong 1</OPTION2>
    <OPTION3 correct="false">Wrong 2</OPTION3>
    <OPTION4 correct="false">Wrong 3</OPTION4>
    <!-- Missing OPTION5 -->
    <TOPIC>Too Few Options</TOPIC>
    </QUIZ_ITEM>
    <QUIZ_ITEM>
    <QUESTION>This question has too many options.</QUESTION>
    <OPTION1 correct="true">Correct</OPTION1>
    <OPTION2 correct="false">Wrong X</OPTION2>
    <OPTION3 correct="false">Wrong Y</OPTION3>
    <OPTION4 correct="false">Wrong Z</OPTION4>
    <OPTION5 correct="false">Wrong W</OPTION5>
    <OPTION6 correct="false">Extra!</OPTION6> 
    <TOPIC>Too Many Options</TOPIC>
    </QUIZ_ITEM>
    </QUIZ_BANK>
    """

    print("--- Parsing Good XML ---")
    df_good = parse_quiz_xml_to_dataframe(
        xml_content_good, chapter_no="1", chapter_title="Introduction to Python"
    )
    print(df_good.head())
    print("\n--- Enhancing Good DataFrame ---")
    tag_mapping = {"Basic Operations": "arithmetic", "Control Flow": "flow-control"}
    difficulty_levels = {0: "easy", 1: "medium", 2: "hard"}
    enhanced_df_good = enhance_quiz_dataframe(
        df_good, tag_mapping=tag_mapping, difficulty_levels=difficulty_levels
    )
    print(enhanced_df_good.head())

    print("\n--- Parsing Problematic XML (Expect Skipped Questions) ---")
    df_bad = parse_quiz_xml_to_dataframe(
        xml_content_bad_options, chapter_no="X", chapter_title="Problems"
    )
    print("\nResulting DataFrame (should only contain the valid question):")
    print(df_bad)
