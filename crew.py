from crewai import Crew, Process
from agents import (
    create_story_outliner,
    create_story_writer, 
    create_image_generator,
    create_content_formatter,
    create_markdown_to_pdf_creator
)
from tasks import create_tasks

def create_storybook_crew(topic: str):
    """
    Creates and returns the CrewAI crew for generating children's storybooks.
    
    Args:
        topic (str): The story topic chosen by the user
        
    Returns:
        Crew: Configured crew with all agents and tasks
    """
    # Create agents with the specified topic
    agents = {
        'story_outliner': create_story_outliner(topic),
        'story_writer': create_story_writer(topic),
        'image_generator': create_image_generator(),
        'content_formatter': create_content_formatter(),
        'markdown_to_pdf_creator': create_markdown_to_pdf_creator()
    }
    
    # Create tasks with the specified topic and agents
    tasks = create_tasks(topic, agents)
    
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=True,
        process=Process.sequential,
        memory=True,
        embedder={
            "provider": "google",
            "config": {
                "model": "models/embedding-001",
            }
        }
    )
    
    return crew

def run_storybook_generation(topic: str):
    """
    Executes the storybook generation process.
    
    Args:
        topic (str): The story topic chosen by the user
        
    Returns:
        str: Result of the crew execution
    """
    print(f"🚀 Starting Children's Storybook Generation about: {topic}")
    print("=" * 60)
    
    # Create the crew with the specified topic
    crew = create_storybook_crew(topic)
    
    # Execute the crew
    try:
        result = crew.kickoff()
        print("\n" + "=" * 60)
        print("✅ Storybook generation completed successfully!")
        print(f"📖 Generated storybook about: {topic}")
        print("📁 Check the generated files:")
        print("   - story.md (Markdown version)")
        print("   - story.pdf (PDF version)")
        print("   - Generated images in the current directory")
        return result
    except Exception as e:
        print(f"\n❌ Error during storybook generation: {str(e)}")
        return None