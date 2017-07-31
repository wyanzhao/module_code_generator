import json


class PostHandler(object):
    def __init__ (self, params):
            self._params = "static void handler_post (struct kprobe *p, struct pt_regs *regs,\n unsigned long flags)\n"
            stack_size = 8;
            self._code = "{\n"
            self._code += "char *sp_regs = NULL;\n"
            for i in range (len (params)):
                self._code += "sp_regs=(char *)regs->sp + %d;\n" % (stack_size)
                self._code += "pr_info(\"<%s> esp addr: 0x%lx, value:0x%lx\\n\",\n\
                p->symbol_name, sp_regs, *(unsigned int *)sp_regs);\n"
                stack_size += 4
            self._code += "\n}\n\n"

    def __str__ (self):
            return self._params + self._code


#Used to generate module code
class CodeGenerator(object):
    def __init__(self, data):
        self._head_file = "#include <linux/kernel.h>\n#include <linux/module.h>\n#include <linux/kprobes.h>\n\n"
        self._marco = "#define MAX_SYMBOL_LEN 64\n"
        self._symbol_string = "static char symbol[MAX_SYMBOL_LEN] = \"{}\";\nmodule_param_string(symbol, symbol, sizeof(symbol),0644);\n\n".format (data["function_name"])
        self._struct = "static struct kprobe kp = {\n.symbol_name = symbol,\n};\n\n"
        self._post = PostHandler (data["params"])
        self._main = "static int __init kprobe_init(void)\n\
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
        self._exit = "static void __exit kprobe_exit(void)\n\
        {\n\
        unregister_kprobe(&kp);\n\
        pr_info(\"kprobe at %p unregistered\\n\", kp.addr);\n\
        }\n\n\n"
        self._module = "module_init(kprobe_init)\n\
        module_exit(kprobe_exit)\n\
        MODULE_LICENSE(\"GPL\");\n"
        
  
    def __str__(self):
        return self._head_file + self._marco + self._symbol_string + self._struct + str(self._post) + self._main + self._exit + self._module

def generate_makefile ():
    tmp_str = ""
    tmp_str += "all:\n"
    tmp_str += "\tmake -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules\n\n"
    tmp_str += "clean:\n"
    tmp_str += "\tmake -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules\n\n"
    return tmp_str

def add_makefile_head (module_name = str):
    return "obj-m += {}\n".format (module_name)

def main():
    # import config from files
    with open ("config.json", "r") as f:
        config_data = json.load (f)
    make_str = ""

    for i in config_data:
        code_str = str (CodeGenerator(i))
        with open ("{}.c".format(i["function_name"]), "w") as f:
            f.write (code_str)
        make_str += add_makefile_head ("{}.o".format (i["function_name"]))
        
    make_str += generate_makefile ()
    with open ("Makefile", "w") as f:
        f.write (make_str)

if __name__ == "__main__":
    main()
