import os
import xml.etree.ElementTree as ET
import argparse

def update_pom_tag(file_path, tag_name, new_value, append: bool, remove: bool):
	# Check if the environment variable is set
	if not new_value:
		print("Error: The variable is not set.")
		return

	# Parse the pom.xml file
	tree = ET.parse(file_path)
	root = tree.getroot()

	ns = {'xmlns': 'http://maven.apache.org/POM/4.0.0'}
	# Find the tag to update
	tag = root.find(f"xmlns:{tag_name}", ns)
	if tag is None:
		print(f"Error: Tag {tag_name} not found in file.")
		return

	# Update the tag value
	if append:
		tag.text = f"{tag.text}{new_value}"
	elif remove:
		tag.text = tag.text.replace(new_value, "")
	else:
		tag.text = new_value

	ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
	if(hasattr(ET, 'indent')):
		ET.indent(tree)

	# Write the updated XML back to the file
	tree.write(file_path, xml_declaration=True)

	print(f"Value of tag {tag_name} updated to {new_value} in file.")

if __name__ == "__main__":
	# Initialize parser
	parser = argparse.ArgumentParser()

	# Adding optional argument
	parser.add_argument("-p", "--pom_path", help = "POM path location")
	parser.add_argument("-v", "--value", help = "Value to replace")
	parser.add_argument("-t", "--tag", help = "Tag to replace")
	parser.add_argument("-a", "--append", help="Append instead of replace", action='store_true')
	parser.add_argument("-r", "--remove", help="Remove value in tag", action='store_true')

	# Read arguments from command line
	args = parser.parse_args()

	# Call the function to update the tag value
	update_pom_tag(args.pom_path, args.tag, args.value, args.append, args.remove)