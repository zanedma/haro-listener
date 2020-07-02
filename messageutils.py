import base64
import email

def getMimeMessage(body):
    """Return decoded message in MIME format of the contents in body

    @param body String: raw RFC 2822 formatted and base64 encoded string
    @return String: decoded message in MIME format
    """
    msg_str = base64.urlsafe_b64decode(body.encode('ASCII'))
    mime_message = email.message_from_bytes(msg_str)
    return mime_message.get_payload(0)


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
    links_end = '****************************'
    link_num = 1
    while True:
        start_idx = body.find('{}) '.format(link_num))
        if start_idx == -1:
            break
        body = body[start_idx:] # less to search through next iteration

        end_idx = body.find('>')
        if end_idx == -1:
            end_idx = body.find(links_end)
            if end_idx == -1:
                break

        full_link = body[:end_idx+1] + '\n'
        link_title = full_link[:full_link.fin('<')]
        for key in link_keys:
            if key in link_title.lower():
                found_links.append(full_link)
                break

        link_num += 1

    return found_links
