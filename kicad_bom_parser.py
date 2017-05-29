#!/usr/bin/env python

from xml.dom import minidom

class BOMparser():
    def __init__(self, filepath):
        self.filepath = filepath
        self.xmldoc = minidom.parse(filepath)
        self.components = self.xmldoc.getElementsByTagName('components')[0]
        self.components = self.components.getElementsByTagName('comp')
        
    def get_part_info(self,reference,paramName):
        for comp in self.components:
            if comp.attributes['ref'].value == reference:
                fields = comp.getElementsByTagName('fields')[0]
                fields = fields.getElementsByTagName('field')
                for field in fields:
                    if field.attributes['name'].value == paramName:
                        return {"value":field.firstChild.nodeValue}
                
                
                
        return {"value":""}
            
if __name__ == '__main__':
    parser = BOMparser("/home/arne/programming/projekte/windrad/kicad/revB/windrad.xml")
    print(parser.get_part_info("D501"))