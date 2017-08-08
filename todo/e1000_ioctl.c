#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/kallsyms.h>

#define MAX_SYMBOL_LEN 64
static char symbol[MAX_SYMBOL_LEN] = "e1000_ioctl";
module_param_string(symbol, symbol,    sizeof(symbol),0644);

static void (*crete_capture_begin)(void);
static void (*crete_capture_end)(void);
static void (*crete_make_concolic)(void*, size_t, const char*);

static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    crete_capture_begin();

    char *sp_regs = kernel_stack_pointer (regs);

    // TODO: XXX

// 1. Argument pass by stack example:
//    size_t arg1_addr = sp_regs + 4;
//    size_t arg2_addr = sp_regs + 8;
//    size_t arg3_addr = sp_regs + 12;
//    size_t arg3_size = 4;
//    crete_make_conoclic(arg3_addr, arg3_size, "crete_probe_arg3");

// 2. Argument pass by register:
    crete_make_concolic(&regs->cx, sizeof(regs->cx), "crete_probe_cx");

    return 0;
}

static int ret_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    crete_capture_end();

    return 0;
}

static int init_crete_intrinics(void)
{
    int ret;

    printk(KERN_INFO "[crete] init_crete_intrinics()\n");

    crete_capture_begin =  kallsyms_lookup_name("crete_capture_begin");
    crete_capture_end =  kallsyms_lookup_name("crete_capture_end");
    crete_make_concolic =  kallsyms_lookup_name("crete_make_concolic");

    if (crete_capture_begin &&
        crete_capture_end &&
        crete_make_concolic)
    {
        ret = 0;
        printk(KERN_INFO "[crete] all functions found\n");
    } else {
        ret = 1;
        printk(KERN_INFO "[crete] not all function found, please check crete-intrinsics.ko\n");
    }

    return ret;
}

static struct kretprobe kretp = {
        .handler        = ret_handler,
        .entry_handler      = entry_handler,
};


static int __init kprobe_init(void)
{
    int ret;

    kretp.kp.symbol_name = symbol;
    ret = register_kretprobe(&kretp);
    if (ret < 0) {
        printk(KERN_INFO "register_kretprobe failed, returned %d\n",
                ret);
        return -1;
    }
    printk(KERN_INFO "Planted return probe at %s: %p\n",
            kretp.kp.symbol_name, kretp.kp.addr);

    init_crete_intrinics();
    return 0;
}

static void __exit kprobe_exit(void)
{
    unregister_kretprobe(&kretp);
    printk(KERN_INFO "kretprobe at %p unregistered\n",
            kretp.kp.addr);

    /* nmissed > 0 suggests that maxactive was set too low. */
    printk(KERN_INFO "Missed probing %d instances of %s\n",
        kretp.nmissed, kretp.kp.symbol_name);
}

module_init(kprobe_init)
module_exit(kprobe_exit)
MODULE_LICENSE("GPL");
