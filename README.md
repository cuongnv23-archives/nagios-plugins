### Nagios plugins
List of my custom nagios+nrpe plugins

#### check_mem.py

This plugin calculates the free memory of system.
Since kernel 3.14, there is a value 'MemAvailable' which estimates
the allocatable memory without swapping. 
See [this commit](https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/commit/fs/proc/meminfo.c?id=34e431b0ae398fc54ea69ff85ec700722c9da773)

This estimates freeable memory based on 'MemAvailable' value
Also support for old kernel.

Sample configuration:
- On remote host
```
command[check_mem]=/usr/lib64/nagios/plugins/check_mem.py -w 80 -c 40
```
- On nagios host
```
define command{
    command_name check_nrpe
    command_line $USER1$/check_nrpe -H $HOSTADDRESS$ -c $ARG1$
}

define service{
    use                             local-service
    host_name                       remote-host
    service_description             Free Memory
    check_command                   check_nrpe!check_mem
}
```

Sample expected output:
```
# /usr/lib64/nagios/plugins/check_nrpe -H remote_ip -c check_mem
WARNING - 74% Free (742M/996M)
```


### License
MIT
