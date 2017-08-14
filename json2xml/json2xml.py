#!/usr/bin/python3
"This module is used to generate xml file readed by crete"
import subprocess

def json2xml(workload_str=str, setup_list=list,
    function_name=str, full_path=str):
    "Convert json format to xml"
    json_list = list(workload_str.split(" "))
    xml_str = ""
    xml_str += "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    xml_str += "<crete>\n"
    cmd_path = subprocess.check_output(["whereis", "-b", json_list[0]])
    cmd_path = cmd_path.decode("utf-8")
    cmd_path = cmd_path.split(" ")[-1].strip("\n")

    xml_str += "<exec>{}</exec>\n".format(cmd_path)
    xml_str += "<args>\n"
    for i in range(1, len(json_list)):
        xml_str += "<arg index=\"%d\" value=\"%s\"/>\n" % (i, json_list[i])
    xml_str += "</args>\n"
    xml_str += "<setup_commands>\n"
    for i in enumerate(setup_list):
        xml_str += "<setup_command>{}</setup_command>\n".format(i[1])
    xml_str += "</setup_commands>\n"
    xml_str += "<kprobe_module>{}/{}.ko</kprobe_module>\n".format(full_path, function_name)
    xml_str += "</crete>\n"
    return xml_str

if __name__ == "__main__":
    print (json2xml("ifconfig eth0 eth1", ["vcibfug 473hd ds", "cmd fudssdndcia"], function_name="Hello", full_path="~/home/kernel"),)