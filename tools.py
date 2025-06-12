import os
import re
import requests
import subprocess
import shutil
from crewai_tools import tool
from crewai_tools.tools import FileReadTool
from config import HF_API_URL, HF_HEADERS, TEMPLATE_FILE
from PIL import Image
from io import BytesIO
import markdown
import tempfile
import platform
import html

# File reading tool
file_read_tool = FileReadTool(
    file_path=TEMPLATE_FILE,
    description='A tool to read the Story Template file and understand the expected output format.'
)

@tool
def generate_image_flux(chapter_content_and_character_details: str) -> str:
    """
    Generates an image for a given chapter using FLUX.1-dev model from Hugging Face.
    Saves it in the current folder and returns the image path.
    If generation fails, returns a descriptive placeholder.
    
    Args:
        chapter_content_and_character_details (str): Content describing the chapter scene and characters
        
    Returns:
        str: Path to the generated image file or placeholder description
    """
    try:
        # Create a detailed prompt for FLUX
        prompt = f"""
        {chapter_content_and_character_details}
        
        Style: Children's storybook illustration with vivid colors, especially azure and emerald tones with gold accents. 
        The illustration should have the whimsical quality of early 20th-century storybook art, 
        blending realism with fantasy elements. Rich textures, soft luminous lighting, 
        magical atmosphere with depth and dimensionality. No text in the image.
        """
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "guidance_scale": 7.5,
                "num_inference_steps": 50,
                "width": 1024,
                "height": 1024
            }
        }
        
        print(f"🎨 Generating image for: {chapter_content_and_character_details[:50]}...")
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
        
        if response.status_code == 200:
            # Generate filename from content
            words = chapter_content_and_character_details.split()[:5]
            safe_words = [re.sub(r'[^a-zA-Z0-9_]', '', word) for word in words]
            filename = "_".join(safe_words).lower() + ".png"
            filepath = os.path.join(os.getcwd(), filename)
            
            # Save the image
            image = Image.open(BytesIO(response.content))
            image.save(filepath)
            
            print(f"✅ Image saved: {filepath}")
            return filepath
        else:
            print(f"❌ Failed to generate image. Status code: {response.status_code}")
            if response.status_code == 429:
                print("⚠️  Rate limit exceeded. Using placeholder description.")
            elif response.status_code == 503:
                print("⚠️  Service temporarily unavailable. Using placeholder description.")
            else:
                print(f"Response: {response.text}")
            
            # Return placeholder description
            return f"PLACEHOLDER: {chapter_content_and_character_details[:100]}..."
            
    except requests.exceptions.Timeout:
        print("⚠️  Request timeout. Using placeholder description.")
        return f"PLACEHOLDER: {chapter_content_and_character_details[:100]}..."
    except Exception as e:
        print(f"❌ Error generating image: {str(e)}")
        return f"PLACEHOLDER: {chapter_content_and_character_details[:100]}..."

def setup_fontconfig():
    """Setup fontconfig environment to avoid font errors."""
    try:
        # Check if we're in a problematic environment
        if platform.system() == "Linux":
            # Try to find system fonts
            font_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                "/System/Library/Fonts",  # macOS
                "/Library/Fonts",  # macOS
                os.path.expanduser("~/.fonts")
            ]
            
            # Set FONTCONFIG_PATH if not set
            if not os.environ.get('FONTCONFIG_PATH'):
                for font_dir in font_dirs:
                    if os.path.exists(font_dir):
                        os.environ['FONTCONFIG_PATH'] = font_dir
                        break
            
            # Create a minimal fontconfig if needed
            if not os.environ.get('FONTCONFIG_FILE'):
                fontconfig_content = '''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/usr/share/fonts</dir>
  <dir>/usr/local/share/fonts</dir>
  <dir>~/.fonts</dir>
  <alias>
    <family>sans-serif</family>
    <prefer>
      <family>DejaVu Sans</family>
      <family>Liberation Sans</family>
      <family>Arial</family>
    </prefer>
  </alias>
  <alias>
    <family>serif</family>
    <prefer>
      <family>DejaVu Serif</family>
      <family>Liberation Serif</family>
      <family>Times New Roman</family>
    </prefer>
  </alias>
  <alias>
    <family>monospace</family>
    <prefer>
      <family>DejaVu Sans Mono</family>
      <family>Liberation Mono</family>
      <family>Courier New</family>
    </prefer>
  </alias>
</fontconfig>'''
                
                # Create temporary fontconfig file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                    f.write(fontconfig_content)
                    os.environ['FONTCONFIG_FILE'] = f.name
                    
        return True
    except Exception as e:
        print(f"⚠️  Could not setup fontconfig: {e}")
        return False

def check_pdf_tools():
    """Check which PDF conversion tools are available."""
    tools_available = {}
    
    # Check mdpdf
    try:
        subprocess.run(['mdpdf', '--help'], capture_output=True, check=True)
        tools_available['mdpdf'] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        tools_available['mdpdf'] = False
    
    # Check wkhtmltopdf (for pdfkit)
    try:
        subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, check=True)
        tools_available['wkhtmltopdf'] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        tools_available['wkhtmltopdf'] = False
    
    # Check weasyprint
    try:
        import weasyprint
        tools_available['weasyprint'] = True
    except ImportError:
        tools_available['weasyprint'] = False
    
    return tools_available

def preprocess_markdown(md_content: str) -> str:
    """
    Preprocess the markdown content to handle images and formatting better.
    """
    # Handle image placeholders - convert PLACEHOLDER descriptions to styled text
    def replace_placeholder_images(match):
        alt_text = match.group(1) if match.group(1) else "Chapter Image"
        src = match.group(2)
        
        if src.startswith("PLACEHOLDER:"):
            # Convert placeholder to styled description
            description = src.replace("PLACEHOLDER:", "").strip()
            return f'<div class="image-placeholder"><em>📖 {description}</em></div>'
        else:
            # Keep regular images
            return f'<img src="{src}" alt="{alt_text}" class="chapter-image">'
    
    # Replace markdown images with processed versions
    md_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_placeholder_images, md_content)
    
    # Ensure proper chapter breaks
    md_content = re.sub(r'^## (Chapter \d+[^#\n]*)', r'<div class="chapter-break"></div>\n## \1', md_content, flags=re.MULTILINE)
    
    return md_content

def get_enhanced_css():
    """Get enhanced CSS for better PDF formatting."""
    return """
    <style>
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "Children's Storybook";
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
            max-width: none;
            margin: 0;
            padding: 0;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 24pt;
            text-align: center;
            margin: 0 0 30pt 0;
            padding: 20pt 0;
            border-bottom: 3pt solid #3498db;
            page-break-after: avoid;
        }
        
        h2 {
            color: #34495e;
            font-size: 18pt;
            margin: 30pt 0 15pt 0;
            padding: 10pt 0 5pt 15pt;
            border-left: 4pt solid #3498db;
            background-color: #f8f9fa;
            page-break-after: avoid;
        }
        
        .chapter-break {
            page-break-before: always;
            height: 0;
        }
        
        .chapter-break:first-child {
            page-break-before: auto;
        }
        
        p {
            margin: 0 0 12pt 0;
            text-align: justify;
            text-indent: 20pt;
            orphans: 2;
            widows: 2;
        }
        
        .chapter-image {
            display: block;
            max-width: 100%;
            height: auto;
            margin: 20pt auto;
            border: 1pt solid #ddd;
            border-radius: 8pt;
            box-shadow: 0 2pt 4pt rgba(0,0,0,0.1);
        }
        
        .image-placeholder {
            margin: 20pt 0;
            padding: 15pt;
            background-color: #f0f8ff;
            border: 2pt dashed #3498db;
            border-radius: 8pt;
            text-align: center;
        }
        
        .image-placeholder em {
            font-style: italic;
            color: #2c3e50;
            font-size: 11pt;
            line-height: 1.4;
        }
        
        /* Table of Contents styling if present */
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        li {
            margin: 5pt 0;
            padding: 5pt 0;
            border-bottom: 1pt dotted #ccc;
        }
        
        /* Ensure good page breaks */
        h1, h2 {
            page-break-after: avoid;
        }
        
        p {
            page-break-inside: avoid;
        }
        
        .chapter-image, .image-placeholder {
            page-break-inside: avoid;
        }
        
        /* Print-specific adjustments */
        @media print {
            body {
                font-size: 11pt;
            }
            
            h1 {
                font-size: 22pt;
            }
            
            h2 {
                font-size: 16pt;
            }
        }
    </style>
    """

def convert_with_mdpdf(markdown_file_name: str, output_file: str) -> bool:
    """Try converting with mdpdf - enhanced version."""
    try:
        print("🔄 Trying mdpdf...")
        
        # Read and preprocess markdown
        with open(markdown_file_name, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Create a temporary processed markdown file
        temp_md = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        temp_md.write(preprocess_markdown(md_content))
        temp_md.close()
        
        # Use mdpdf with custom CSS
        css_file = tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False, encoding='utf-8')
        css_file.write(get_enhanced_css().replace('<style>', '').replace('</style>', ''))
        css_file.close()
        
        cmd = [
            'mdpdf', 
            '--output', output_file,
            '--css', css_file.name,
            '--format', 'A4',
            '--margin', '2cm',
            temp_md.name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up temp files
        os.unlink(temp_md.name)
        os.unlink(css_file.name)
        
        print(f"✅ PDF created successfully with mdpdf: {output_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ mdpdf failed: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ mdpdf error: {str(e)}")
        return False

def convert_with_weasyprint(markdown_file_name: str, output_file: str) -> bool:
    """Try converting with weasyprint - enhanced version."""
    try:
        print("🔄 Trying weasyprint...")
        
        # Setup fontconfig to avoid font errors
        setup_fontconfig()
        
        # Suppress fontconfig warnings
        import warnings
        warnings.filterwarnings('ignore')
        
        # Read and preprocess markdown
        with open(markdown_file_name, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Preprocess the markdown
        processed_md = preprocess_markdown(md_content)
        
        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            processed_md, 
            extensions=['extra', 'codehilite', 'toc']
        )
        
        # Create complete HTML document with enhanced styling
        styled_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Children's Storybook</title>
            {get_enhanced_css()}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Import weasyprint components
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Create a custom font configuration
        font_config = FontConfiguration()
        
        # Convert to PDF with enhanced settings
        HTML(string=styled_html, base_url=os.path.dirname(os.path.abspath(markdown_file_name))).write_pdf(
            output_file,
            font_config=font_config,
            optimize_images=True,
            presentational_hints=True
        )
        
        print(f"✅ PDF created successfully with weasyprint: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ weasyprint failed: {str(e)}")
        if "fontconfig" in str(e).lower():
            print("⚠️  Fontconfig error detected. Checking if PDF was created...")
            # Check if PDF was actually created despite the error
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:  # At least 1KB
                print("✅ PDF was created successfully despite fontconfig warning")
                return True
        return False

def convert_with_pdfkit(markdown_file_name: str, output_file: str) -> bool:
    """Try converting with pdfkit - enhanced version."""
    try:
        print("🔄 Trying pdfkit...")
        
        # Check if pdfkit is available
        try:
            import pdfkit
        except ImportError:
            print("❌ pdfkit not installed")
            return False
        
        # Read and preprocess markdown
        with open(markdown_file_name, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Preprocess the markdown
        processed_md = preprocess_markdown(md_content)
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            processed_md,
            extensions=['extra', 'codehilite', 'toc']
        )
        
        # Create complete HTML document
        styled_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Children's Storybook</title>
            {get_enhanced_css()}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Enhanced options for better PDF generation
        options = {
            'page-size': 'A4',
            'margin-top': '2cm',
            'margin-right': '2cm',
            'margin-bottom': '2cm',
            'margin-left': '2cm',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': '',
            'print-media-type': None,
            'disable-smart-shrinking': None,
            'enable-local-file-access': None,
            'minimum-font-size': 10,
            'javascript-delay': 1000,
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore'
        }
        
        # Convert to PDF
        pdfkit.from_string(styled_html, output_file, options=options)
        print(f"✅ PDF created successfully with pdfkit: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ pdfkit failed: {str(e)}")
        return False

def create_fallback_html(markdown_file_name: str) -> str:
    """Create a high-quality HTML version as fallback."""
    try:
        print("🔄 Creating enhanced HTML fallback...")
        html_output = os.path.splitext(markdown_file_name)[0] + '.html'
        
        with open(markdown_file_name, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Preprocess the markdown
        processed_md = preprocess_markdown(md_content)
        
        # Convert to HTML with extensions
        html_content = markdown.markdown(
            processed_md,
            extensions=['extra', 'codehilite', 'toc', 'tables']
        )
        
        # Create complete HTML document
        styled_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Children's Storybook</title>
            {get_enhanced_css()}
            <style>
                /* Additional screen-specific styles */
                @media screen {{
                    body {{
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #fafafa;
                    }}
                    
                    .print-button {{
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #3498db;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 14px;
                        z-index: 1000;
                    }}
                    
                    .print-button:hover {{
                        background: #2980b9;
                    }}
                }}
            </style>
            <script>
                function printPage() {{
                    window.print();
                }}
            </script>
        </head>
        <body>
            <button class="print-button" onclick="printPage()">🖨️ Print to PDF</button>
            {html_content}
        </body>
        </html>
        """
        
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(styled_html)
        
        return html_output
        
    except Exception as e:
        print(f"❌ HTML fallback creation failed: {str(e)}")
        return None

@tool
def convert_markdown_to_pdf(markdown_file_name: str) -> str:
    """
    Converts a Markdown file to a professionally formatted PDF document.
    Uses multiple conversion methods with enhanced formatting and error handling.

    Args:
        markdown_file_name (str): Path to the input Markdown file.

    Returns:
        str: Path to the generated PDF file or detailed status message.
    """
    if not os.path.exists(markdown_file_name):
        error_msg = f"❌ Markdown file not found: {markdown_file_name}"
        print(error_msg)
        return error_msg
    
    output_file = os.path.splitext(markdown_file_name)[0] + '.pdf'
    available_tools = check_pdf_tools()
    
    print(f"📄 Converting {markdown_file_name} to professionally formatted PDF...")
    print(f"Available tools: {available_tools}")
    
    # Try each method in order of preference
    conversion_methods = [
        ('weasyprint', convert_with_weasyprint),  # Best for complex layouts
        ('mdpdf', convert_with_mdpdf),           # Good for markdown
        ('pdfkit', convert_with_pdfkit)          # Fallback option
    ]
    
    for tool_name, convert_func in conversion_methods:
        if available_tools.get(tool_name) or tool_name == 'weasyprint':
            try:
                if convert_func(markdown_file_name, output_file):
                    # Verify the PDF was created and has content
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                        print(f"✅ Professional PDF created: {output_file}")
                        print(f"📊 File size: {os.path.getsize(output_file)} bytes")
                        return output_file
                    else:
                        print(f"⚠️  PDF file seems too small or empty")
                        continue
            except Exception as e:
                print(f"❌ {tool_name} conversion failed with exception: {str(e)}")
                continue
    
    # If all PDF methods failed, create enhanced HTML version
    html_file = create_fallback_html(markdown_file_name)
    
    if html_file:
        fallback_msg = f"""
✅ Enhanced HTML version created: {html_file}

📖 Your storybook is ready! Since PDF conversion had issues, I've created a
professionally formatted HTML version that you can:

1. 🖨️ Open in your browser and use "Print to PDF" (Ctrl+P)
2. 🌐 Use online converters like:
   - https://www.markdowntopdf.com/
   - https://dillinger.io/ (export to PDF)
3. 📱 Share the HTML file directly - it's mobile-friendly!

🛠️ To enable direct PDF generation, install:
   pip install weasyprint
   # OR
   pip install mdpdf

The HTML version has the same professional formatting and will convert
beautifully to PDF using your browser's print function.
"""
        print(fallback_msg)
        return fallback_msg
    else:
        error_msg = f"""
❌ All conversion methods failed.

The markdown file '{markdown_file_name}' contains your complete storybook.
You can still use it by:

1. 📝 Opening it in any text editor
2. 🌐 Using online markdown viewers
3. 🔄 Installing PDF conversion tools:
   
   pip install weasyprint
   pip install mdpdf
   pip install pdfkit (requires wkhtmltopdf)

Your story content is safe in the markdown file!
"""
        print(error_msg)
        return error_msg