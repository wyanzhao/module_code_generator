#include <iostream>
#include <sys/epoll.h>

int main ()
{
    epoll_ctl (0x66, 0x377, 0x323, NULL);

    return 0;   
}
