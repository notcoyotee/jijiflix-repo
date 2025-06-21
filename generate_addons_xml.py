import os
import hashlib
import xml.etree.ElementTree as ET

def generate_addons_xml(addon_dir):
    addons = []
    for addon in os.listdir(addon_dir):
        addon_path = os.path.join(addon_dir, addon)
        if os.path.isdir(addon_path):
            addon_xml = os.path.join(addon_path, 'addon.xml')
            if os.path.exists(addon_xml):
                tree = ET.parse(addon_xml)
                root = tree.getroot()
                if root.tag == 'addon':
                    addons.append(ET.tostring(root, encoding='unicode'))

    addons_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n{"".join(addons)}</addons>'
    
    # Generate MD5
    md5 = hashlib.md5(addons_xml.encode('utf-8')).hexdigest()
    
    return addons_xml, md5

if __name__ == '__main__':
    addons_xml, md5 = generate_addons_xml('.')
    with open('addons.xml', 'w') as f:
        f.write(addons_xml)
    with open('addons.xml.md5', 'w') as f:
        f.write(md5)
