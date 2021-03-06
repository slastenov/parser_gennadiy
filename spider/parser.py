import requests
import os
from urllib import parse
from bs4 import BeautifulSoup

css_files = set()
js_files = set()
image_files = set()


def parse_website(url: str, nesting: int = 1) -> set:
    links = {url, }
    get_all_pages(url, 0, links, nesting)
    save_content(css_files)
    save_content(js_files)
    save_content(image_files)
    return links


def get_all_pages(url: str, level: int, links: set, nesting: int) -> None:
    domain = parse.urlparse(url).netloc
    content, content_type = get_content(url)
    save_file(url, content, 'html')
    print(url)
    if level >= nesting:
        return
    if 'text/html' in content_type:
        bs = BeautifulSoup(content, "html.parser")
        get_scripts(bs, url)
        get_css(bs, url)
        get_images(bs, url)
        for link_tag in bs.findAll("a"):
            href = link_tag.attrs.get("href")
            if href == "" or href is None:
                continue
            href = make_clean_href(url, href)
            if domain not in href:
                continue
            if href in links:
                continue
            links.add(href)

            get_all_pages(href, level+1, links, nesting)


def make_clean_href(url: str, href: str) -> str:
    href = parse.urlparse(parse.urljoin(url, href))
    return href.scheme + "://" + href.netloc + href.path


def save_file(url, content, content_type=None):
    if content_type == 'html' and url[-4:] != 'html':
        path = href_path_to_directory(url) + '.html'
    else:
        path = href_path_to_directory(url)
    if os.path.dirname(path) and not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, mode='wb') as file:
        file.write(content)


def save_content(files: set or list):
    for file in files:
        content = get_content(file)[0]
        save_file(file, content)


def get_content(url: str):
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                                    "Chrome/83.0.4103.116 Safari/537.36 OPR/69.0.3686.95"
    request = requests.get(url)
    return request.content, request.headers['Content-Type']


def href_path_to_directory(url: str):
    href_path = parse.urlparse(url).path.rstrip('/')
    split_path = href_path.split('/')
    if not href_path:
        split_path = ['index.html', ]
    dir_path = os.path.join(parse.urlparse(url).netloc, *split_path)

    return dir_path


def get_scripts(bs: BeautifulSoup, url: str):
    for script in bs.find_all("script"):
        if script.attrs.get("src"):
            if not parse.urlparse(script.attrs["src"]).netloc:
                script_url = make_clean_href(url, script.attrs.get("src"))
                js_files.add(script_url)


def get_css(bs: BeautifulSoup, url: str):
    for css in bs.find_all("link"):
        if css.attrs.get("href"):
            if not parse.urlparse(css.attrs["href"]).netloc:
                css_url = make_clean_href(url, css.attrs.get("href"))
                css_files.add(css_url)


def get_images(bs: BeautifulSoup, url: str):
    for image in bs.find_all("img"):
        image_url = image.attrs.get("src")
        if not image_url:
            continue
        image_url = parse.urljoin(url, image_url)
        try:
            pos = image_url.index("?")
            image_url = image_url[:pos]
        except ValueError:
            pass
        image_files.add(image_url)
