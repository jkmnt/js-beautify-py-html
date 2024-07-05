from jsbeautifier.html.beautifier import Beautifier


b = Beautifier("""

        <div>
        <!-- soup -->
<span>Foo</span><span>Bar</span>
<div>
    <div attr="1" attr="1"

        attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" >
    Bla
            </div>




</div><div>a</div><div>a</div><div>a</div><div>a</   div><      div>

a            <span>


INLINE   </span>      </      div     >
            </div>
""", {"wrap_attributes": "force-aligned", "max_preserve_newlines": 1, "wrap_line_length": 80})
res = b.beautify()

print(res)