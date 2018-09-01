#!/usr/bin/python3 -i
#
# Copyright (c) 2018 LunarG, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os,re,sys
from base_generator import *

# Eliminates JSON blackLists and platformTypes files, which are not necessary for
# pNext switch statement generation.
class DecodePNextStructGeneratorOptions(BaseGeneratorOptions):
    """Options for Vulkan API pNext structure decoding C++ code generation"""
    def __init__(self,
                 filename = None,
                 directory = '.',
                 prefixText = '',
                 protectFile = False,
                 protectFeature = True):
        BaseGeneratorOptions.__init__(self, None, None,
                                      filename, directory, prefixText,
                                      protectFile, protectFeature)

# DecodePNextStructGenerator - subclass of BaseGenerator.
# Generates C++ code for Vulkan API pNext structure decoding.
class DecodePNextStructGenerator(BaseGenerator):
    """Generate pNext structure decoding C++ code"""
    def __init__(self,
                 errFile = sys.stderr,
                 warnFile = sys.stderr,
                 diagFile = sys.stdout):
        BaseGenerator.__init__(self,
                               processCmds=False, processStructs=False, featureBreak=False,
                               errFile=errFile, warnFile=warnFile, diagFile=diagFile)

        # Map to store VkStructureType enum values.
        self.sTypeValues = dict()

    # Method override
    def beginFile(self, genOpts):
        BaseGenerator.beginFile(self, genOpts)

        write('#include <cassert>', file=self.outFile)
        write('#include <memory>', file=self.outFile)
        self.newline()
        write('#include "vulkan/vulkan.h"', file=self.outFile)
        self.newline()
        write('#include "util/defines.h"', file=self.outFile)
        write('#include "format/platform_types.h"', file=self.outFile)
        write('#include "format/pnext_node.h"', file=self.outFile)
        write('#include "format/pnext_null_node.h"', file=self.outFile)
        write('#include "format/pnext_typed_node.h"', file=self.outFile)
        write('#include "format/trace_pnext_util.h"', file=self.outFile)
        self.newline()
        write('BRIMSTONE_BEGIN_NAMESPACE(brimstone)', file=self.outFile)
        write('BRIMSTONE_BEGIN_NAMESPACE(format)', file=self.outFile)
        self.newline()
        write('size_t decode_pnext_struct(const uint8_t* parameter_buffer, size_t buffer_size,  std::unique_ptr<PNextNode>* pNext)', file=self.outFile)
        write('{', file=self.outFile)
        write('    assert(pNext != nullptr);', file=self.outFile)
        self.newline()
        write('    size_t bytes_read = 0;', file=self.outFile)
        write('    uint32_t attrib = 0;', file=self.outFile)
        self.newline()
        write('    if ((parameter_buffer != nullptr) && (buffer_size >= sizeof(attrib)))', file=self.outFile)
        write('    {', file=self.outFile)
        write('        size_t stype_offset = 0;', file=self.outFile)
        self.newline()
        write('        // Peek at the pointer attribute mask to make sure we have a non-NULL value that can be decoded.', file=self.outFile)
        write('        attrib = *(reinterpret_cast<const uint32_t*>(parameter_buffer));', file=self.outFile)
        self.newline()
        write('        if ((attrib & PointerAttributes::kIsNull) != PointerAttributes::kIsNull)', file=self.outFile)
        write('        {', file=self.outFile)
        write('            // Offset to VkStructureType, after the pointer encoding preamble.', file=self.outFile)
        write('            stype_offset = sizeof(attrib);', file=self.outFile)
        self.newline()
        write('            if ((attrib & PointerAttributes::kHasAddress) == PointerAttributes::kHasAddress)', file=self.outFile)
        write('            {', file=self.outFile)
        write('                stype_offset += sizeof(AddressEncodeType);', file=self.outFile)
        write('            }', file=self.outFile)
        write('        }', file=self.outFile)
        self.newline()
        write('        if ((stype_offset != 0) && ((buffer_size - stype_offset) >= sizeof(VkStructureType)))', file=self.outFile)
        write('        {', file=self.outFile)
        write('            const VkStructureType* sType = reinterpret_cast<const VkStructureType*>(parameter_buffer + stype_offset);', file=self.outFile)
        self.newline()
        write('            switch (*sType)', file=self.outFile)
        write('            {', file=self.outFile)
        write('            default:', file=self.outFile)
        write('                // TODO: Report or raise fatal error for unrecongized sType?', file=self.outFile)
        write('                break;', file=self.outFile)

    # Method override
    def endFile(self):
        write('            }', file=self.outFile)
        write('        }', file=self.outFile)
        write('    }', file=self.outFile)
        self.newline()
        write('    if (bytes_read == 0)', file=self.outFile)
        write('    {', file=self.outFile)
        write('        // The buffer was too small, the encoded pointer attribute mask included kIsNull, or the sType was unrecognized.', file=self.outFile)
        write('        // We will report that we read the attribute mask and return a PNextNullNode.', file=self.outFile)
        write('        if (attrib != 0)', file=self.outFile)
        write('        {', file=self.outFile)
        write('            bytes_read = sizeof(attrib);', file=self.outFile)
        write('        }', file=self.outFile)
        self.newline()
        write('        (*pNext) = std::make_unique<PNextNullNode>();', file=self.outFile)
        write('    }', file=self.outFile)
        self.newline()
        write('    return bytes_read;', file=self.outFile)
        write('}', file=self.outFile)
        self.newline()
        write('BRIMSTONE_END_NAMESPACE(format)', file=self.outFile)
        write('BRIMSTONE_END_NAMESPACE(brimstone)', file=self.outFile)

        # Finish processing in superclass
        BaseGenerator.endFile(self)

    # Method override
    def genStruct(self, typeinfo, typename, alias):
        if not alias:
            # Only process struct types that specify a 'structextends' tag, which indicates the struct can be used in a pNext chain.
            parentStructs = typeinfo.elem.get('structextends')
            if parentStructs:
                sType = self.makeStructureTypeEnum(typeinfo, typename)
                if sType:
                    self.sTypeValues[typename] = sType

    #
    # Indicates that the current feature has C++ code to generate.
    def needFeatureGeneration(self):
        if self.sTypeValues:
            return True
        return False

    #
    # Performs C++ code generation for the feature.
    def generateFeature(self):
        for struct in self.sTypeValues:
            write('            case {}:'.format(self.sTypeValues[struct]), file=self.outFile)
            write('                (*pNext) = std::make_unique<PNextTypedNode<Decoded_{}>>();'.format(struct), file=self.outFile)
            write('                bytes_read = (*pNext)->Decode(parameter_buffer, buffer_size);'.format(struct), file=self.outFile)
            write('                break;', file=self.outFile)
        self.sTypeValues = dict()
