#!/usr/bin/python3
"This module is used to generate c code by reading from configure file"

import json
import sys
import os
import datetime
import subprocess
import shutil

from json2xml import json2xml

def get_size(param):
    "Return the size of given parameter"
    if "size" not in param:
        return 4
    else:
        return param["size"]    

def create_stack_entry_handler(params):
    "Used to generate post handler function"
    _code = "static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)\n"
    _code += "{\n"
    _code += "_crete_capture_begin();\n"
    _code += "char *sp_regs = kernel_stack_pointer (regs);\n"

    _stack_size = 4
    for i in range(len(params)):
        if params[i]["concolic"]:
            if "*" in params[i]["type"]:
                _code += "char* arg{}_addr = *(sp_regs + {});\n".format(i + 1, _stack_size)
            else:
                _code += "char* arg{}_addr = sp_regs + {};\n".format(i + 1, _stack_size)
            _code += "size_t arg{}_size = {};\n".format(i + 1, get_size(params[i]))
            _code += "_crete_make_concolic(arg{}_addr, arg{}_size, \"crete_probe_arg{}\");\n".format(i + 1, i + 1, i + 1)
        _stack_size += 4

    _code += "return 0;\n"
    _code += "}\n"
    return _code

def create_register_posthandler(params):
    "Used to generate post handler function"
    _code = "static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)\n"
    _code += "{\n"
    _code += "_crete_capture_begin();\n"
    _code += "char *sp_regs = kernel_stack_pointer (regs);\n"

    _stack_size = 4
    for i in range(len(params)):
        if params[i]["concolic"]:
            if i == 0:
                if "*" in params[i]["type"]:
                    _code += "_crete_make_concolic (regs->ax, sizeof (regs->ax), \"crete_probe_ax\");\n"
                else:
                    _code += "_crete_make_concolic (&regs->ax, sizeof (regs->ax), \"crete_probe_ax\");\n"
            elif i == 1:
                if "*" in params[i]["type"]:
                    _code += "_crete_make_concolic (regs->dx, sizeof (regs->dx), \"crete_probe_dx\");\n"
                else:
                    _code += "_crete_make_concolic (&regs->dx, sizeof (regs->dx), \"crete_probe_dx\");\n"
            elif i == 2:
                if "*" in params[i]["type"]:
                    _code += "_crete_make_concolic (regs->cx, sizeof (regs->cx), \"crete_probe_cx\");\n"
                else:
                    _code += "_crete_make_concolic (&regs->cx, sizeof (regs->cx), \"crete_probe_cx\");\n"
            else:
                if "*" in params[i]["type"]:
                    _code += "char arg{}_addr = *(sp_regs + {});\n".format(i + 1, _stack_size)
                else:
                    _code += "char arg{}_addr = sp_regs + {};\n".format(i + 1, _stack_size)
                _code += "size_t arg{}_size = {};\n".format(i + 1, get_size(params[i]))
                _code += "_crete_make_concolic(arg{}_addr, arg{}_size, \"crete_probe_arg{}\");\n".format(i + 1, i + 1, i + 1)
        if i > 2:
            _stack_size += 4

    _code += "return 0;\n"
    _code += "}\n"
    return _code

def code_generator(data, exception_list):
    "Used to generate module code"
    _head_file = "#include <linux/kernel.h>\n"
    _head_file += "#include <linux/module.h>\n"
    _head_file += "#include <linux/kprobes.h>\n"
    _head_file += ("\n")

    _marco = "#define MAX_SYMBOL_LEN 64\n"

    _symbol_string = "static char symbol[MAX_SYMBOL_LEN] = \"{}\";\n".format (data["function_name"])
    _symbol_string += "module_param_string(symbol, symbol, sizeof(symbol), 0644);\n"

    _crete_announce = "static void (*_crete_capture_begin)(void);\n"
    _crete_announce += "static void (*_crete_capture_end)(void);\n"
    _crete_announce += "static void (*_crete_make_concolic)(void*, size_t, const char *);\n"

    _probe_struct = ""
    _probe_struct += "static struct kretprobe kretp = {\n"
    _probe_struct += ".handler = ret_handler,\n"
    _probe_struct += ".entry_handler = entry_handler,\n"
    _probe_struct += "};\n"

    if data["function_name"] in exception_list:
        _entry_handler = create_stack_entry_handler(data["params"])
    else:
        _entry_handler = create_register_posthandler(data["params"])

    _ret_handler = "static int ret_handler (struct kretprobe_instance *ri, struct pt_regs *regs)\n"
    _ret_handler += "{\n"
    _ret_handler += "_crete_capture_end();\n"
    _ret_handler += "return 0;\n"
    _ret_handler += "}\n"


    _main = "static int __init kprobe_init(void)\n"
    _main += "{\n"
    _main += "int32_t ret = 0;\n"
    _main += "kretp.kp.symbol_name = symbol;\n"
    _main += "ret = register_kretprobe (&kretp);\n"
    _main += "if (ret < 0) {\n"
    _main += "printk(KERN_INFO \"register_kretprobe failed, returned %d\\n\", ret);\n"
    _main += "return -1;\n"
    _main += "}\n"
    _main += "printk(KERN_INFO \"Planted return probe at %s :%p\\n\", kretp.kp.symbol_name, kretp.kp.addr);\n"
    _main += "_crete_capture_begin = kallsyms_lookup_name (\"crete_capture_begin\");\n"
    _main += "_crete_capture_end = kallsyms_lookup_name (\"crete_capture_end\");\n"
    _main += "_crete_make_concolic = kallsyms_lookup_name (\"crete_make_concolic\");\n"
    _main += "if (! (_crete_capture_begin && _crete_capture_end && _crete_make_concolic)) {\n"
    _main += " printk(KERN_INFO \"[crete] not all function found, please check crete-intrinsics.ko\\n\");\n"
    _main += "return -1;\n"
    _main += "}\n"
    _main += "return 0;\n"
    _main += "}\n"

    _exit = "static void __exit kprobe_exit(void)\n"
    _exit += "{\n"
    _exit += "unregister_kretprobe(&kretp);\n"
    _exit += "pr_info(\"kretprobe at %p unregistered\\n\", kretp.kp.addr);\n"
    _exit += "}\n\n\n"

    _module = "module_init(kprobe_init)\n"
    _module += "module_exit(kprobe_exit)\n"
    _module += "MODULE_LICENSE(\"GPL\");\n"

    return _head_file + _marco + _symbol_string + _crete_announce \
    + _entry_handler + _ret_handler + _probe_struct \
    + _main + _exit + _module

def generate_makefile():
    "To generate makefile"
    make_str = ""
    make_str += "my_dir = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))\n"
    make_str += "all:\n"
    make_str += "\tmake -C /lib/modules/$(shell uname -r)/build M=$(my_dir) modules\n\n"
    make_str += "clean:\n"
    make_str += "\trm -rf $(my_dir)/*.ko $(my_dir)/*.o $(my_dir)/*.symvers $(my_dir)/*.order $(my_dir)/.*.cmd $(my_dir)/.tmp*\n\n"
    return make_str

def add_makefile_head(module_name=str):
    "adding file_file_head"
    return "obj-m += {}\n".format(module_name)

def main(current_time):
    "import config from files"
    
    if not os.path.exists(current_time):
        os.makedirs(current_time)
    else:
        os.rmdir (current_time)
        os.makedirs(current_time)

    latest_folder = "latest"
    if not os.path.exists(latest_folder):
        os.symlink(current_time, latest_folder)
    else:
        os.unlink (latest_folder)
        os.symlink(current_time, latest_folder)

    if len(sys.argv) == 1:
        configure_file = "configure.json"
    else:
        configure_file = sys.argv[1]
    with open("{}".format(configure_file), "r") as f:
        config_data = json.load(f)

    with open("exception.json", "r") as f:
        exception_list = json.load(f)

    make_str = ""
    for i in config_data:
        code_str = code_generator(i, exception_list)
        with open("./{}/{}.c".format(current_time, i["function_name"]), "w") as f:
            f.write(code_str)

        xml_str = json2xml.json2xml(i["workload"], i["setup"], function_name = i["function_name"],
        full_path = os.path.dirname(os.path.abspath(__file__)) + "/{}".format(current_time))
        with open("./{}/output.crete.{}.xml".format(current_time, i["function_name"]), "w") as f:
            f.write(xml_str)

        make_str += add_makefile_head("{}.o".format(i["function_name"]))

    make_str += generate_makefile()
    with open("./{}/Makefile".format(current_time), "w") as f:
        f.write(make_str)

if __name__ == "__main__":
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        main(current_time)
    except:
        shutil.rmtree ("{}".format(current_time))
        os.unlink("latest")
        raise
    else:
        subprocess.call(["make", "-f", "./latest/Makefile"])
       