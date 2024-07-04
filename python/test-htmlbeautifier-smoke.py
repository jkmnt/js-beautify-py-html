from jsbeautifier.html.beautifier import Beautifier


b = Beautifier("""
    <!-- soup -->
        <div>
<span>Foo</span><span>Bar</span>
<div>
    <div attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" attr="1" >
    Bla
            </div>
</div>
            </div>
""")
res = b.beautify()

print(res)