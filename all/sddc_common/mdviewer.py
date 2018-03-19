
import mdpopups
import sublime
from sublime_plugin import TextCommand
from functools import partial

frontmatter = {
    "markdown_extensions": [
        "markdown.extensions.admonition",
        "markdown.extensions.attr_list",
        "markdown.extensions.def_list",
        "markdown.extensions.nl2br",
        # {"markdown.extensions.wikilinks": {"base_url":"#wiki/","end_url":".md"}},
        # Smart quotes always have corner cases that annoy me, so don't bother with them.
        {"markdown.extensions.smarty": {"smart_quotes": False}},
        "pymdownx.betterem",
        {
            "pymdownx.magiclink": {
                "repo_url_shortener": True,
                "base_repo_url": "https://github.com/facelessuser/sublime-markdown-popups"
            }
        },
        "pymdownx.extrarawhtml",
        "pymdownx.keys",
        "pymdownx.b64",
        {"pymdownx.escapeall": {"hardbreak": True, "nbsp": True}},
        # Sublime doesn't support superscript, so no ordinal numbers
        {"pymdownx.smartsymbols": {"ordinal_numbers": False}}
    ]
}

class MarkdownViewerCommand(TextCommand):

    def run(self, edit, content=None, phantom_name=None, new_view=None, frontmatter=frontmatter):
        if content is None:
            content = self.view.substr(sublime.Region(0, self.view.size()))
            if phantom_name and new_view is None:
                new_view = True
        if new_view:
            view = self.view.window().new_file()
            view.set_scratch(True)
            view.set_read_only(True)
            view.run_command('markdown_viewer',args={
                'content':content,'phantom_name':phantom_name,'new_view':False,'frontmatter':frontmatter})
        else:
            self.show_text(content,phantom_name,mdpopups.format_frontmatter(frontmatter))

    def handler(self, href, phantom_name, frontmatter):
        print(href)

    def on_close(self, href, phantom_name, frontmatter):
        if href=='#':
            if phantom_name:
                mdpopups.erase_phantoms(self.view, phantom_name)
                if self.view.is_scratch() and self.view.is_read_only():
                    self.view.close()
            else:
                mdpopups.hide_popup(self.view)
        else:
            self.handler(href, phantom_name, frontmatter)

    def show_text(self, text, phantom_name, frontmatter):
        """Show the popup."""
        mdpopups.clear_cache()
        region = self.view.visible_region()
        close = '\n[close](#){: .btn .btn-small .btn-info}\n'
        nav = partial(self.on_close,phantom_name=phantom_name, frontmatter=frontmatter)
        if phantom_name:
            mdpopups.add_phantom(
                self.view, phantom_name, region, frontmatter+text+close, 2,
                on_navigate=nav, wrapper_class='mdviewer'
            )
        else:
            mdpopups.show_popup(
                self.view, frontmatter+text+close, location=region.a, on_navigate=nav,
                max_height=900, max_width=900, wrapper_class='mdviewer',
                css='div.mdviewer { padding: 0.5rem; }'
            )
