#!/usr/bin/env python3
#
# Copyright (c) 2021 LunarG, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from dx12_base_generator import *
from dx12_ascii_consumer_header_generator\
    import DX12AsciiConsumerHeaderGenerator


# Generates C++ functions responsible for consuming DX12 API calls
class DX12AsciiConsumerBodyGenerator(DX12AsciiConsumerHeaderGenerator):

    # Method override
    def write_include(self):
        write('#include "generated_dx12_ascii_consumer.h"', file=self.outFile)

    # Method override
    def generateFeature(self):
        DX12BaseGenerator.generateFeature(self)
        self.write_dx12_consumer_class('Ascii')

    # Method override
    def get_decoder_class_define(self, consumer_type):
        declaration = ''
        indent = ''
        function_class = 'DX12{}Consumer::'.format(consumer_type)
        class_end = ''
        return (declaration, indent, function_class, class_end)

    # Method override
    def get_consumer_function_body(self, class_name, method_info):
        if class_name:
            code = '\n'\
                   '{{\n'\
                   '    fprintf(GetFile(), "%s\\n", "{}::{}");\n'\
                   '}}\n'.format(class_name[1:], method_info['name'])
        else:
            code = '\n'\
                   '{{\n'\
                   '    fprintf(GetFile(), "%s\\n", "{}");\n'\
                   '}}\n'.format(method_info['name'])
        return code