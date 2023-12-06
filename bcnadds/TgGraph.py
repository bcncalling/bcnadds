import json
import httpx
from .errors import TelegraphException, RetryAfterError, NotAllowedTag, InvalidHTML
import mimetypes
import re
from html.parser import HTMLParser
from html.entities import name2codepoint
from html import escape

RE_WHITESPACE = re.compile(r'(\s+)', re.UNICODE)

ALLOWED_TAGS = {
    'a', 'aside', 'b', 'blockquote', 'br', 'code', 'em', 'figcaption', 'figure',
    'h3', 'h4', 'hr', 'i', 'iframe', 'img', 'li', 'ol', 'p', 'pre', 's',
    'strong', 'u', 'ul', 'video', 'div', 'span'  # Add more allowed tags here
}

VOID_ELEMENTS = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'keygen',
    'link', 'menuitem', 'meta', 'param', 'source', 'track', 'wbr'
}

BLOCK_ELEMENTS = {
    'address', 'article', 'aside', 'blockquote', 'canvas', 'dd', 'div', 'dl',
    'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2',
    'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'li', 'main', 'nav',
    'noscript', 'ol', 'output', 'p', 'pre', 'section', 'table', 'tfoot', 'ul',
    'video'
}


class HtmlToNodesParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

        self.nodes = []

        self.current_nodes = self.nodes
        self.parent_nodes = []

        self.last_text_node = None

        self.tags_path = []

    def add_str_node(self, s):
        if not s:
            return

        if 'pre' not in self.tags_path:  # keep whitespace in <pre>
            s = RE_WHITESPACE.sub(' ', s)

            if self.last_text_node is None or self.last_text_node.endswith(' '):
                s = s.lstrip(' ')

            if not s:
                self.last_text_node = None
                return

            self.last_text_node = s

        if self.current_nodes and isinstance(self.current_nodes[-1], str):
            self.current_nodes[-1] += s
        else:
            self.current_nodes.append(s)

    def handle_starttag(self, tag, attrs_list):
        if tag not in ALLOWED_TAGS:
            raise NotAllowedTag(f'{tag!r} tag is not allowed')

        if tag in BLOCK_ELEMENTS:
            self.last_text_node = None

        node = {'tag': tag}
        self.tags_path.append(tag)
        self.current_nodes.append(node)

        if attrs_list:
            attrs = {}
            node['attrs'] = attrs

            for attr, value in attrs_list:
                attrs[attr] = value

        if tag not in VOID_ELEMENTS:
            self.parent_nodes.append(self.current_nodes)
            self.current_nodes = node['children'] = []

    def handle_endtag(self, tag):
        if tag in VOID_ELEMENTS:
            return

        if not len(self.parent_nodes):
            raise InvalidHTML(f'{tag!r} missing start tag')

        self.current_nodes = self.parent_nodes.pop()

        last_node = self.current_nodes[-1]

        if last_node['tag'] != tag:
            raise InvalidHTML(f'{tag!r} tag closed instead of {last_node["tag"]!r}')

        self.tags_path.pop()

        if not last_node['children']:
            last_node.pop('children')

    def handle_data(self, data):
        self.add_str_node(data)

    def handle_entityref(self, name):
        self.add_str_node(chr(name2codepoint[name]))

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))

        self.add_str_node(c)

    def get_nodes(self):
        if self.parent_nodes:
            not_closed_tag = self.parent_nodes[-1][-1]['tag']
            raise InvalidHTML(f'{not_closed_tag!r} tag is not closed')

        return self.nodes


def html_to_nodes(html_content):
    parser = HtmlToNodesParser()
    parser.feed(html_content)
    return parser.get_nodes()


def nodes_to_html(nodes):
    out = []
    append = out.append

    stack = []
    curr = nodes
    i = -1

    while True:
        i += 1

        if i >= len(curr):
            if not stack:
                break
            curr, i = stack.pop()
            append(f'</{curr[i]["tag"]}>')
            continue

        node = curr[i]

        if isinstance(node, str):
            append(escape(node))
            continue

        append(f'<{node["tag"]}')

        if node.get('attrs'):
            for attr, value in node['attrs'].items():
                append(f' {attr}="{escape(value)}"')

        if node.get('children'):
            append('>')
            stack.append((curr, i))
            curr, i = node['children'], -1
            continue

        if node["tag"] in VOID_ELEMENTS:
            append('/>')
        else:
            append(f'></{node["tag"]}>')

    return ''.join(out)


class FilesOpener(object):
    def __init__(self, paths, key_format='file{}'):
        if not isinstance(paths, list):
            paths = [paths]

        self.paths = paths
        self.key_format = key_format
        self.opened_files = []

    def __enter__(self):
        return self.open_files()

    def __exit__(self, type, value, traceback):
        self.close_files()

    def open_files(self):
        self.close_files()

        files = []

        for x, file_or_name in enumerate(self.paths):
            name = ''
            if isinstance(file_or_name, tuple) and len(file_or_name) >= 2:
                name = file_or_name[1]
                file_or_name = file_or_name[0]

            if hasattr(file_or_name, 'read'):
                f = file_or_name

                if hasattr(f, 'name'):
                    filename = f.name
                else:
                    filename = name
            else:
                filename = file_or_name
                f = open(filename, 'rb')
                self.opened_files.append(f)

            mimetype = mimetypes.MimeTypes().guess_type(filename)[0]

            files.append(
                (self.key_format.format(x), ('file{}'.format(x), f, mimetype))
            )

        return files

    def close_files(self):
        for f in self.opened_files:
            f.close()

        self.opened_files = []


def json_dumps(*args, **kwargs):
    return json.dumps(*args, **kwargs, separators=(',', ':'), ensure_ascii=False)


class TgGraphApi:
    """ Telegraph API Client

    :param access_token: access_token
    :type access_token: str

    :param domain: domain (e.g. alternative mirror graph.org)
    """

    __slots__ = ('access_token', 'domain', 'session')

    def __init__(self, access_token=None, domain='telegra.ph'):
        self.access_token = access_token
        self.domain = domain
        self.session = httpx.AsyncClient()

    async def method(self, method, values=None, path=''):
        values = values.copy() if values is not None else {}

        if 'access_token' not in values and self.access_token:
            values['access_token'] = self.access_token

        response = (await self.session.post(
            'https://api.{}/{}/{}'.format(self.domain, method, path),
            data=values
        )).json()

        if response.get('ok'):
            return response['result']

        error = response.get('error')
        if isinstance(error, str) and error.startswith('FLOOD_WAIT_'):
            retry_after = int(error.rsplit('_', 1)[-1])
            raise RetryAfterError(retry_after)
        else:
            raise TelegraphException(error)

    async def file_upload(self, f):
        """ Upload file. NOT PART OF OFFICIAL API, USE AT YOUR OWN RISK
            Returns a list of dicts with `src` key.
            Allowed only .jpg, .jpeg, .png, .gif and .mp4 files.

        :param f: filename or file-like object.
        :type f: file, str or list
        """
        with FilesOpener(f) as files:
            response = (await self.session.post(
                'https://{}/upload'.format(self.domain),
                files=files
            )).json()

        if isinstance(response, list):
            error = response[0].get('error')
        else:
            error = response.get('error')

        if error:
            if isinstance(error, str) and error.startswith('FLOOD_WAIT_'):
                retry_after = int(error.rsplit('_', 1)[-1])
                raise RetryAfterError(retry_after)
            else:
                raise TelegraphException(error)

        return response


class TgGraph:
    """ Telegraph API client helper

    :param access_token: access token
    :param domain: domain (e.g. alternative mirror graph.org)
    """

    __slots__ = ('_tgraph',)

    def __init__(self, access_token=None, domain='telegra.ph'):
        self._tgraph = TgGraphApi(access_token, domain)

    def get_access_token(self):
        """Get current access_token"""
        return self._tgraph.access_token

    async def create_account(self, short_name, author_name=None, author_url=None,
                             replace_token=True):
        """ Create a new Telegraph account

        :param short_name: Account name, helps users with several
                           accounts remember which they are currently using.
                           Displayed to the user above the "Edit/Publish"
                           button on Telegra.ph, other users don't see this name
        :param author_name: Default author name used when creating new articles
        :param author_url: Default profile link, opened when users click on the
                           author's name below the title. Can be any link,
                           not necessarily to a Telegram profile or channels
        :param replace_token: Replaces current token to a new user's token
        """
        response = (await self._tgraph.method('createAccount', values={
            'short_name': short_name,
            'author_name': author_name,
            'author_url': author_url
        }))

        if replace_token:
            self._tgraph.access_token = response.get('access_token')

        return response

    async def edit_account_info(self, short_name=None, author_name=None,
                                author_url=None):
        """ Update information about a Telegraph account.
            Pass only the parameters that you want to edit

        :param short_name: Account name, helps users with several
                           accounts remember which they are currently using.
                           Displayed to the user above the "Edit/Publish"
                           button on Telegra.ph, other users don't see this name
        :param author_name: Default author name used when creating new articles
        :param author_url: Default profile link, opened when users click on the
                           author's name below the title. Can be any link,
                           not necessarily to a Telegram profile or channels
        """
        return (await self._tgraph.method('editAccountInfo', values={
            'short_name': short_name,
            'author_name': author_name,
            'author_url': author_url
        }))

    async def revoke_access_token(self):
        """ Revoke access_token and generate a new one, for example,
            if the user would like to reset all connected sessions, or
            you have reasons to believe the token was compromised.
            On success, returns dict with new access_token and auth_url fields
        """
        response = (await self._tgraph.method('revokeAccessToken'))

        self._tgraph.access_token = response.get('access_token')

        return response

    async def get_page(self, path, return_content=True, return_html=True):
        """ Get a Telegraph page

        :param path: Path to the Telegraph page (in the format Title-12-31,
                     i.e. everything that comes after https://telegra.ph/)
        :param return_content: If true, content field will be returned
        :param return_html: If true, returns HTML instead of Nodes list
        """
        response = (await self._tgraph.method('getPage', path=path, values={
            'return_content': return_content
        }))

        if return_content and return_html:
            response['content'] = nodes_to_html(response['content'])

        return response

    async def create_page(self, title, content=None, html_content=None,
                          author_name=None, author_url=None, return_content=False,
                          return_html=False):
        """ Create a new Telegraph page

        :param title: Page title
        :param content: Content in nodes list format (see doc)
        :param html_content: Content in HTML format
        :param author_name: Author name, displayed below the article's title
        :param author_url: Profile link, opened when users click on
                           the author's name below the title
        :param return_content: If true, a content field will be returned
        :param return_html: If true, returns HTML instead of Nodes list
        """
        if content is None:
            content = html_to_nodes(html_content)

        content_json = json_dumps(content)

        response = (await self._tgraph.method('createPage', values={
            'title': title,
            'author_name': author_name,
            'author_url': author_url,
            'content': content_json,
            'return_content': return_content
        }))

        if return_content and return_html:
            response['content'] = nodes_to_html(response['content'])

        return response

    async def edit_page(self, path, title, content=None, html_content=None,
                        author_name=None, author_url=None, return_content=False,
                        return_html=False):
        """ Edit an existing Telegraph page

        :param path: Path to the page
        :param title: Page title
        :param content: Content in nodes list format (see doc)
        :param html_content: Content in HTML format
        :param author_name: Author name, displayed below the article's title
        :param author_url: Profile link, opened when users click on
                           the author's name below the title
        :param return_content: If true, a content field will be returned
        :param return_html: If true, returns HTML instead of Nodes list
        """
        if content is None:
            content = html_to_nodes(html_content)

        content_json = json_dumps(content)

        response = (await self._tgraph.method('editPage', path=path, values={
            'title': title,
            'author_name': author_name,
            'author_url': author_url,
            'content': content_json,
            'return_content': return_content
        }))

        if return_content and return_html:
            response['content'] = nodes_to_html(response['content'])

        return response

    async def get_account_info(self, fields=None):
        """ Get information about a Telegraph account

        :param fields: List of account fields to return. Available fields:
                       short_name, author_name, author_url, auth_url, page_count

                       Default: [“short_name”,“author_name”,“author_url”]
        """
        return (await self._tgraph.method('getAccountInfo', {
            'fields': json_dumps(fields) if fields else None
        }))

    async def get_page_list(self, offset=0, limit=50):
        """ Get a list of pages belonging to a Telegraph account
            sorted by most recently created pages first

        :param offset: Sequential number of the first page to be returned
                       (default = 0)
        :param limit: Limits the number of pages to be retrieved
                      (0-200, default = 50)
        """
        return (await self._tgraph.method('getPageList', {
            'offset': offset,
            'limit': limit
        }))

    async def get_views(self, path, year=None, month=None, day=None, hour=None):
        """ Get the number of views for a Telegraph article

        :param path: Path to the Telegraph page
        :param year: Required if month is passed. If passed, the number of
                     page views for the requested year will be returned
        :param month: Required if day is passed. If passed, the number of
                      page views for the requested month will be returned
        :param day: Required if hour is passed. If passed, the number of
                    page views for the requested day will be returned
        :param hour: If passed, the number of page views for
                     the requested hour will be returned
        """
        return (await self._tgraph.method('getViews', path=path, values={
            'year': year,
            'month': month,
            'day': day,
            'hour': hour
        }))

    async def file_upload(self, f):
        """ Upload file. NOT PART OF OFFICIAL API, USE AT YOUR OWN RISK
            Returns a list of dicts with `src` key.
            Allowed only .jpg, .jpeg, .png, .gif, and .mp4 files.

        :param f: filename or file-like object.
        :type f: file, str, or list
        """
        return (await self._tgraph.file_upload(f))
