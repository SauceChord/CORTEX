import markdown

def render_markdown(md_text):
    # Convert Markdown to HTML
    html = markdown.markdown(md_text)

    # Simple stripping of HTML tags to print plain text
    plain_text = ''.join(html.split('<')[0:1] + [i.split('>')[1] for i in html.split('<')[1:] if '>' in i])
    plain_text = plain_text.replace("```python", "")
    plain_text = plain_text.replace("```", "")
    # Print the plain text to the console
    return plain_text