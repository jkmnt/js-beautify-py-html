from jsbeautifier.html.beautifier import Beautifier

text = """<div><div></div><div><div></div></div></div>

"""

text = """

        <div>
        <!-- soup -->
                <span>Foo</span><span>Bar</span>
                <div>
                    <div attr="1" attr="1"

                        attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" >
                    Bla
                            </div>


</div><div>a</div><div>a</div><div>a</div><div>a</div><div>

a            <span>


INLINE   </span>      </div     >
            </div>
"""

b = Beautifier(
    text,
    {
        "indent_size": "4",
        "indent_char": " ",
        "max_preserve_newlines": "1",
        "preserve_newlines": True,
        "keep_array_indentation": False,
        "break_chained_methods": False,
        "indent_scripts": "keep",
        "brace_style": "end-expand",
        "space_before_conditional": True,
        "unescape_strings": False,
        "jslint_happy": False,
        "end_with_newline": False,
        "wrap_line_length": "80",
        "indent_inner_html": False,
        "comma_first": False,
        "e4x": False,
        "indent_empty_lines": True,
    },
)
res = b.beautify()

print(res)
