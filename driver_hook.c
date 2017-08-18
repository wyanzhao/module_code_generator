 #include <linux/module.h>	/* Needed by all modules */
 #include <linux/kernel.h>	/* Needed for KERN_INFO */
 #include <linux/if.h>
 void (* fun_ptr)(char *a, int b) = NULL;

 int init_module(void)
 {
     printk(KERN_INFO "Hello world 1.\n");

     fun_ptr = 0xf847ac10;
     fun_ptr (0xf3397000, 1000);
     /* 
      * A non 0 return means init_module failed; module can't be loaded. 
      */
     return 0;
 }
 
 void cleanup_module(void)
 {
     printk(KERN_INFO "Goodbye.\n");
 }
