import pandas as pd
from lxml import etree
from io import StringIO
import re


def parse_quiz_xml_to_dataframe(xml_content, chapter_no=None, chapter_title=None):
    """
    Parse XML quiz content and convert it to a pandas DataFrame.
    Enforces that each QUIZ_ITEM must contain exactly 5 OPTION elements (OPTION1-OPTION5).
    Extracts QUESTION, OPTIONS, TOPIC, and an optional TAG.

    Args:
        xml_content (str): XML string containing quiz questions in the expected format.
        chapter_no (str, optional): Chapter number to associate with all questions.
        chapter_title (str, optional): Chapter title to associate with all questions.

    Returns:
        pd.DataFrame: DataFrame with columns: 'text', 'options', 'answerIndex',
                      'topic', 'tag', 'chapter_no', 'CHAPTER_TITLE'.
                      Returns an empty DataFrame if parsing fails completely.
    """
    # Clean up potential XML issues (prolog, surrounding text)
    xml_content = re.sub(r"^.*?<QUIZ_BANK", "<QUIZ_BANK", xml_content, flags=re.DOTALL)
    xml_content = re.sub(
        r"</QUIZ_BANK>.*?$", "</QUIZ_BANK>", xml_content, flags=re.DOTALL
    )
    # Remove XML declaration which can sometimes interfere with lxml fragment parsing
    xml_content = re.sub(r"<\?xml.*?\?>", "", xml_content).strip()

    # Parse the XML using lxml for robustness
    try:
        # Use encoding='utf-8' and recover=True
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        # Use StringIO to handle the string input correctly with the parser
        # Encoding the string to bytes first is crucial for the parser's encoding declaration
        root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)

        # Basic validation after parsing
        if root is None or root.tag.upper() != "QUIZ_BANK":
            # If recovery wrapped it in a bogus root, try finding QUIZ_BANK
            if root is not None and root.find(".//QUIZ_BANK") is not None:
                root = root.find(".//QUIZ_BANK")
            else:
                raise ValueError(
                    "Root <QUIZ_BANK> element not found or invalid after parsing."
                )

    except Exception as e:
        print(f"Fatal XML parsing error: {e}")
        # Attempt recovery by wrapping in a dummy root if needed (less common now)
        # This should ideally not be needed with fromstring and proper encoding handling
        # but kept as a fallback concept if structure is severely broken.
        # If initial parsing failed badly, return empty DF.
        if "parser" not in locals() or (
            hasattr(parser, "error_log") and parser.error_log
        ):
            print(f"Parser errors: {getattr(parser, 'error_log', 'Unknown')}")
        return pd.DataFrame()

    # Prepare data structure
    quiz_data = []
    skipped_count = 0

    # Find all QUIZ_ITEM elements
    quiz_items = root.xpath(
        ".//QUIZ_ITEM"
    )  # Use .// to be robust against nesting variations

    # Extract main topic if available
    main_topic = root.get("topic", "")

    for item_index, item in enumerate(quiz_items):
        question_snippet = "[Question identification failed]"  # Default snippet
        try:
            # --- Extract QUESTION (mandatory) ---
            question_element = item.find("./QUESTION")
            if question_element is None:
                print(
                    f"Warning: QUIZ_ITEM index {item_index} has no QUESTION element. Skipping."
                )
                skipped_count += 1
                continue

            # Convert question element to string including all children/HTML tags
            # Using method='html' often helps preserve nested tags better than 'xml'
            question_html = etree.tostring(
                question_element, encoding="unicode", method="html"
            )
            # Extract content *within* the <QUESTION> tags
            question_match = re.search(
                r"<question\b[^>]*>(.*?)</question>",  # Case-insensitive tag matching
                question_html,
                re.DOTALL | re.IGNORECASE,
            )
            if question_match:
                question = question_match.group(1).strip()
            else:  # Fallback if regex fails (e.g., self-closing or unusual structure)
                print(
                    f"Warning: Could not extract question content via regex for item {item_index}. Falling back to itertext."
                )
                question = "".join(question_element.itertext()).strip()
                # If still empty, try capturing inner HTML as last resort
                if not question:
                    question = "".join(
                        etree.tostring(child, encoding="unicode", method="html")
                        for child in question_element
                    )

            question_snippet = question[:70].strip()  # Update snippet for logging

            # --- Validate Exactly 5 Options (OPTION1 to OPTION5) ---
            # Use XPath with regex for case-insensitive tag matching (OPTION1, Option1, option1 etc.)
            # This finds *any* element whose tag name matches OPTION[1-5] case-insensitively
            option_elements_found = item.xpath(
                './*[re:match(local-name(), "^OPTION[1-5]$", "i")]',
                namespaces={"re": "http://exslt.org/regular-expressions"},
            )
            # Also check for *any* tag starting with OPTION (to catch OPTION6, etc.)
            all_option_tags = item.xpath(
                './*[starts-with(local-name(), "OPTION") or starts-with(local-name(), "option")]'
            )

            if len(all_option_tags) != 5:
                print(
                    f"Error: Expected 5 options but found {len(all_option_tags)} for question '{question_snippet}...'. Skipping this item."
                )
                skipped_count += 1
                continue

            # Verify the 5 tags found are indeed OPTION1 through OPTION5 (case-insensitive check is implicit in the first XPath)
            # Extract the number from the tag name for robust checking
            option_numbers_found = set()
            valid_options_1_to_5 = True
            for opt_el in option_elements_found:
                # Use regex to find number at the end of the tag name, case-insensitive
                match = re.search(r"(\d+)$", opt_el.tag, re.IGNORECASE)
                if match:
                    option_numbers_found.add(int(match.group(1)))
                else:
                    valid_options_1_to_5 = False
                    break

            if not valid_options_1_to_5 or option_numbers_found != {1, 2, 3, 4, 5}:
                found_tags_str = sorted(
                    [opt.tag for opt in all_option_tags]
                )  # Show actual tags found
                print(
                    f"Error: Found 5 tags starting with 'OPTION', but they are not exactly OPTION1-5 (found tags: {found_tags_str}, extracted numbers: {sorted(list(option_numbers_found))}) for question '{question_snippet}...'. Skipping this item."
                )
                skipped_count += 1
                continue
            # --- End Option Validation ---

            # --- Extract Options (we now know OPTION1-5 exist) ---
            options = []
            correct_index = 1  # Per specification, OPTION1 is always correct

            for i in range(1, 6):
                # Find OPTIONi case-insensitively (guaranteed to find one by checks above)
                option_element = item.xpath(
                    f'./*[re:match(local-name(), "OPTION{i}", "i")]',
                    namespaces={"re": "http://exslt.org/regular-expressions"},
                )[0]

                # Convert option element to string including any inner HTML
                option_html = etree.tostring(
                    option_element, encoding="unicode", method="html"
                )
                tag_name = (
                    option_element.tag
                )  # Get the actual tag name (e.g., OPTION1, Option1)
                # Extract content *within* the option tags
                option_match = re.search(
                    rf"<{tag_name}\b[^>]*>(.*?)</{tag_name}>",  # Use actual tag name
                    option_html,
                    re.DOTALL | re.IGNORECASE,
                )

                if option_match:
                    option_text = option_match.group(1).strip()
                else:  # Fallback
                    print(
                        f"Warning: Could not extract option {i} content via regex for item {item_index}. Falling back to itertext."
                    )
                    option_text = "".join(option_element.itertext()).strip()
                    if (
                        not option_text
                    ):  # Last resort for potentially empty tags with children
                        option_text = "".join(
                            etree.tostring(child, encoding="unicode", method="html")
                            for child in option_element
                        )

                options.append(option_text)

                # Check correct attribute on OPTION1
                if i == 1 and str(option_element.get("correct", "")).lower() != "true":
                    print(
                        f"Warning: OPTION1 for question '{question_snippet}...' is missing correct='true' attribute or it's not set to 'true'."
                    )
                # Check incorrect attribute on OPTION2-5
                elif (
                    i > 1 and str(option_element.get("correct", "")).lower() != "false"
                ):
                    print(
                        f"Warning: OPTION{i} for question '{question_snippet}...' is missing correct='false' attribute or it's not set to 'false'."
                    )

            # --- Extract TOPIC (optional, fallback to main topic) ---
            # Case-insensitive search for TOPIC tag
            topic_element = item.xpath(
                './*[re:match(local-name(), "TOPIC", "i")]/text()',
                namespaces={"re": "http://exslt.org/regular-expressions"},
            )
            topic = "".join(topic_element).strip() if topic_element else main_topic

            # --- Extract TAG (optional) ---
            # Case-insensitive search for TAG tag
            tag_element = item.xpath(
                './*[re:match(local-name(), "TAG", "i")]/text()',
                namespaces={"re": "http://exslt.org/regular-expressions"},
            )
            tag = (
                "".join(tag_element).strip() if tag_element else ""
            )  # Default to empty string if not found

            # --- Append data for this valid item ---
            quiz_data.append(
                {
                    "text": question,
                    "options": options,
                    "answerIndex": correct_index,
                    "topic": topic,
                    "tag": tag,  # Added tag column
                    "chapter_no": chapter_no or "",
                    "CHAPTER_TITLE": chapter_title or "",
                }
            )

        except Exception as e:
            # Catch unexpected errors during processing of a single item
            print(
                f"Error processing question '{question_snippet}...': {e.__class__.__name__}: {e}"
            )
            skipped_count += 1
            continue  # Skip to the next QUIZ_ITEM

    # Create DataFrame from collected data
    df = pd.DataFrame(quiz_data)

    # Print summary statistics
    if not quiz_items and xml_content:  # Check if xml_content was non-empty
        print("Warning: No <QUIZ_ITEM> elements found in the XML content.")
    elif not xml_content:
        print("Warning: Input XML content was empty.")

    print(f"Successfully parsed {len(df)} questions.")
    # Always print the skipped count.
    print(
        f"Skipped {skipped_count} questions due to errors (e.g., incorrect option count, missing question, XML errors)."
    )

    # Ensure essential columns exist even if df is empty
    expected_cols = [
        "text",
        "options",
        "answerIndex",
        "topic",
        "tag",
        "chapter_no",
        "CHAPTER_TITLE",
    ]
    for col in expected_cols:
        if col not in df.columns:
            # Use appropriate empty type for pandas >= 1.0
            if col == "options":
                df[col] = [
                    [] for _ in range(len(df))
                ]  # Or pd.NA if appropriate for list column handling later
            elif col == "answerIndex":
                df[col] = pd.NA  # Use pandas NA for numeric index
            else:
                df[col] = ""  # Empty string for text columns

    # Reorder columns to a standard format only if df is not empty
    if not df.empty:
        df = df[expected_cols]

    return df


# --- enhance_quiz_dataframe function (CORRECTED) ---
def enhance_quiz_dataframe(
    df,
    tag_mapping=None,
    chapter_no=None,
    chapter_title=None,
    difficulty_levels=None,
    time_estimates=None,
):
    """
    Enhance the quiz DataFrame with additional metadata.

    Args:
        df (pd.DataFrame): Original quiz DataFrame (should include 'topic' and 'tag' columns).
        tag_mapping (dict, optional): Mapping from topic to standardized tags.
                                     If provided, this will potentially overwrite the 'tag' column
                                     based on 'topic'. If a topic has no mapping, the original tag is kept.
        chapter_no (str, optional): Chapter number to set for all questions.
        chapter_title (str, optional): Chapter title to set for all questions.
        difficulty_levels (dict, optional): Mapping from DataFrame index to difficulty level.
        time_estimates (dict, optional): Mapping from DataFrame index to estimated completion time.

    Returns:
        pd.DataFrame: Enhanced DataFrame.
    """
    if df.empty:
        print("Warning: Cannot enhance an empty DataFrame.")
        # Return an empty DataFrame with expected columns if possible
        cols = [
            "text",
            "options",
            "answerIndex",
            "topic",
            "tag",
            "chapter_no",
            "CHAPTER_TITLE",
            "difficulty",
            "time_estimate",
        ]
        return pd.DataFrame(columns=cols)

    enhanced_df = df.copy()

    # Ensure core columns exist from parsing before enhancing
    for core_col in ["topic", "tag"]:
        if core_col not in enhanced_df.columns:
            enhanced_df[core_col] = ""  # Add empty if somehow missing

    if chapter_no is not None:
        enhanced_df["chapter_no"] = chapter_no
    if chapter_title is not None:
        enhanced_df["CHAPTER_TITLE"] = chapter_title

    # Apply tag mapping based on 'topic'. (CORRECTED LOGIC)
    if tag_mapping is not None and "topic" in enhanced_df.columns:
        # Function to apply: Use mapping if topic exists, otherwise keep original tag
        def get_mapped_tag_or_original(row):
            # Use row['tag'] (the original value) as the default if topic not in mapping
            return tag_mapping.get(row["topic"], row["tag"])

        # Apply this function row-wise using .apply()
        enhanced_df["tag"] = enhanced_df.apply(get_mapped_tag_or_original, axis=1)

    # Apply difficulty levels based on DataFrame index
    if difficulty_levels is not None:
        enhanced_df["difficulty"] = enhanced_df.index.map(
            lambda i: difficulty_levels.get(i, "medium")  # Default to medium
        )
    elif "difficulty" not in enhanced_df.columns:
        enhanced_df["difficulty"] = "medium"  # Add default if column missing

    # Apply time estimates based on DataFrame index
    if time_estimates is not None:
        enhanced_df["time_estimate"] = enhanced_df.index.map(
            lambda i: time_estimates.get(i, 60)  # Default to 60 seconds
        )
    elif "time_estimate" not in enhanced_df.columns:
        enhanced_df["time_estimate"] = 60  # Add default if column missing

    # Ensure standard columns are present after potential enhancements
    final_cols = [
        "text",
        "options",
        "answerIndex",
        "topic",
        "tag",
        "chapter_no",
        "CHAPTER_TITLE",
        "difficulty",
        "time_estimate",
    ]
    for col in final_cols:
        if col not in enhanced_df.columns:
            # Add missing enhancement columns with appropriate defaults if necessary
            if col == "difficulty":
                enhanced_df[col] = "medium"
            elif col == "time_estimate":
                enhanced_df[col] = 60
            # Core columns ('text', 'options', etc.) should exist from parsing or initial check
            # 'tag' should exist from parsing or the 'elif' block above if mapping was None

    # Reorder to include potential new columns
    # Filter out columns not present if enhancement options were None
    present_cols = [col for col in final_cols if col in enhanced_df.columns]
    enhanced_df = enhanced_df[present_cols]

    return enhanced_df


# --- Example usage (updated to include TAG) ---
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
    <TAG>Arithmetic Addition</TAG>
    </QUIZ_ITEM>
    <QUIZ_ITEM>
    <QUESTION>What is a docstring?</QUESTION>
    <OPTION1 correct="true">A string literal for documenting Python code</OPTION1>
    <OPTION2 correct="false">A type of variable</OPTION2>
    <OPTION3 correct="false">A reserved keyword</OPTION3>
    <OPTION4 correct="false">A syntax error</OPTION4>
    <OPTION5 correct="false">An external library</OPTION5>
    <TOPIC>Python Fundamentals</TOPIC>
    <TAG>Documentation</TAG> <!-- Added a tag here for demo -->
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
    <TAG>Valid Tag</TAG>
    </QUIZ_ITEM>
    <QUIZ_ITEM>
    <QUESTION>This question has too few options.</QUESTION>
    <OPTION1 correct="true">Correct</OPTION1>
    <OPTION2 correct="false">Wrong 1</OPTION2>
    <OPTION3 correct="false">Wrong 2</OPTION3>
    <OPTION4 correct="false">Wrong 3</OPTION4>
    <!-- Missing OPTION5 -->
    <TOPIC>Too Few Options</TOPIC>
    <TAG>Invalid Structure</TAG>
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
    <TAG>Invalid Structure</TAG>
    </QUIZ_ITEM>
    </QUIZ_BANK>
    """

    print("--- Parsing Good XML (with tags) ---")
    df_good = parse_quiz_xml_to_dataframe(
        xml_content_good, chapter_no="1", chapter_title="Introduction to Python"
    )
    print(df_good[["text", "topic", "tag"]].head())  # Show relevant columns

    print("\n--- Enhancing Good DataFrame ---")
    # Note: tag_mapping will overwrite the parsed tag ONLY if the topic matches
    tag_mapping = {
        "Basic Operations": "mapped-arithmetic",  # Maps topic to a new tag
        # "Python Fundamentals" is NOT in the mapping
    }
    difficulty_levels = {0: "easy", 1: "medium"}  # Index-based difficulty
    enhanced_df_good = enhance_quiz_dataframe(
        df_good,
        tag_mapping=tag_mapping,
        difficulty_levels=difficulty_levels,
        time_estimates={0: 30, 1: 45},  # Index-based time
    )
    print(
        "DataFrame AFTER enhancement (notice tag for 'Basic Operations' changed, 'Documentation' tag kept):"
    )
    print(
        enhanced_df_good[["text", "topic", "tag", "difficulty", "time_estimate"]].head()
    )

    print("\n--- Parsing Problematic XML (Expect Skipped Questions) ---")
    df_bad = parse_quiz_xml_to_dataframe(
        xml_content_bad_options, chapter_no="X", chapter_title="Problems"
    )
    print("\nResulting DataFrame (should only contain the valid question):")
    # Check if df_bad is not empty before trying to print columns
    if not df_bad.empty:
        print(df_bad[["text", "topic", "tag"]])  # Show relevant columns
    else:
        print("DataFrame is empty as expected.")
