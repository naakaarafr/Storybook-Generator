from crewai import Agent
from config import llm
from tools import file_read_tool, generate_image_flux, convert_markdown_to_pdf

# Story Outliner Agent
def create_story_outliner(topic: str):
    return Agent(
        role='Story Outliner',
        goal=f'Develop an outline for a children\'s storybook about {topic}, including chapter titles and characters for 5 chapters.',
        backstory="An imaginative creator who lays the foundation of captivating stories for children. You specialize in creating engaging narratives that teach valuable lessons while entertaining young readers.",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

# Story Writer Agent
def create_story_writer(topic: str):
    return Agent(
        role='Story Writer',
        goal=f'Write the full content of the story about {topic} for all 5 chapters, each chapter 100 words, weaving together the narratives and characters outlined.',
        backstory="A talented storyteller who brings to life the world and characters outlined, crafting engaging and imaginative tales for children. You have a gift for creating age-appropriate content that captures young imaginations.",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

# Image Generator Agent
def create_image_generator():
    return Agent(
        role='Image Generator',
        goal='Generate one image per chapter content provided by the story writer. Create totally 5 images, one for each chapter. Each image should capture the essence of the chapter with detailed character and location information. If image generation fails, provide placeholder text descriptions.',
        backstory="A creative AI specialized in visual storytelling, bringing each chapter to life through imaginative imagery. You excel at creating whimsical, child-friendly illustrations that complement the narrative perfectly. When technical issues arise, you provide detailed image descriptions as fallbacks.",
        verbose=True,
        llm=llm,
        tools=[generate_image_flux],
        allow_delegation=False
    )

# Content Formatter Agent
def create_content_formatter():
    return Agent(
        role='Content Formatter',
        goal='Format the written story content in markdown, including images at the beginning of each chapter, following the template structure. Handle missing images gracefully by using placeholder descriptions.',
        backstory='A meticulous formatter who enhances the readability and presentation of the storybook. You ensure that the final product is professionally formatted and visually appealing for both digital and print formats. You adapt gracefully when images are unavailable.',
        verbose=True,
        llm=llm,
        tools=[file_read_tool],
        allow_delegation=False
    )

# PDF Converter Agent
def create_markdown_to_pdf_creator():
    return Agent(
        role='PDF Converter',
        goal='Convert the formatted Markdown file to a professional PDF document using available tools. Try multiple conversion methods if needed.',
        backstory='An efficient converter that transforms Markdown files into professionally formatted PDF documents. You ensure that all formatting and layout are preserved in the final PDF output. You have multiple conversion strategies available.',
        verbose=True,
        llm=llm,
        tools=[convert_markdown_to_pdf],
        allow_delegation=False
    )