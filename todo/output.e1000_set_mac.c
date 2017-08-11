#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>

#define MAX_SYMBOL_LEN 64
static char symbol[MAX_SYMBOL_LEN] = "e1000_set_mac";
module_param_string(symbol, symbol, sizeof(symbol), 0644);
static void (*_crete_capture_begin)(void);
static void (*_crete_capture_end)(void);
static void (*_crete_make_concolic)(void*, size_t, const char *);
static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
  _crete_capture_begin();
  char *sp_regs = kernel_stack_pointer (regs);
  size_t addr = regs->dx;
  size_t size = 16;
  _crete_make_concolic (addr, size, "crete_probe_p");
  return 0;
}
static int ret_handler (struct kretprobe_instance *ri, struct pt_regs *regs)
{
  _crete_capture_end();
  return 0;
}
static struct kretprobe kretp = {
  .handler = ret_handler,
  .entry_handler = entry_handler,
};
static int __init kprobe_init(void)
{
  int32_t ret = 0;
  kretp.kp.symbol_name = symbol;
  ret = register_kretprobe (&kretp);
  if (ret < 0) {
    printk(KERN_INFO "register_kretprobe failed, returned %d\n", ret);
    return -1;
  }
  printk(KERN_INFO "Planted return probe at %s :%p\n", kretp.kp.symbol_name, kretp.kp.addr);
  _crete_capture_begin = kallsyms_lookup_name ("crete_capture_begin");
  _crete_capture_end = kallsyms_lookup_name ("crete_capture_end");
  _crete_make_concolic = kallsyms_lookup_name ("crete_make_concolic");
  if (! (_crete_capture_begin && _crete_capture_end && _crete_make_concolic)) {
    printk(KERN_INFO "[crete] not all function found, please check crete-intrinsics.ko\n");
    return -1;
  }
  return 0;
}
static void __exit kprobe_exit(void)
{
  unregister_kretprobe(&kretp);
  pr_info("kretprobe at %p unregistered\n", kretp.kp.addr);
}


module_init(kprobe_init)
module_exit(kprobe_exit)
MODULE_LICENSE("GPL");
