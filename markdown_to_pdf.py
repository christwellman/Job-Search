import markdown
from weasyprint import HTML

# Read the Markdown resume file
with open('Resume.md', 'r') as file:
    md_content = file.read()

# Convert Markdown to HTML
html_content = markdown.markdown(md_content)

# Add CSS link to the HTML content
css_link = '<link rel="stylesheet" type="text/css" href="Resume.css">'
html_content_with_css = f'<html><head>{css_link}</head><body>{html_content}</body></html>'

# Create a new HTML file with the converted content
with open('resume.html', 'w') as file:
    file.write(html_content_with_css)

# Generate PDF from the HTML file
HTML('resume.html').write_pdf('resume.pdf')

print("Resume converted from Markdown to PDF successfully!")
