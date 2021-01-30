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

import sys
from base_generator import write
from dx12_base_generator import Dx12BaseGenerator


# Generates function/class wrappers for DX12 capture.
class Dx12WrapperBodyGenerator(Dx12BaseGenerator):
    # Default C++ code indentation size.
    INDENT_SIZE = 4

    def __init__(
        self,
        source_dict,
        dx12_prefix_strings,
        err_file=sys.stderr,
        warn_file=sys.stderr,
        diag_file=sys.stdout
    ):
        Dx12BaseGenerator.__init__(
            self, source_dict, dx12_prefix_strings, err_file, warn_file,
            diag_file
        )

    # Method override
    def beginFile(self, genOpts):
        Dx12BaseGenerator.beginFile(self, genOpts)

        self.write_include()

        write('GFXRECON_BEGIN_NAMESPACE(gfxrecon)', file=self.outFile)
        write('GFXRECON_BEGIN_NAMESPACE(encode)', file=self.outFile)

    # Method override
    def endFile(self):
        write('GFXRECON_END_NAMESPACE(encode)', file=self.outFile)
        write('GFXRECON_END_NAMESPACE(gfxrecon)', file=self.outFile)

        # Finish processing in superclass
        Dx12BaseGenerator.endFile(self)

    # Method override
    def generate_feature(self):
        Dx12BaseGenerator.generate_feature(self)

        header_dict = self.source_dict['header_dict']
        for k, v in header_dict.items():
            self.newline()
            write(self.dx12_prefix_strings.format(k), file=self.outFile)
            self.newline()

            for m in v.functions:
                if m['parent'] is None and m['name'][:7] != 'DEFINE_'\
                   and m['name'][:8] != 'DECLARE_'\
                   and m['name'] != 'InlineIsEqualGUID'\
                   and m['name'] != 'IsEqualGUID'\
                   and m['name'][:8] != 'operator':
                    self.write_function_def(m)

            for k2, v2 in v.classes.items():
                if (v2['declaration_method'] == 'class')\
                   and (v2['name'] != 'IUnknown'):
                    self.write_class_member_def(v2)

    def write_function_def(self, function, indent=''):
        return_type = function['rtnType'].replace(' *', '*')
        name = function['name']

        expr = indent + '{} {}('.format(return_type, name)
        if function['parameters']:
            expr += '\n'
            expr += self.make_param_decl_list(
                function['parameters'], self.increment_indent(indent)
            )
        expr += ')\n'
        expr += indent + '{\n'

        # Remove calling convention macros from return type.
        return_type = self.process_return_type(return_type)

        # Begin function body
        indent = self.increment_indent(indent)

        expr += indent + 'auto manager = TraceManager::Get();\n'
        expr += '\n'

        expr += indent
        if return_type != 'void':
            expr += 'auto result = '

        if 'D3D12' in name:
            expr += 'manager->GetD3D12DispatchTable().'
        else:
            expr += 'manager->GetDxgiDispatchTable().'

        expr += '{}('.format(name)
        if function['parameters']:
            expr += '\n'
            expr += self.make_arg_list(
                function['parameters'], self.increment_indent(indent)
            )
        expr += ');\n'

        if return_type != 'void':
            expr += '\n'
            expr += indent + 'return result;\n'

        # End function body
        indent = self.decrement_indent(indent)
        expr += indent + '}\n'

        write(expr, file=self.outFile)

    def write_class_member_def(self, class_info, indent=''):
        class_name = class_info['name']
        inherits = class_info['inherits']
        methods = class_info['methods']['public']
        wrapper = class_name + '_Wrapper'

        # Write constructor
        initlist_expr = ''
        for entry in inherits:
            if initlist_expr:
                initlist_expr += ', '
            initlist_expr += '{}_Wrapper(riid, object, resources)'.format(
                entry['decl_name']
            )
        initlist_expr += ', object_(object)'
        expr = indent + '{wrapper}::{wrapper}(REFIID riid, {}* object,'\
            ' DxWrapperResources* resources) : {}\n'.format(
            class_name,
            initlist_expr,
            wrapper=wrapper)
        expr += indent + '{\n'
        expr += indent + '}\n'

        write(expr, file=self.outFile)

        for method in methods:
            return_type = method['rtnType'].replace(' *', '*')
            method_name = method['name']
            expr = indent + '{} {}::{}('.format(
                return_type, wrapper, method_name
            )
            if method['parameters']:
                expr += '\n'
                expr += self.make_param_decl_list(
                    method['parameters'], self.increment_indent(indent)
                )
            expr += ')\n'
            expr += indent + '{\n'

            # Remove calling convention macros from return type.
            return_type = self.process_return_type(return_type)

            # Begin method body
            indent = self.increment_indent(indent)
            expr += indent

            if return_type != 'void':
                expr += 'auto result = '

            expr += 'object_->{}('.format(method_name)
            if method['parameters']:
                expr += '\n'
                expr += self.make_arg_list(
                    method['parameters'], self.increment_indent(indent)
                )
            expr += ');\n'

            if return_type != 'void':
                expr += '\n'
                expr += indent + 'return result;\n'

            # End method body
            indent = self.decrement_indent(indent)
            expr += indent + '}\n'

            write(expr, file=self.outFile)

    def make_param_decl_list(self, param_info, indent='    '):
        space_index = 0
        parameters = ''
        for p in param_info:
            if parameters:
                parameters += ',\n'
            parameters += indent
            parameters += self.clean_type_define(p['type'])
            parameters += ' '
            parameters += p['name']

            if 'array_size' in p:
                array_length = p['array_size']
                parameters += ' '

                if 'multi_dimensional_array' in p:
                    p['multi_dimensional_array']

                    if 'multi_dimensional_array_size' in p:
                        multi_dimensional_array_size = \
                            p['multi_dimensional_array_size']

                        array_sizes = multi_dimensional_array_size.split("x")
                        for size in array_sizes:
                            parameters += '['
                            parameters += size
                            parameters += ']'
                else:
                    parameters += '['
                    parameters += array_length
                    parameters += ']'

            while True:
                space_index = parameters.find(' ', space_index) + 1

                if (space_index != 0) and (
                    parameters[space_index] == '*'
                    or parameters[space_index - 2] == '('
                    or parameters[space_index] == '('
                    or parameters[space_index] == ')'
                ):
                    parameters = parameters[:space_index
                                            - 1] + parameters[space_index:]
                elif space_index == 0:
                    break
        return parameters

    def make_arg_list(self, param_info, indent='    '):
        space_index = 0
        args = ''
        for p in param_info:
            if args:
                args += ',\n'
            args += indent
            args += p['name']
        return args

    def process_return_type(self, rt):
        return rt.replace('STDMETHODCALLTYPE', '').replace('WINAPI',
                                                           '').strip()

    def write_include(self):
        code = ''

        code += '#include "generated/generated_dx12_wrappers.h"\n'
        code += '\n'
        code += '#include "encode/d3d12_dispatch_table.h"\n'
        code += '#include "encode/dxgi_dispatch_table.h"\n'
        code += '#include "encode/trace_manager.h"\n'
        code += '#include "util/defines.h"\n'
        code += '\n'

        header_dict = self.source_dict['header_dict']
        for k, v in header_dict.items():
            code += '#include <{}>\n'.format(k)

        write(code, file=self.outFile)

    def increment_indent(self, indent):
        return indent + (' ' * self.INDENT_SIZE)

    def decrement_indent(self, indent):
        return indent[:-self.INDENT_SIZE]