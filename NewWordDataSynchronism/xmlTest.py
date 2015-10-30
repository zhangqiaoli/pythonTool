#!/usr/bin/python
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
    
tree = ET.parse('country_data.xml')
root = tree.getroot()    
#root = ET.fromstring(country_data_as_string)
for child in root:
    for node in child:
        print(node.text,node.attrib)
    print child.tag, child.attrib['name']
for neighbor in root.iter('neighbor'):
    print neighbor.attrib
for country in root.findall('country'):
    rank = country.find('rank').text
    name = country.get('name')
    print name, rank