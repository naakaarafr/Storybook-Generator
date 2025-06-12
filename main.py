#!/usr/bin/env python3
"""
Children's Storybook Generator
=============================

This application uses CrewAI with Gemini Flash 2.0 and FLUX.1-dev to generate
illustrated children's storybooks about any topic.

Requirements:
- GOOGLE_API_KEY environment variable
- HUGGINGFACE_API_KEY environment variable
- At least one PDF conversion tool (mdpdf, weasyprint, or pdfkit)

Usage:
    python main.py
"""

import os
import sys
import time
from crew import run_storybook_generation
from tools import check_pdf_tools
from config import validate_config, print_api_status, get_api_status

def get_story_topic():
    """Get the story topic from the user with suggestions."""
    print("\n📚 What topic would you like your children's storybook to be about?")
    print("\n💡 Here are some popular topics for inspiration:")
    print("   • Animals (farm animals, jungle animals, pets)")
    print("   • Space and planets")
    print("   • Friendship and kindness")
    print("   • Ocean and sea creatures")
    print("   • Magic and fairy tales")
    print("   • Dinosaurs")
    print("   • Transportation (cars, trains, airplanes)")
    print("   • Family and home")
    print("   • Nature and environment")
    print("   • Superheroes")
    print("   • Food and cooking")
    print("   • Sports and games")
    
    while True:
        topic = input("\n✏️  Enter your story topic: ").strip()
        
        if not topic:
            print("❌ Please enter a topic for your story.")
            continue
            
        if len(topic.split()) > 10:
            print("❌ Please keep the topic shorter (10 words or less).")
            continue
            
        # Confirm the topic
        print(f"\n📖 You chose: '{topic}'")
        confirm = input("Is this correct? (y/n): ").lower().strip()
        
        if confirm in ['y', 'yes']:
            return topic
        elif confirm in ['n', 'no']:
            print("Let's try again!")
            continue
        else:
            print("Please enter 'y' for yes or 'n' for no.")
            continue

def check_environment():
    """Check if required environment variables are set."""
    return validate_config()

def check_system_requirements():
    """Check PDF conversion tools and provide recommendations."""
    print("\n🔍 Checking system requirements...")
    
    pdf_tools = check_pdf_tools()
    
    if not any(pdf_tools.values()):
        print("⚠️  No PDF conversion tools found!")
        print("\nTo enable PDF generation, install one of:")
        print("1. mdpdf (recommended): pip install mdpdf")
        print("2. weasyprint: pip install weasyprint")
        print("3. pdfkit + wkhtmltopdf")
        print("\n📄 Don't worry - the markdown file will still be created!")
        
        proceed = input("\nContinue without PDF generation? (y/n): ").lower().strip()
        if proceed not in ['y', 'yes']:
            print("Please install a PDF conversion tool and run again.")
            return False
    else:
        available = [tool for tool, status in pdf_tools.items() if status]
        print(f"✅ PDF conversion tools available: {', '.join(available)}")
    
    return True

def create_template_file():
    """Create a basic template file if it doesn't exist."""
    template_content = """# {Story Title}

## Chapter 1: {Chapter Title}
![Chapter 1 Image]({image_path})

{Chapter content goes here...}

## Chapter 2: {Chapter Title}
![Chapter 2 Image]({image_path})

{Chapter content goes here...}

## Chapter 3: {Chapter Title}
![Chapter 3 Image]({image_path})

{Chapter content goes here...}

## Chapter 4: {Chapter Title}
![Chapter 4 Image]({image_path})

{Chapter content goes here...}

## Chapter 5: {Chapter Title}
![Chapter 5 Image]({image_path})

{Chapter content goes here...}
"""
    
    if not os.path.exists("template.md"):
        with open("template.md", "w") as f:
            f.write(template_content)
        print("📝 Created template.md file")

def show_rate_limit_info():
    """Show information about rate limits and usage"""
    print("\n📊 Rate Limiting Information:")
    print("   • Gemini API: 15 requests per minute (conservative)")
    print("   • Automatic retry with exponential backoff")
    print("   • Intelligent waiting between failed requests")
    print("   • Progress tracking and status updates")
    
    status = get_api_status()
    if status['requests_today'] > 0:
        print(f"\n📈 Today's Usage:")
        print(f"   • Total requests: {status['requests_today']}")
        print(f"   • Current minute: {status['rate_limit_requests']}/15")

def handle_quota_exceeded():
    """Handle quota exceeded scenarios"""
    print("\n💡 If you encounter quota issues:")
    print("   1. Wait for the next billing cycle to reset")
    print("   2. Check your Google AI Studio dashboard")
    print("   3. Consider upgrading your plan if needed")
    print("   4. The app will automatically retry with proper delays")
    
    print("\n🔗 Useful Links:")
    print("   • Google AI Studio: https://aistudio.google.com/")
    print("   • Gemini API Quotas: https://ai.google.dev/gemini-api/docs/rate-limits")

def main():
    """Main function to run the storybook generator."""
    print("🐾 Interactive Children's Storybook Generator")
    print("=" * 50)
    print("Powered by:")
    print("  • Gemini Flash 2.0 (Google)")
    print("  • FLUX.1-dev (Hugging Face)")
    print("  • CrewAI Framework")
    print("=" * 50)
    
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    # Show rate limiting info
    show_rate_limit_info()
    
    # Check system requirements
    if not check_system_requirements():
        sys.exit(1)
    
    # Create template file if needed
    create_template_file()
    
    # Get story topic from user
    topic = get_story_topic()
    
    print(f"\n🎨 Creating a wonderful storybook about '{topic}' for you!")
    print("⏳ This may take several minutes due to rate limiting...")
    print("   📝 Writing story outline and chapters")
    print("   🎨 Generating images (or creating descriptions)")
    print("   📄 Formatting content")
    print("   📋 Converting to PDF")
    print("\n⚠️  Note: The process will automatically handle rate limits")
    print("   and wait between requests to avoid quota issues.")
    
    # Show initial API status
    print_api_status()
    
    # Ask user if they want to continue knowing the time it might take
    proceed = input("\n🚀 Ready to start generation? This might take 5-15 minutes. (y/n): ").lower().strip()
    if proceed not in ['y', 'yes']:
        print("👋 Generation cancelled. Run again when ready!")
        return
    
    start_time = time.time()
    
    try:
        # Run the storybook generation with the chosen topic
        result = run_storybook_generation(topic)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result:
            print(f"\n📋 Generation completed in {duration/60:.1f} minutes!")
            print(f"🎉 Your '{topic}' storybook is ready!")
            print("📖 Perfect for children aged 4-8 years old")
            print("\n📁 Generated files:")
            
            # Check what files were actually created
            if os.path.exists("story.md"):
                print("   ✅ story.md (Markdown version)")
            if os.path.exists("story.pdf"):
                print("   ✅ story.pdf (PDF version)")
            
            # Check for generated images
            image_files = [f for f in os.listdir('.') if f.endswith('.png') and not f.startswith('template')]
            if image_files:
                print(f"   ✅ {len(image_files)} generated images")
            else:
                print("   ℹ️  Image descriptions included (images not generated)")
            
            # Show final API usage
            print_api_status()
            print(f"\n🌟 Final Result Summary:\n{result}")
            
        else:
            print(f"\n❌ Storybook generation encountered issues after {duration/60:.1f} minutes.")
            print("📄 Check if story.md was created - you can still use the content!")
            if os.path.exists("story.md"):
                print("✅ Markdown file was created successfully")
                print("💡 You can convert it to PDF manually using online tools")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user.")
        print("📄 Check if any partial files were created.")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Unexpected error: {error_msg}")
        
        if "quota" in error_msg.lower() or "429" in error_msg:
            handle_quota_exceeded()
        else:
            print("💡 Try running the generator again, or check the error logs.")
        
        # Show API status even on error
        try:
            print_api_status()
        except:
            pass
    
    finally:
        # Clean up and show final status
        try:
            print("\n" + "="*50)
            print("Thank you for using the Children's Storybook Generator!")
            print("="*50)
        except:
            pass

if __name__ == "__main__":
    main()