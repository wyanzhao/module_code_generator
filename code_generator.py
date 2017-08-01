#!/usr/bin/python3

import json
import sys
import os
import datetime


def create_posthandler(params):
    "Used to generate post handler function"
    _params = "static void handler_post (struct kprobe *p, struct pt_regs *regs,\n unsigned long flags)\n"
    _stack_size = 8
    _code = "{\n"
    _code += "char *sp_regs = NULL;\n"
    for i in range (len (params)):
        _code += "sp_regs=(char *)regs->sp + %d;\n" % (_stack_size)
        _code += "pr_info(\"<%s> esp addr: 0x%lx, value:0x%lx\\n\",\n\
        p->symbol_name, sp_regs, *(unsigned int *)sp_regs);\n"
        _stack_size += 4
    _code += "\n}\n\n"
    return _params + _code

def code_generator(data):
    "#Used to generate module code"
    _head_file = "#include <linux/kernel.h>\n#include <linux/module.h>\n#include <linux/kprobes.h>\n\n"
    _marco = "#define MAX_SYMBOL_LEN 64\n"
    _symbol_string = "static char symbol[MAX_SYMBOL_LEN] = \"{}\";\nmodule_param_string(symbol, symbol, sizeof(symbol),0644);\n\n".format (data["function_name"])
    _struct = "static struct kprobe kp = {\n.symbol_name = symbol,\n};\n\n"
    _post = create_posthandler (data["params"])
    _main = "static int __init kprobe_init(void)\n\
    {\n\
    int ret;\n\
    kp.post_handler = handler_post;\n\
    ret = register_kprobe(&kp);\n\
    if (ret < 0) {\n\
        pr_err(\"register_kprobe failed, returned %lx\\n\", ret);\n\
        return ret;\n\
    }\n\
    pr_info(\"Planted kprobe at %p\\n\", kp.addr);\n\
    return 0;\n\
    }\n\n"
    _exit = "static void __exit kprobe_exit(void)\n\
    {\n\
    unregister_kprobe(&kp);\n\
    pr_info(\"kprobe at %p unregistered\\n\", kp.addr);\n\
    }\n\n\n"
    _module = "module_init(kprobe_init)\n\
    module_exit(kprobe_exit)\n\
    MODULE_LICENSE(\"GPL\");\n"
    return _head_file + _marco + _symbol_string + _struct + _post + _main + _exit + _module

def generate_makefile ():
    "To generate makefile"
    tmp_str = ""
    tmp_str += "all:\n"
    tmp_str += "\tmake -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules\n\n"
    tmp_str += "clean:\n"
    tmp_str += "\tmake -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules\n\n"
    return tmp_str

def add_makefile_head(module_name=str):
    "adding file_file_head"
    return "obj-m += {}\n".format (module_name)

def main():
    "import config from files"
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if not os.path.exists (current_time):
        os.makedirs (current_time)
    else:
        raise Exception ("Current Folder exists")

    latest_folder = "latest"
    if os.path.exists (latest_folder):
        os.remove (latest_folder)
    os.symlink (current_time, latest_folder)

    if len (sys.argv) == 1:
        configure_file = "configure.json"
    else:
        configure_file = sys.argv[1]
    with open("{}".format(configure_file), "r") as f:
        config_data = json.load(f)
    make_str = ""

    for i in config_data:
        code_str = str(code_generator(i))
        with open("./{}/{}.c".format(current_time,i["function_name"]), "w") as f:
            f.write(code_str)
        make_str += add_makefile_head("{}.o".format(i["function_name"]))

    make_str += generate_makefile()
    with open("./{}/Makefile".format (current_time), "w") as f:
        f.write(make_str)

if __name__ == "__main__":
    main()
