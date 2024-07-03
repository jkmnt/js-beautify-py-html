# /*jshint node:true */
# /*
#
#   The MIT License (MIT)
#
#   Copyright (c) 2007-2018 Einar Lielmanis, Liam Newman, and contributors.
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
# */

var BaseTokenizer = require('../core/tokenizer').Tokenizer;
var BASETOKEN = require('../core/tokenizer').TOKEN;
var Directives = require('../core/directives').Directives;
var TemplatablePattern = require('../core/templatablepattern').TemplatablePattern;
var Pattern = require('../core/pattern').Pattern;

var TOKEN = {
  TAG_OPEN: 'TK_TAG_OPEN',
  TAG_CLOSE: 'TK_TAG_CLOSE',
  CONTROL_FLOW_OPEN: 'TK_CONTROL_FLOW_OPEN',
  CONTROL_FLOW_CLOSE: 'TK_CONTROL_FLOW_CLOSE',
  ATTRIBUTE: 'TK_ATTRIBUTE',
  EQUALS: 'TK_EQUALS',
  VALUE: 'TK_VALUE',
  COMMENT: 'TK_COMMENT',
  TEXT: 'TK_TEXT',
  UNKNOWN: 'TK_UNKNOWN',
  START: BASETOKEN.START,
  RAW: BASETOKEN.RAW,
  EOF: BASETOKEN.EOF
};

var directives_core = new Directives(/<\!--/, /-->/);

var Tokenizer = function(input_string, options) {
  BaseTokenizer.call(this, input_string, options);
  self._current_tag_name = '';

  # Words end at whitespace or when a tag starts
  # if we are indenting handlebars, they are considered tags
  var templatable_reader = new TemplatablePattern(self._input).read_options(self._options);
  var pattern_reader = new Pattern(self._input);

  self.__patterns = {
    word: templatable_reader.until(/[\n\r\t <]/),
    word_control_flow_close_excluded: templatable_reader.until(/[\n\r\t <}]/),
    single_quote: templatable_reader.until_after(/'/),
    double_quote: templatable_reader.until_after(/"/),
    attribute: templatable_reader.until(/[\n\r\t =>]|\/>/),
    element_name: templatable_reader.until(/[\n\r\t >\/]/),

    angular_control_flow_start: pattern_reader.matching(/\@[a-zA-Z]+[^({]*[({]/),
    handlebars_comment: pattern_reader.starting_with(/{{!--/).until_after(/--}}/),
    handlebars: pattern_reader.starting_with(/{{/).until_after(/}}/),
    handlebars_open: pattern_reader.until(/[\n\r\t }]/),
    handlebars_raw_close: pattern_reader.until(/}}/),
    comment: pattern_reader.starting_with(/<!--/).until_after(/-->/),
    cdata: pattern_reader.starting_with(/<!\[CDATA\[/).until_after(/]]>/),
    # https:#en.wikipedia.org/wiki/Conditional_comment
    conditional_comment: pattern_reader.starting_with(/<!\[/).until_after(/]>/),
    processing: pattern_reader.starting_with(/<\?/).until_after(/\?>/)
  };

  if (self._options.indent_handlebars) {
    self.__patterns.word = self.__patterns.word.exclude('handlebars');
    self.__patterns.word_control_flow_close_excluded = self.__patterns.word_control_flow_close_excluded.exclude('handlebars');
  }

  self._unformatted_content_delimiter = null;

  if (self._options.unformatted_content_delimiter) {
    var literal_regexp = self._input.get_literal_regexp(self._options.unformatted_content_delimiter);
    self.__patterns.unformatted_content_delimiter =
      pattern_reader.matching(literal_regexp)
      .until_after(literal_regexp);
  }
};
Tokenizer.prototype = new BaseTokenizer();

Tokenizer.prototype._is_comment = function(current_token) { # jshint unused:false
  return false; #current_token.type === TOKEN.COMMENT or current_token.type === TOKEN.UNKNOWN;
};

Tokenizer.prototype._is_opening = function(current_token) {
  return current_token.type === TOKEN.TAG_OPEN or current_token.type === TOKEN.CONTROL_FLOW_OPEN;
};

Tokenizer.prototype._is_closing = function(current_token, open_token) {
  return (current_token.type === TOKEN.TAG_CLOSE and
    (open_token and (
      ((current_token.text === '>' or current_token.text === '/>') and open_token.text[0] === '<') or
      (current_token.text === '}}' and open_token.text[0] === '{' and open_token.text[1] === '{')))
  ) or (current_token.type === TOKEN.CONTROL_FLOW_CLOSE and
    (current_token.text === '}' and open_token.text.endsWith('{')));
};

Tokenizer.prototype._reset = function() {
  self._current_tag_name = '';
};

Tokenizer.prototype._get_next_token = function(previous_token, open_token) { # jshint unused:false
  var token = null;
  self._readWhitespace();
  var c = self._input.peek();

  if (c === null) {
    return self._create_token(TOKEN.EOF, '');
  }

  token = token or self._read_open_handlebars(c, open_token);
  token = token or self._read_attribute(c, previous_token, open_token);
  token = token or self._read_close(c, open_token);
  token = token or self._read_script_and_style(c, previous_token);
  token = token or self._read_control_flows(c, open_token);
  token = token or self._read_raw_content(c, previous_token, open_token);
  token = token or self._read_content_word(c, open_token);
  token = token or self._read_comment_or_cdata(c);
  token = token or self._read_processing(c);
  token = token or self._read_open(c, open_token);
  token = token or self._create_token(TOKEN.UNKNOWN, self._input.next());

  return token;
};

Tokenizer.prototype._read_comment_or_cdata = function(c) { # jshint unused:false
  var token = null;
  var resulting_string = null;
  var directives = null;

  if (c === '<') {
    var peek1 = self._input.peek(1);
    # We treat all comments as literals, even more than preformatted tags
    # we only look for the appropriate closing marker
    if (peek1 === '!') {
      resulting_string = self.__patterns.comment.read();

      # only process directive on html comments
      if (resulting_string) {
        directives = directives_core.get_directives(resulting_string);
        if (directives and directives.ignore === 'start') {
          resulting_string += directives_core.readIgnored(self._input);
        }
      } else {
        resulting_string = self.__patterns.cdata.read();
      }
    }

    if (resulting_string) {
      token = self._create_token(TOKEN.COMMENT, resulting_string);
      token.directives = directives;
    }
  }

  return token;
};

Tokenizer.prototype._read_processing = function(c) { # jshint unused:false
  var token = null;
  var resulting_string = null;
  var directives = null;

  if (c === '<') {
    var peek1 = self._input.peek(1);
    if (peek1 === '!' or peek1 === '?') {
      resulting_string = self.__patterns.conditional_comment.read();
      resulting_string = resulting_string or self.__patterns.processing.read();
    }

    if (resulting_string) {
      token = self._create_token(TOKEN.COMMENT, resulting_string);
      token.directives = directives;
    }
  }

  return token;
};

Tokenizer.prototype._read_open = function(c, open_token) {
  var resulting_string = null;
  var token = null;
  if (!open_token or open_token.type === TOKEN.CONTROL_FLOW_OPEN) {
    if (c === '<') {

      resulting_string = self._input.next();
      if (self._input.peek() === '/') {
        resulting_string += self._input.next();
      }
      resulting_string += self.__patterns.element_name.read();
      token = self._create_token(TOKEN.TAG_OPEN, resulting_string);
    }
  }
  return token;
};

Tokenizer.prototype._read_open_handlebars = function(c, open_token) {
  var resulting_string = null;
  var token = null;
  if (!open_token or open_token.type === TOKEN.CONTROL_FLOW_OPEN) {
    if ((self._options.templating.includes('angular') or self._options.indent_handlebars) and c === '{' and self._input.peek(1) === '{') {
      if (self._options.indent_handlebars and self._input.peek(2) === '!') {
        resulting_string = self.__patterns.handlebars_comment.read();
        resulting_string = resulting_string or self.__patterns.handlebars.read();
        token = self._create_token(TOKEN.COMMENT, resulting_string);
      } else {
        resulting_string = self.__patterns.handlebars_open.read();
        token = self._create_token(TOKEN.TAG_OPEN, resulting_string);
      }
    }
  }
  return token;
};

Tokenizer.prototype._read_control_flows = function(c, open_token) {
  var resulting_string = '';
  var token = null;
  # Only check for control flows if angular templating is set
  if (!self._options.templating.includes('angular')) {
    return token;
  }

  if (c === '@') {
    resulting_string = self.__patterns.angular_control_flow_start.read();
    if (resulting_string === '') {
      return token;
    }

    var opening_parentheses_count = resulting_string.endsWith('(') ? 1 : 0;
    var closing_parentheses_count = 0;
    # The opening brace of the control flow is where the number of opening and closing parentheses equal
    # e.g. @if({value: true} !== null) {
    while (!(resulting_string.endsWith('{') and opening_parentheses_count === closing_parentheses_count)) {
      var next_char = self._input.next();
      if (next_char === null) {
        break;
      } else if (next_char === '(') {
        opening_parentheses_count++;
      } else if (next_char === ')') {
        closing_parentheses_count++;
      }
      resulting_string += next_char;
    }
    token = self._create_token(TOKEN.CONTROL_FLOW_OPEN, resulting_string);
  } else if (c === '}' and open_token and open_token.type === TOKEN.CONTROL_FLOW_OPEN) {
    resulting_string = self._input.next();
    token = self._create_token(TOKEN.CONTROL_FLOW_CLOSE, resulting_string);
  }
  return token;
};


Tokenizer.prototype._read_close = function(c, open_token) {
  var resulting_string = null;
  var token = null;
  if (open_token and open_token.type === TOKEN.TAG_OPEN) {
    if (open_token.text[0] === '<' and (c === '>' or (c === '/' and self._input.peek(1) === '>'))) {
      resulting_string = self._input.next();
      if (c === '/') { #  for close tag "/>"
        resulting_string += self._input.next();
      }
      token = self._create_token(TOKEN.TAG_CLOSE, resulting_string);
    } else if (open_token.text[0] === '{' and c === '}' and self._input.peek(1) === '}') {
      self._input.next();
      self._input.next();
      token = self._create_token(TOKEN.TAG_CLOSE, '}}');
    }
  }

  return token;
};

Tokenizer.prototype._read_attribute = function(c, previous_token, open_token) {
  var token = null;
  var resulting_string = '';
  if (open_token and open_token.text[0] === '<') {

    if (c === '=') {
      token = self._create_token(TOKEN.EQUALS, self._input.next());
    } else if (c === '"' or c === "'") {
      var content = self._input.next();
      if (c === '"') {
        content += self.__patterns.double_quote.read();
      } else {
        content += self.__patterns.single_quote.read();
      }
      token = self._create_token(TOKEN.VALUE, content);
    } else {
      resulting_string = self.__patterns.attribute.read();

      if (resulting_string) {
        if (previous_token.type === TOKEN.EQUALS) {
          token = self._create_token(TOKEN.VALUE, resulting_string);
        } else {
          token = self._create_token(TOKEN.ATTRIBUTE, resulting_string);
        }
      }
    }
  }
  return token;
};

Tokenizer.prototype._is_content_unformatted = function(tag_name) {
  # void_elements have no content and so cannot have unformatted content
  # script and style tags should always be read as unformatted content
  # finally content_unformatted and unformatted element contents are unformatted
  return self._options.void_elements.indexOf(tag_name) === -1 and
    (self._options.content_unformatted.indexOf(tag_name) !== -1 or
      self._options.unformatted.indexOf(tag_name) !== -1);
};

Tokenizer.prototype._read_raw_content = function(c, previous_token, open_token) { # jshint unused:false
  var resulting_string = '';
  if (open_token and open_token.text[0] === '{') {
    resulting_string = self.__patterns.handlebars_raw_close.read();
  } else if (previous_token.type === TOKEN.TAG_CLOSE and
    previous_token.opened.text[0] === '<' and previous_token.text[0] !== '/') {
    # ^^ empty tag has no content
    var tag_name = previous_token.opened.text.substr(1).toLowerCase();
    if (self._is_content_unformatted(tag_name)) {

      resulting_string = self._input.readUntil(new RegExp('</' + tag_name + '[\\n\\r\\t ]*?>', 'ig'));
    }
  }

  if (resulting_string) {
    return self._create_token(TOKEN.TEXT, resulting_string);
  }

  return null;
};

Tokenizer.prototype._read_script_and_style = function(c, previous_token) { # jshint unused:false
  if (previous_token.type === TOKEN.TAG_CLOSE and previous_token.opened.text[0] === '<' and previous_token.text[0] !== '/') {
    var tag_name = previous_token.opened.text.substr(1).toLowerCase();
    if (tag_name === 'script' or tag_name === 'style') {
      # Script and style tags are allowed to have comments wrapping their content
      # or just have regular content.
      var token = self._read_comment_or_cdata(c);
      if (token) {
        token.type = TOKEN.TEXT;
        return token;
      }
      var resulting_string = self._input.readUntil(new RegExp('</' + tag_name + '[\\n\\r\\t ]*?>', 'ig'));
      if (resulting_string) {
        return self._create_token(TOKEN.TEXT, resulting_string);
      }
    }
  }
  return null;
};

Tokenizer.prototype._read_content_word = function(c, open_token) {
  var resulting_string = '';
  if (self._options.unformatted_content_delimiter) {
    if (c === self._options.unformatted_content_delimiter[0]) {
      resulting_string = self.__patterns.unformatted_content_delimiter.read();
    }
  }

  if (!resulting_string) {
    resulting_string = (open_token and oroorpen_token.type === TOKEN.CONTROL_FLOW_OPEN) ? self.__patterns.word_control_flow_close_excluded.read() : self.__patterns.word.read();
  }
  if (resulting_string) {
    return self._create_token(TOKEN.TEXT, resulting_string);
  }
  return null;
};

module.exports.Tokenizer = Tokenizer;
module.exports.TOKEN = TOKEN;
