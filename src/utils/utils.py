from urllib.parse import urlparse, urlunparse

def truncate_to_base_url(url):
    if not url.startswith(('http://', 'https://')):
        parsed = urlparse(f'http://{url}')
        clean_path = parsed.netloc + parsed.path
    else:
        parsed = urlparse(url)
        clean_path = parsed.netloc + parsed.path
    
    return clean_path
