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

from ..core.output import Output
# XXX: these are wrong options ! must be html-specific
from ..core.options import Options
from .tokenizer import Tokenizer, TOKEN

lineBreak = r'\r\n|[\r\n]';
# XXX: Wrong, there was global (multiline ?) mode
# allLineBreaks = /\r\n|[\r\n]/g;
allLineBreaks = r'\r\n|[\r\n]';

class Printer:
  def __init__(self, options, base_indent_string):  # handles input/output and some other printing functions

    self.indent_level = 0;
    self.alignment_size = 0;
    self.max_preserve_newlines = options.max_preserve_newlines;
    self.preserve_newlines = options.preserve_newlines;

    self._output = Output(options, base_indent_string);

  def current_line_has_match(self, pattern):
    return self._output.current_line.has_match(pattern);


  def set_space_before_token(self, value, non_breaking):
    self._output.space_before_token = value;
    self._output.non_breaking_space = non_breaking;

  def set_wrap_point(self):
    self._output.set_indent(self.indent_level, self.alignment_size)
    self._output.set_wrap_point();



  def add_raw_token(self, token):
    self._output.add_raw_token(token);

  def print_preserved_newlines(self, raw_token):
    newlines = 0;
    if (raw_token.type != TOKEN.TEXT and raw_token.previous.type != TOKEN.TEXT) {
      newlines = raw_token.newlines ? 1 : 0;
    }

    if (self.preserve_newlines) {
      newlines = raw_token.newlines < self.max_preserve_newlines + 1 ? raw_token.newlines : self.max_preserve_newlines + 1;
    }
    for (var n = 0; n < newlines; n++) {
      self.print_newline(n > 0);
    }

    return newlines != 0;


    def traverse_whitespace = function(raw_token) {
      if (raw_token.whitespace_before or raw_token.newlines) {
        if (!self.print_preserved_newlines(raw_token)) {
          self._output.space_before_token = true;
        }
        return true;
      }
      return false;
    };

    def previous_token_wrapped = function() {
      return self._output.previous_token_wrapped;
    };

    def print_newline = function(force) {
      self._output.add_new_line(force);
    };

    def print_token = function(token) {
      if (token.text) {
        self._output.set_indent(self.indent_level, self.alignment_size);
        self._output.add_token(token.text);
      }
    };

    def indent = function() {
      self.indent_level++;
    };

    def deindent = function() {
      if (self.indent_level > 0) {
        self.indent_level--;
        self._output.set_indent(self.indent_level, self.alignment_size);
      }
    };

    def get_full_indent = function(level) {
      level = self.indent_level + (level or 0);
      if (level < 1) {
        return '';
      }

      return self._output.get_indent_string(level);
    };

def get_type_attribute(start_token):
  var result = null;
  var raw_token = start_token.next;

  #  Search attributes for a type attribute
  while (raw_token.type != TOKEN.EOF and start_token.closed != raw_token) {
    if (raw_token.type == TOKEN.ATTRIBUTE and raw_token.text == 'type') {
      if (raw_token.next and raw_token.next.type == TOKEN.EQUALS and
        raw_token.next.next and raw_token.next.next.type == TOKEN.VALUE) {
        result = raw_token.next.next.text;
      }
      break;
    }
    raw_token = raw_token.next;
  }

  return result;


def get_custom_beautifier_name(tag_check, raw_token):
  var typeAttribute = null;
  var result = null;

  if (!raw_token.closed) {
    return null;
  }

  if (tag_check == 'script') {
    typeAttribute = 'text/javascript';
  } elif (tag_check == 'style') {
    typeAttribute = 'text/css';
  }

  typeAttribute = get_type_attribute(raw_token) or typeAttribute;

  #  For script and style tags that have a type attribute, only enable custom beautifiers for matching values
  #  For those without a type attribute use default;
  if (typeAttribute.search('text/css') > -1) {
    result = 'css';
  } elif (typeAttribute.search(/module|((text|application|dojo)\/(x-)?(javascript|ecmascript|jscript|livescript|(ld\+)?json|method|aspect))/) > -1) {
    result = 'javascript';
  } elif (typeAttribute.search(/(text|application|dojo)\/(x-)?(html)/) > -1) {
    result = 'html';
  } elif (typeAttribute.search(/test\/null/) > -1) {
    #  Test only mime-type for testing the beautifier when null is passed as beautifing function
    result = 'null';
  }

  return result;
};

def in_array(what, arr):
  return arr.indexOf(what) != -1;

class TagFrame:
  def __init__(self, parent, parser_token, indent_level):
    self.parent = parent or null;
    self.tag = parser_token ? parser_token.tag_name : '';
    self.indent_level = indent_level or 0;
    self.parser_token = parser_token or null;

class TagStack:
  def __init__(self, printer):
    self._printer = printer;
    self._current_frame = null;

  def get_parser_token(self, ):
    return self._current_frame ? self._current_frame.parser_token : null;


  def record_tag(self, parser_token): # function to record a tag and its parent in self.tags Object
    var new_frame = new TagFrame(self._current_frame, parser_token, self._printer.indent_level);
    self._current_frame = new_frame;


  def _try_pop_frame(self, frame): # function to retrieve the opening tag to the corresponding closer
    var parser_token = null;

    if (frame) {
      parser_token = frame.parser_token;
      self._printer.indent_level = frame.indent_level;
      self._current_frame = frame.parent;
    }

    return parser_token;


  def _get_frame(self, tag_list, stop_list): # function to retrieve the opening tag to the corresponding closer
    var frame = self._current_frame;

    while (frame) { # till we reach '' (the initial value);
      if (tag_list.indexOf(frame.tag) != -1) { # if this is it use it
        break;
      } elif (stop_list and stop_list.indexOf(frame.tag) != -1) {
        frame = null;
        break;
      }
      frame = frame.parent;
    }

    return frame;


  def try_pop(self, tag, stop_list): # function to retrieve the opening tag to the corresponding closer
    var frame = self._get_frame([tag], stop_list);
    return self._try_pop_frame(frame);


  def indent_to_tag(self, tag_list):
    var frame = self._get_frame(tag_list);
    if (frame) {
      self._printer.indent_level = frame.indent_level;
    }

var TagOpenParserToken = function(options, parent, raw_token) {
  self.parent = parent or null;
  self.text = '';
  self.type = 'TK_TAG_OPEN';
  self.tag_name = '';
  self.is_inline_element = false;
  self.is_unformatted = false;
  self.is_content_unformatted = false;
  self.is_empty_element = false;
  self.is_start_tag = false;
  self.is_end_tag = false;
  self.indent_content = false;
  self.multiline_content = false;
  self.custom_beautifier_name = null;
  self.start_tag_token = null;
  self.attr_count = 0;
  self.has_wrapped_attrs = false;
  self.alignment_size = 0;
  self.tag_complete = false;
  self.tag_start_char = '';
  self.tag_check = '';

  if (!raw_token) {
    self.tag_complete = true;
  } else {
    var tag_check_match;

    self.tag_start_char = raw_token.text[0];
    self.text = raw_token.text;

    if (self.tag_start_char == '<') {
      tag_check_match = raw_token.text.match(/^<([^\s>]*)/);
      self.tag_check = tag_check_match ? tag_check_match[1] : '';
    } else {
      tag_check_match = raw_token.text.match(/^{{~?(?:[\^]|#\*?)?([^\s}]+)/);
      self.tag_check = tag_check_match ? tag_check_match[1] : '';

      #  handle "{{#> myPartial}}" or "{{~#> myPartial}}"
      if ((raw_token.text.startsWith('{{#>') or raw_token.text.startsWith('{{~#>')) and self.tag_check[0] == '>') {
        if (self.tag_check == '>' and raw_token.next != null) {
          self.tag_check = raw_token.next.text.split(' ')[0];
        } else {
          self.tag_check = raw_token.text.split('>')[1];
        }
      }
    }

    self.tag_check = self.tag_check.toLowerCase();

    if (raw_token.type == TOKEN.COMMENT) {
      self.tag_complete = true;
    }

    self.is_start_tag = self.tag_check.charAt(0) != '/';
    self.tag_name = !self.is_start_tag ? self.tag_check.substr(1) : self.tag_check;
    self.is_end_tag = !self.is_start_tag ||
      (raw_token.closed and raw_token.closed.text == '/>');

    #  if whitespace handler ~ included (i.e. {{~#if true}}), handlebars tags start at pos 3 not pos 2
    var handlebar_starts = 2;
    if (self.tag_start_char == '{' and self.text.length >= 3) {
      if (self.text.charAt(2) == '~') {
        handlebar_starts = 3;
      }
    }

    #  handlebars tags that don't start with # or ^ are single_tags, and so also start and end.
    #  if they start with # or ^, they are still considered single tags if indenting of handlebars is set to false
    self.is_end_tag = self.is_end_tag ||
      (self.tag_start_char == '{' and (!options.indent_handlebars or self.text.length < 3 or (/[^#\^]/.test(self.text.charAt(handlebar_starts)))));
  }
};

function Beautifier(source_text, options, js_beautify, css_beautify) {
  def __init__(self, source_text, options, js_beautify, css_beautify):
    # Wrapper function to invoke all the necessary constructors and deal with the output.
    self._source_text = source_text or '';
    options = options or {};
    self._js_beautify = js_beautify;
    self._css_beautify = css_beautify;
    self._tag_stack = null;

    #  Allow the setting of language/file-type specific options
    #  with inheritance of overall settings
    var optionHtml = new Options(options, 'html');

    self._options = optionHtml;

    self._is_wrap_attributes_force = self._options.wrap_attributes.substr(0, 'force'.length) == 'force';
    self._is_wrap_attributes_force_expand_multiline = (self._options.wrap_attributes == 'force-expand-multiline');
    self._is_wrap_attributes_force_aligned = (self._options.wrap_attributes == 'force-aligned');
    self._is_wrap_attributes_aligned_multiple = (self._options.wrap_attributes == 'aligned-multiple');
    self._is_wrap_attributes_preserve = self._options.wrap_attributes.substr(0, 'preserve'.length) == 'preserve';
    self._is_wrap_attributes_preserve_aligned = (self._options.wrap_attributes == 'preserve-aligned');
  }

  def beautify(self, ):

    #  if disabled, return the input unchanged.
    if (self._options.disabled) {
      return self._source_text;
    }

    var source_text = self._source_text;
    var eol = self._options.eol;
    if (self._options.eol == 'auto') {
      eol = '\n';
      if (source_text and lineBreak.test(source_text)) {
        eol = source_text.match(lineBreak)[0];
      }
    }

    #  HACK: newline parsing inconsistent. This brute force normalizes the input.
    source_text = source_text.replace(allLineBreaks, '\n');

    var baseIndentString = source_text.match(/^[\t ]*/)[0];

    var last_token = {
      text: '',
      type: ''
    };

    var last_tag_token = new TagOpenParserToken(self._options);

    var printer = new Printer(self._options, baseIndentString);
    var tokens = new Tokenizer(source_text, self._options).tokenize();

    self._tag_stack = new TagStack(printer);

    var parser_token = null;
    var raw_token = tokens.next();
    while (raw_token.type != TOKEN.EOF) {

      if (raw_token.type == TOKEN.TAG_OPEN or raw_token.type == TOKEN.COMMENT) {
        parser_token = self._handle_tag_open(printer, raw_token, last_tag_token, last_token, tokens);
        last_tag_token = parser_token;
      } elif ((raw_token.type == TOKEN.ATTRIBUTE or raw_token.type == TOKEN.EQUALS or raw_token.type == TOKEN.VALUE) ||
        (raw_token.type == TOKEN.TEXT and !last_tag_token.tag_complete)) {
        parser_token = self._handle_inside_tag(printer, raw_token, last_tag_token, last_token);
      } elif (raw_token.type == TOKEN.TAG_CLOSE) {
        parser_token = self._handle_tag_close(printer, raw_token, last_tag_token);
      } elif (raw_token.type == TOKEN.TEXT) {
        parser_token = self._handle_text(printer, raw_token, last_tag_token);
      } elif (raw_token.type == TOKEN.CONTROL_FLOW_OPEN) {
        parser_token = self._handle_control_flow_open(printer, raw_token);
      } elif (raw_token.type == TOKEN.CONTROL_FLOW_CLOSE) {
        parser_token = self._handle_control_flow_close(printer, raw_token);
      } else {
        #  This should never happen, but if it does. Print the raw token
        printer.add_raw_token(raw_token);
      }

      last_token = parser_token;

      raw_token = tokens.next();
    }
    var sweet_code = printer._output.get_code(eol);

    return sweet_code;
  };

  def _handle_control_flow_open(self, printer, raw_token):
    var parser_token = {
      text: raw_token.text,
      type: raw_token.type
    };
    printer.set_space_before_token(raw_token.newlines or raw_token.whitespace_before != '', true);
    if (raw_token.newlines) {
      printer.print_preserved_newlines(raw_token);
    } else {
      printer.set_space_before_token(raw_token.newlines or raw_token.whitespace_before != '', true);
    }
    printer.print_token(raw_token);
    printer.indent();
    return parser_token;
  };

  def _handle_control_flow_close(self, printer, raw_token):
    var parser_token = {
      text: raw_token.text,
      type: raw_token.type
    };

    printer.deindent();
    if (raw_token.newlines) {
      printer.print_preserved_newlines(raw_token);
    } else {
      printer.set_space_before_token(raw_token.newlines or raw_token.whitespace_before != '', true);
    }
    printer.print_token(raw_token);
    return parser_token;
  };

  def _handle_tag_close(self, printer, raw_token, last_tag_token):
    var parser_token = {
      text: raw_token.text,
      type: raw_token.type
    };
    printer.alignment_size = 0;
    last_tag_token.tag_complete = true;

    printer.set_space_before_token(raw_token.newlines or raw_token.whitespace_before != '', true);
    if (last_tag_token.is_unformatted) {
      printer.add_raw_token(raw_token);
    } else {
      if (last_tag_token.tag_start_char == '<') {
        printer.set_space_before_token(raw_token.text[0] == '/', true); #  space before />, no space before >
        if (self._is_wrap_attributes_force_expand_multiline and last_tag_token.has_wrapped_attrs) {
          printer.print_newline(false);
        }
      }
      printer.print_token(raw_token);

    }

    if (last_tag_token.indent_content and
      !(last_tag_token.is_unformatted or last_tag_token.is_content_unformatted)) {
      printer.indent();

      #  only indent once per opened tag
      last_tag_token.indent_content = false;
    }

    if (!last_tag_token.is_inline_element and
      !(last_tag_token.is_unformatted or last_tag_token.is_content_unformatted)) {
      printer.set_wrap_point();
    }

    return parser_token;
  };

  def _handle_inside_tag(self, printer, raw_token, last_tag_token, last_token):
    var wrapped = last_tag_token.has_wrapped_attrs;
    var parser_token = {
      text: raw_token.text,
      type: raw_token.type
    };

    printer.set_space_before_token(raw_token.newlines or raw_token.whitespace_before != '', true);
    if (last_tag_token.is_unformatted) {
      printer.add_raw_token(raw_token);
    } elif (last_tag_token.tag_start_char == '{' and raw_token.type == TOKEN.TEXT) {
      #  For the insides of handlebars allow newlines or a single space between open and contents
      if (printer.print_preserved_newlines(raw_token)) {
        raw_token.newlines = 0;
        printer.add_raw_token(raw_token);
      } else {
        printer.print_token(raw_token);
      }
    } else {
      if (raw_token.type == TOKEN.ATTRIBUTE) {
        printer.set_space_before_token(true);
      } elif (raw_token.type == TOKEN.EQUALS) { # no space before =
        printer.set_space_before_token(false);
      } elif (raw_token.type == TOKEN.VALUE and raw_token.previous.type == TOKEN.EQUALS) { # no space before value
        printer.set_space_before_token(false);
      }

      if (raw_token.type == TOKEN.ATTRIBUTE and last_tag_token.tag_start_char == '<') {
        if (self._is_wrap_attributes_preserve or self._is_wrap_attributes_preserve_aligned) {
          printer.traverse_whitespace(raw_token);
          wrapped = wrapped or raw_token.newlines != 0;
        }

        #  Wrap for 'force' options, and if the number of attributes is at least that specified in 'wrap_attributes_min_attrs':
        #  1. always wrap the second and beyond attributes
        #  2. wrap the first attribute only if 'force-expand-multiline' is specified
        if (self._is_wrap_attributes_force and
          last_tag_token.attr_count >= self._options.wrap_attributes_min_attrs and
          (last_token.type != TOKEN.TAG_OPEN or #  ie. second attribute and beyond
            self._is_wrap_attributes_force_expand_multiline)) {
          printer.print_newline(false);
          wrapped = true;
        }
      }
      printer.print_token(raw_token);
      wrapped = wrapped or printer.previous_token_wrapped();
      last_tag_token.has_wrapped_attrs = wrapped;
    }
    return parser_token;
  };

  def _handle_text(self, printer, raw_token, last_tag_token):
    var parser_token = {
      text: raw_token.text,
      type: 'TK_CONTENT'
    };
    if (last_tag_token.custom_beautifier_name) { # check if we need to format javascript
      self._print_custom_beatifier_text(printer, raw_token, last_tag_token);
    } elif (last_tag_token.is_unformatted or last_tag_token.is_content_unformatted) {
      printer.add_raw_token(raw_token);
    } else {
      printer.traverse_whitespace(raw_token);
      printer.print_token(raw_token);
    }
    return parser_token;
  };

  def _print_custom_beatifier_text(self, printer, raw_token, last_tag_token):
    var local = this;
    if (raw_token.text != '') {

      var text = raw_token.text,
        _beautifier,
        script_indent_level = 1,
        pre = '',
        post = '';
      if (last_tag_token.custom_beautifier_name == 'javascript' and typeof self._js_beautify == 'function') {
        _beautifier = self._js_beautify;
      } elif (last_tag_token.custom_beautifier_name == 'css' and typeof self._css_beautify == 'function') {
        _beautifier = self._css_beautify;
      } elif (last_tag_token.custom_beautifier_name == 'html') {
        _beautifier = function(html_source, options) {
          var beautifier = new Beautifier(html_source, options, local._js_beautify, local._css_beautify);
          return beautifier.beautify();
        };
      }

      if (self._options.indent_scripts == "keep") {
        script_indent_level = 0;
      } elif (self._options.indent_scripts == "separate") {
        script_indent_level = -printer.indent_level;
      }

      var indentation = printer.get_full_indent(script_indent_level);

      #  if there is at least one empty line at the end of this text, strip it
      #  we'll be adding one back after the text but before the containing tag.
      text = text.replace(/\n[ \t]*$/, '');

      #  Handle the case where content is wrapped in a comment or cdata.
      if (last_tag_token.custom_beautifier_name != 'html' and
        text[0] == '<' and text.match(/^(<!--|<!\[CDATA\[)/)) {
        var matched = /^(<!--[^\n]*|<!\[CDATA\[)(\n?)([ \t\n]*)([\s\S]*)(-->|]]>)$/.exec(text);

        #  if we start to wrap but don't finish, print raw
        if (!matched) {
          printer.add_raw_token(raw_token);
          return;
        }

        pre = indentation + matched[1] + '\n';
        text = matched[4];
        if (matched[5]) {
          post = indentation + matched[5];
        }

        #  if there is at least one empty line at the end of this text, strip it
        #  we'll be adding one back after the text but before the containing tag.
        text = text.replace(/\n[ \t]*$/, '');

        if (matched[2] or matched[3].indexOf('\n') != -1) {
          #  if the first line of the non-comment text has spaces
          #  use that as the basis for indenting in null case.
          matched = matched[3].match(/[ \t]+$/);
          if (matched) {
            raw_token.whitespace_before = matched[0];
          }
        }
      }

      if (text) {
        if (_beautifier) {

          #  call the Beautifier if avaliable
          var Child_options = function() {
            self.eol = '\n';
          };
          Child_options.prototype = self._options.raw_options;
          var child_options = new Child_options();
          text = _beautifier(indentation + text, child_options);
        } else {
          #  simply indent the string otherwise
          var white = raw_token.whitespace_before;
          if (white) {
            text = text.replace(new RegExp('\n(' + white + ')?', 'g'), '\n');
          }

          text = indentation + text.replace(/\n/g, '\n' + indentation);
        }
      }

      if (pre) {
        if (!text) {
          text = pre + post;
        } else {
          text = pre + text + '\n' + post;
        }
      }

      printer.print_newline(false);
      if (text) {
        raw_token.text = text;
        raw_token.whitespace_before = '';
        raw_token.newlines = 0;
        printer.add_raw_token(raw_token);
        printer.print_newline(true);
      }
    }
  };

  def _handle_tag_open(self, printer, raw_token, last_tag_token, last_token, tokens):
    var parser_token = self._get_tag_open_token(raw_token);

    if ((last_tag_token.is_unformatted or last_tag_token.is_content_unformatted) and
      !last_tag_token.is_empty_element and
      raw_token.type == TOKEN.TAG_OPEN and !parser_token.is_start_tag) {
      #  End element tags for unformatted or content_unformatted elements
      #  are printed raw to keep any newlines inside them exactly the same.
      printer.add_raw_token(raw_token);
      parser_token.start_tag_token = self._tag_stack.try_pop(parser_token.tag_name);
    } else {
      printer.traverse_whitespace(raw_token);
      self._set_tag_position(printer, raw_token, parser_token, last_tag_token, last_token);
      if (!parser_token.is_inline_element) {
        printer.set_wrap_point();
      }
      printer.print_token(raw_token);
    }

    #  count the number of attributes
    if (parser_token.is_start_tag and self._is_wrap_attributes_force) {
      var peek_index = 0;
      var peek_token;
      do {
        peek_token = tokens.peek(peek_index);
        if (peek_token.type == TOKEN.ATTRIBUTE) {
          parser_token.attr_count += 1;
        }
        peek_index += 1;
      } while (peek_token.type != TOKEN.EOF and peek_token.type != TOKEN.TAG_CLOSE);
    }

    # indent attributes an auto, forced, aligned or forced-align line-wrap
    if (self._is_wrap_attributes_force_aligned or self._is_wrap_attributes_aligned_multiple or self._is_wrap_attributes_preserve_aligned) {
      parser_token.alignment_size = raw_token.text.length + 1;
    }

    if (!parser_token.tag_complete and !parser_token.is_unformatted) {
      printer.alignment_size = parser_token.alignment_size;
    }

    return parser_token;
  };



  def _get_tag_open_token(self, raw_token): # function to get a full tag and parse its type
    var parser_token = new TagOpenParserToken(self._options, self._tag_stack.get_parser_token(), raw_token);

    parser_token.alignment_size = self._options.wrap_attributes_indent_size;

    parser_token.is_end_tag = parser_token.is_end_tag ||
      in_array(parser_token.tag_check, self._options.void_elements);

    parser_token.is_empty_element = parser_token.tag_complete ||
      (parser_token.is_start_tag and parser_token.is_end_tag);

    parser_token.is_unformatted = !parser_token.tag_complete and in_array(parser_token.tag_check, self._options.unformatted);
    parser_token.is_content_unformatted = !parser_token.is_empty_element and in_array(parser_token.tag_check, self._options.content_unformatted);
    parser_token.is_inline_element = in_array(parser_token.tag_name, self._options.inline) or (self._options.inline_custom_elements and parser_token.tag_name.includes("-")) or parser_token.tag_start_char == '{';

    return parser_token;
  };

  def _set_tag_position(self, printer, raw_token, parser_token, last_tag_token, last_token):

    if (!parser_token.is_empty_element) {
      if (parser_token.is_end_tag) { # this tag is a double tag so check for tag-ending
        parser_token.start_tag_token = self._tag_stack.try_pop(parser_token.tag_name); # remove it and all ancestors
      } else { #  it's a start-tag
        #  check if this tag is starting an element that has optional end element
        #  and do an ending needed
        if (self._do_optional_end_element(parser_token)) {
          if (!parser_token.is_inline_element) {
            printer.print_newline(false);
          }
        }

        self._tag_stack.record_tag(parser_token); # push it on the tag stack

        if ((parser_token.tag_name == 'script' or parser_token.tag_name == 'style') and
          !(parser_token.is_unformatted or parser_token.is_content_unformatted)) {
          parser_token.custom_beautifier_name = get_custom_beautifier_name(parser_token.tag_check, raw_token);
        }
      }
    }

    if (in_array(parser_token.tag_check, self._options.extra_liners)) { # check if this double needs an extra line
      printer.print_newline(false);
      if (!printer._output.just_added_blankline()) {
        printer.print_newline(true);
      }
    }

    if (parser_token.is_empty_element) { # if this tag name is a single tag type (either in the list or has a closing /)

      #  if you hit an else case, reset the indent level if you are inside an:
      #  'if', 'unless', or 'each' block.
      if (parser_token.tag_start_char == '{' and parser_token.tag_check == 'else') {
        self._tag_stack.indent_to_tag(['if', 'unless', 'each']);
        parser_token.indent_content = true;
        #  Don't add a newline if opening {{#if}} tag is on the current line
        var foundIfOnCurrentLine = printer.current_line_has_match(/{{#if/);
        if (!foundIfOnCurrentLine) {
          printer.print_newline(false);
        }
      }

      #  Don't add a newline before elements that should remain where they are.
      if (parser_token.tag_name == '!--' and last_token.type == TOKEN.TAG_CLOSE and
        last_tag_token.is_end_tag and parser_token.text.indexOf('\n') == -1) {
        # Do nothing. Leave comments on same line.
      } else {
        if (!(parser_token.is_inline_element or parser_token.is_unformatted)) {
          printer.print_newline(false);
        }
        self._calcluate_parent_multiline(printer, parser_token);
      }
    } elif (parser_token.is_end_tag) { # this tag is a double tag so check for tag-ending
      var do_end_expand = false;

      #  deciding whether a block is multiline should not be this hard
      do_end_expand = parser_token.start_tag_token and parser_token.start_tag_token.multiline_content;
      do_end_expand = do_end_expand or (!parser_token.is_inline_element and
        !(last_tag_token.is_inline_element or last_tag_token.is_unformatted) and
        !(last_token.type == TOKEN.TAG_CLOSE and parser_token.start_tag_token == last_tag_token) and
        last_token.type != 'TK_CONTENT'
      );

      if (parser_token.is_content_unformatted or parser_token.is_unformatted) {
        do_end_expand = false;
      }

      if (do_end_expand) {
        printer.print_newline(false);
      }
    } else { #  it's a start-tag
      parser_token.indent_content = !parser_token.custom_beautifier_name;

      if (parser_token.tag_start_char == '<') {
        if (parser_token.tag_name == 'html') {
          parser_token.indent_content = self._options.indent_inner_html;
        } elif (parser_token.tag_name == 'head') {
          parser_token.indent_content = self._options.indent_head_inner_html;
        } elif (parser_token.tag_name == 'body') {
          parser_token.indent_content = self._options.indent_body_inner_html;
        }
      }

      if (!(parser_token.is_inline_element or parser_token.is_unformatted) and
        (last_token.type != 'TK_CONTENT' or parser_token.is_content_unformatted)) {
        printer.print_newline(false);
      }

      self._calcluate_parent_multiline(printer, parser_token);
    }
  };

  def _calcluate_parent_multiline(self, printer, parser_token):
    if (parser_token.parent and printer._output.just_added_newline() and
      !((parser_token.is_inline_element or parser_token.is_unformatted) and parser_token.parent.is_inline_element)) {
      parser_token.parent.multiline_content = true;
    }
  };

  # To be used for <p> tag special case:
  var p_closers = ['address', 'article', 'aside', 'blockquote', 'details', 'div', 'dl', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'main', 'menu', 'nav', 'ol', 'p', 'pre', 'section', 'table', 'ul'];
  var p_parent_excludes = ['a', 'audio', 'del', 'ins', 'map', 'noscript', 'video'];

  def _do_optional_end_element(self, parser_token):
    var result = null;
    #  NOTE: cases of "if there is no more content in the parent element"
    #  are handled automatically by the beautifier.
    #  It assumes parent or ancestor close tag closes all children.
    #  https:# www.w3.org/TR/html5/syntax.html#optional-tags
    if (parser_token.is_empty_element or !parser_token.is_start_tag or !parser_token.parent) {
      return;

    }

    if (parser_token.tag_name == 'body') {
      #  A head element’s end tag may be omitted if the head element is not immediately followed by a space character or a comment.
      result = result or self._tag_stack.try_pop('head');

      # } elif (parser_token.tag_name == 'body') {
      #  DONE: A body element’s end tag may be omitted if the body element is not immediately followed by a comment.

    } elif (parser_token.tag_name == 'li') {
      #  An li element’s end tag may be omitted if the li element is immediately followed by another li element or if there is no more content in the parent element.
      result = result or self._tag_stack.try_pop('li', ['ol', 'ul', 'menu']);

    } elif (parser_token.tag_name == 'dd' or parser_token.tag_name == 'dt') {
      #  A dd element’s end tag may be omitted if the dd element is immediately followed by another dd element or a dt element, or if there is no more content in the parent element.
      #  A dt element’s end tag may be omitted if the dt element is immediately followed by another dt element or a dd element.
      result = result or self._tag_stack.try_pop('dt', ['dl']);
      result = result or self._tag_stack.try_pop('dd', ['dl']);


    } elif (parser_token.parent.tag_name == 'p' and p_closers.indexOf(parser_token.tag_name) != -1) {
      #  IMPORTANT: this else-if works because p_closers has no overlap with any other element we look for in this method
      #  check for the parent element is an HTML element that is not an <a>, <audio>, <del>, <ins>, <map>, <noscript>, or <video> element,  or an autonomous custom element.
      #  To do this right, this needs to be coded as an inclusion of the inverse of the exclusion above.
      #  But to start with (if we ignore "autonomous custom elements") the exclusion would be fine.
      var p_parent = parser_token.parent.parent;
      if (!p_parent or p_parent_excludes.indexOf(p_parent.tag_name) == -1) {
        result = result or self._tag_stack.try_pop('p');
      }
    } elif (parser_token.tag_name == 'rp' or parser_token.tag_name == 'rt') {
      #  An rt element’s end tag may be omitted if the rt element is immediately followed by an rt or rp element, or if there is no more content in the parent element.
      #  An rp element’s end tag may be omitted if the rp element is immediately followed by an rt or rp element, or if there is no more content in the parent element.
      result = result or self._tag_stack.try_pop('rt', ['ruby', 'rtc']);
      result = result or self._tag_stack.try_pop('rp', ['ruby', 'rtc']);

    } elif (parser_token.tag_name == 'optgroup') {
      #  An optgroup element’s end tag may be omitted if the optgroup element is immediately followed by another optgroup element, or if there is no more content in the parent element.
      #  An option element’s end tag may be omitted if the option element is immediately followed by another option element, or if it is immediately followed by an optgroup element, or if there is no more content in the parent element.
      result = result or self._tag_stack.try_pop('optgroup', ['select']);
      # result = result or self._tag_stack.try_pop('option', ['select']);

    } elif (parser_token.tag_name == 'option') {
      #  An option element’s end tag may be omitted if the option element is immediately followed by another option element, or if it is immediately followed by an optgroup element, or if there is no more content in the parent element.
      result = result or self._tag_stack.try_pop('option', ['select', 'datalist', 'optgroup']);

    } elif (parser_token.tag_name == 'colgroup') {
      #  DONE: A colgroup element’s end tag may be omitted if the colgroup element is not immediately followed by a space character or a comment.
      #  A caption element's end tag may be ommitted if a colgroup, thead, tfoot, tbody, or tr element is started.
      result = result or self._tag_stack.try_pop('caption', ['table']);

    } elif (parser_token.tag_name == 'thead') {
      #  A colgroup element's end tag may be ommitted if a thead, tfoot, tbody, or tr element is started.
      #  A caption element's end tag may be ommitted if a colgroup, thead, tfoot, tbody, or tr element is started.
      result = result or self._tag_stack.try_pop('caption', ['table']);
      result = result or self._tag_stack.try_pop('colgroup', ['table']);

      # } elif (parser_token.tag_name == 'caption') {
      #  DONE: A caption element’s end tag may be omitted if the caption element is not immediately followed by a space character or a comment.

    } elif (parser_token.tag_name == 'tbody' or parser_token.tag_name == 'tfoot') {
      #  A thead element’s end tag may be omitted if the thead element is immediately followed by a tbody or tfoot element.
      #  A tbody element’s end tag may be omitted if the tbody element is immediately followed by a tbody or tfoot element, or if there is no more content in the parent element.
      #  A colgroup element's end tag may be ommitted if a thead, tfoot, tbody, or tr element is started.
      #  A caption element's end tag may be ommitted if a colgroup, thead, tfoot, tbody, or tr element is started.
      result = result or self._tag_stack.try_pop('caption', ['table']);
      result = result or self._tag_stack.try_pop('colgroup', ['table']);
      result = result or self._tag_stack.try_pop('thead', ['table']);
      result = result or self._tag_stack.try_pop('tbody', ['table']);

      # } elif (parser_token.tag_name == 'tfoot') {
      #  DONE: A tfoot element’s end tag may be omitted if there is no more content in the parent element.

    } elif (parser_token.tag_name == 'tr') {
      #  A tr element’s end tag may be omitted if the tr element is immediately followed by another tr element, or if there is no more content in the parent element.
      #  A colgroup element's end tag may be ommitted if a thead, tfoot, tbody, or tr element is started.
      #  A caption element's end tag may be ommitted if a colgroup, thead, tfoot, tbody, or tr element is started.
      result = result or self._tag_stack.try_pop('caption', ['table']);
      result = result or self._tag_stack.try_pop('colgroup', ['table']);
      result = result or self._tag_stack.try_pop('tr', ['table', 'thead', 'tbody', 'tfoot']);

    } elif (parser_token.tag_name == 'th' or parser_token.tag_name == 'td') {
      #  A td element’s end tag may be omitted if the td element is immediately followed by a td or th element, or if there is no more content in the parent element.
      #  A th element’s end tag may be omitted if the th element is immediately followed by a td or th element, or if there is no more content in the parent element.
      result = result or self._tag_stack.try_pop('td', ['table', 'thead', 'tbody', 'tfoot', 'tr']);
      result = result or self._tag_stack.try_pop('th', ['table', 'thead', 'tbody', 'tfoot', 'tr']);
    }

    #  Start element omission not handled currently
    #  A head element’s start tag may be omitted if the element is empty, or if the first thing inside the head element is an element.
    #  A tbody element’s start tag may be omitted if the first thing inside the tbody element is a tr element, and if the element is not immediately preceded by a tbody, thead, or tfoot element whose end tag has been omitted. (It can’t be omitted if the element is empty.)
    #  A colgroup element’s start tag may be omitted if the first thing inside the colgroup element is a col element, and if the element is not immediately preceded by another colgroup element whose end tag has been omitted. (It can’t be omitted if the element is empty.)

    #  Fix up the parent of the parser token
    parser_token.parent = self._tag_stack.get_parser_token();

    return result;
};

module.exports.Beautifier = Beautifier;
