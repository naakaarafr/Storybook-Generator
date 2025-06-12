from crewai import Task
from config import OUTPUT_MARKDOWN

def create_tasks(topic: str, agents: dict):
    """
    Create all tasks with the specified topic and agents.
    
    Args:
        topic (str): The story topic chosen by the user
        agents (dict): Dictionary containing all the agent instances
        
    Returns:
        list: List of task instances
    """

    # Task 1: Create Story Outline
    task_outline = Task(
        description=f"""
        Create a comprehensive outline for a children's storybook about {topic}. 
        The outline should include:
        - A compelling story title related to {topic}
        - 5 chapter titles that flow logically
        - Detailed character descriptions (main characters and supporting characters)
        - Main plot points for each chapter
        - Setting descriptions appropriate for {topic}
        - Age-appropriate themes and lessons
        
        Make sure the story is engaging for children aged 4-8 years old and incorporates {topic} in meaningful ways.
        """,
        agent=agents['story_outliner'],
        expected_output=f"""
        A structured outline document containing:
        1. Story title related to {topic}
        2. Character profiles with names, descriptions, and roles
        3. 5 chapter titles with brief summaries
        4. Main plot points and story arc incorporating {topic}
        5. Setting descriptions
        6. Themes and educational value related to {topic}
        """
    )

    # Task 2: Write Full Story
    task_write = Task(
        description=f"""
        Using the outline provided, write the complete story content for all 5 chapters about {topic}.
        Requirements:
        - Each chapter should be approximately 100 words
        - Include the story title at the top
        - Ensure cohesive narrative flow between chapters
        - Use age-appropriate language and vocabulary
        - Include dialogue and descriptive elements
        - Maintain consistent character voices
        - Ensure each chapter has a clear beginning, middle, and conclusion
        - Incorporate {topic} meaningfully throughout the story
        - Write in a format that's ready for professional book layout
        """,
        agent=agents['story_writer'],
        expected_output=f"""
        A complete manuscript of the children's storybook about {topic} with:
        - Story title
        - 5 chapters, each approximately 100 words
        - Engaging dialogue and narration
        - Consistent character development
        - Clear story progression and resolution
        - Meaningful incorporation of {topic}
        - Professional formatting suitable for immediate PDF conversion
        """,
        context=[task_outline]
    )

    # Task 3: Generate Images
    task_image_generate = Task(
        description=f"""
        Generate 5 high-quality images for the children's storybook about {topic}, one for each chapter.
        For each image:
        - Use the chapter content and character details
        - Include detailed location information
        - Capture the key scene or moment from each chapter
        - Ensure images are child-friendly and engaging
        - Maintain consistent artistic style across all images
        - Generate images sequentially, one by one
        - Incorporate visual elements related to {topic}
        - Create images that will enhance the story when displayed in PDF format
        
        If image generation fails due to quota limits or technical issues:
        - Provide detailed placeholder descriptions for each chapter
        - Include character descriptions, setting details, and key visual elements
        - Make descriptions vivid enough that someone could visualize or draw the scene
        - Format descriptions as professional image captions
        
        Return either the file paths of generated images OR detailed placeholder descriptions.
        """,
        agent=agents['image_generator'],
        expected_output=f"""
        For each of the 5 chapters, either:
        - A valid image file path (if generation succeeds), OR
        - A detailed placeholder description starting with "PLACEHOLDER:" (if generation fails)
        
        Format:
        - Chapter 1: [image_path or detailed description]
        - Chapter 2: [image_path or detailed description]  
        - Chapter 3: [image_path or detailed description]
        - Chapter 4: [image_path or detailed description]
        - Chapter 5: [image_path or detailed description]
        
        Each should visually represent or describe the key elements of its respective chapter and incorporate {topic}.
        Images should be optimized for PDF display with proper resolution and formatting.
        """,
        context=[task_outline, task_write]
    )

    # Task 4: Format Content for Professional PDF
    task_format_content = Task(
        description=f"""
        Format the complete story content in a professional book layout suitable for high-quality PDF generation.
        
        Requirements:
        - Create a properly structured HTML document with embedded CSS for professional formatting
        - Include the story title as an elegant main header with decorative elements
        - Format each chapter with:
          * Professional chapter headings with consistent styling
          * Proper image placement (either actual images or styled placeholder descriptions)
          * Well-formatted text with appropriate line spacing and typography
          * Page break considerations for optimal reading flow
        - Use professional typography with:
          * Serif fonts for body text (Georgia, Times New Roman)
          * Sans-serif fonts for headings
          * Proper font sizes and spacing
          * Justified text alignment
        - Include CSS for:
          * Professional color scheme
          * Proper margins and padding
          * Print-ready formatting
          * Image styling and placement
          * Chapter break handling
        - Handle images gracefully:
          * Embed actual images with proper sizing and borders
          * Convert placeholder descriptions to elegant caption boxes
          * Maintain visual consistency throughout
        - Ensure the final document is print-ready and publication-quality
        
        Output should be a complete HTML document that converts seamlessly to professional PDF.
        """,
        agent=agents['content_formatter'],
        expected_output=f"""
        A professionally formatted HTML document containing:
        - Complete HTML structure with embedded CSS
        - Story title with elegant typography and styling
        - 5 chapters with:
          * Professional chapter headers
          * Properly formatted and placed images or styled captions
          * Well-typeset chapter content (~100 words each)
          * Consistent formatting throughout
        - Print-ready CSS with:
          * Professional color scheme and typography
          * Proper page margins and spacing
          * Optimized for PDF conversion
          * Mobile-responsive design as bonus
        - Publication-quality layout suitable for sharing or printing
        
        The document should look like a professionally published children's book.
        """,
        context=[task_write, task_image_generate],
        output_file=OUTPUT_MARKDOWN.replace('.md', '.html')  # Output as HTML instead of markdown
    )

    # Task 5: Convert to Professional PDF
    task_markdown_to_pdf = Task(
        description=f"""
        Convert the professionally formatted HTML document to a high-quality PDF suitable for printing and sharing.
        
        Requirements:
        - Use the formatted HTML document as input (not raw markdown)
        - Preserve all professional formatting, typography, and styling
        - Ensure images are properly embedded and sized
        - Handle page breaks elegantly
        - Create a print-ready document with:
          * Proper margins for binding
          * Consistent page layout
          * High-quality image rendering
          * Professional typography
        - Try multiple conversion methods in this order:
          1. WeasyPrint (best for complex layouts and CSS)
          2. Puppeteer/Playwright (if available)
          3. wkhtmltopdf (reliable fallback)
        - Provide detailed feedback on conversion success
        - If conversion fails, provide specific installation instructions
        - Ensure the final PDF is ready for:
          * Professional printing
          * Digital sharing
          * E-book reading
          * Archive storage
        
        The output should be a publication-quality PDF that looks like a professionally published children's book.
        """,
        agent=agents['markdown_to_pdf_creator'],
        expected_output=f"""
        Either:
        - A high-quality PDF file path (if conversion succeeds) with:
          * Professional book layout and typography
          * Properly embedded and sized images
          * Consistent formatting throughout
          * Print-ready quality suitable for publication
          * Optimized file size for sharing
        
        OR (if conversion fails):
        - Clear error message with specific tool installation instructions
        - Confirmation that the HTML file was created successfully
        - Alternative conversion methods and online tools
        - Detailed troubleshooting steps
        
        The PDF should be indistinguishable from a professionally published children's book,
        suitable for printing, sharing, or commercial use.
        """,
        context=[task_format_content]
    )
    
    return [task_outline, task_write, task_image_generate, task_format_content, task_markdown_to_pdf]