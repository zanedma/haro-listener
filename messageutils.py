import base64
import email
from bs4 import BeautifulSoup

def getMimeMessage(body):
    """Return decoded message in MIME format of the contents in body

    @param body String: raw RFC 2822 formatted and base64 encoded string
    @return String: decoded message in MIME format
    """
    msg_str = base64.urlsafe_b64decode(body.encode('ASCII'))
    mime_message = email.message_from_bytes(msg_str)
    return mime_message.get_payload(0)


def get_full_post(body, link_num):
    post_end = '<p>-----------------------------------<br/></p>'
    start_idx = body.find('{})<a name='.format(link_num))
    end_idx = body[start_idx:].find(post_end)
    full_post = body[start_idx:start_idx+end_idx]
    soup = BeautifulSoup(full_post, features='html.parser')
    text = soup.get_text()
    text = text.replace(':=20', '')
    text = text.replace('helparepo=\nrter.net', 'helpareporter.net')
    text = text.replace('=\n', '')
    text = text.replace('Back to Top Back to Category Index', '')
    return text
    


def findLinks(body, link_keys):
    """Find the links in a HARO email body that contain key words/phrases
    and return them as an iterable of the found MIME formatted links

    @param body String: HARO email message in MIME format
    @param link_keys Iterable[String]: List of key words and/or phrases to
    look for in link titles
    @return Iterable[String]: MIME formatted links that have key words or
    phrases in their title
    """
    found_links = []
    # Haro links are ended by the string below
    links_start = '<h4>********* INDEX ***********</h4>'
    links_end = '<h4>****************************</h4>'
    all_links = body[body.find(links_start):body.find(links_end)]
    link_num = 1
    while True:
        start_idx = all_links.find('{}) <a href='.format(link_num))
        if start_idx == -1:
            break

        end_idx = all_links[start_idx:].find('</a>')
        if end_idx == -1:
            end_idx = all_links.find(links_end)
            if end_idx == -1:
                break

        full_link = all_links[start_idx:start_idx+end_idx+4]
        title_start = full_link.find('\">')+2
        link_title = full_link[title_start:end_idx]
        all_links = all_links[start_idx:] # less to search through next iteration
        for key in link_keys:
            if key in link_title.lower():
                found_links.append(get_full_post(body, link_num))
                break

        link_num += 1

    return found_links
