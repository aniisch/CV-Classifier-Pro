import re

def clean_markdown(text):
    # Supprimer les emojis
    text = re.sub(r':[a-zA-Z_]+:', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # Supprimer les # tout en gardant les titres
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Nettoyer les titres Markdown
        if line.strip().startswith('#'):
            line = line.strip('#').strip()
        
        # Supprimer les lignes de tableau vides ou avec juste des tirets
        if not line.strip() or line.strip().startswith('|---'):
            continue
            
        # Nettoyer les lignes de tableau
        if '|' in line:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            line = '  '.join(cells)
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
