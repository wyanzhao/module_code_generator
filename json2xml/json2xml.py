#!/usr/bin/python3
"This module is used to generate xml file readed by crete"
import subprocess
import sys

def json2xml(json_str=list):
    "Convert json format to xml"
    xml_str = ""
    xml_str += "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    xml_str += "<crete>\n"
    cmd_path = subprocess.check_output (["whereis", "-b", json_str[0]])
    cmd_path = cmd_path.decode ("utf-8")
    cmd_path = cmd_path.split(" ")[-1].strip("\n")

    xml_str += "<exec>{}</exec>\n".format(cmd_path)
    xml_str += "<args>\n"
    for i in range(1, len(json_str)):
        xml_str += "<arg index=\"%d\" value=\"%s\"/>\n" % (i, json_str[i])
    xml_str += "</args>\n"
    xml_str += "</crete>\n"

    return xml_str

if __name__ == "__main__":
    print (json2xml(["ifconfig", "eth0"]))