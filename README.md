# sl0ppy-SubBrute
sl0ppy-subBrute a Python3 based brute forcer for subdomains and subdirectories. 

# Usage
`python sl0ppy-subbrute.py -d example.com -min 1 -max 4 -num 2 -s -c 4 -m`

# Options
Run the script with the desired options. Here are the available command-line options:

```
usage: sl0ppy-SubBrute.py [-h] -d TARGET_DOMAIN [-min SUBDOMAIN_MIN_LENGTH]
                       [-max SUBDOMAIN_MAX_LENGTH] [-n NUM_ANSWERS]
                       [-subdir] [-subdom SUBDIR_FORMAT] [-m] [-t NUM_THREADS]

optional arguments:
  -h, --help            show this help message and exit
  -d TARGET_DOMAIN, --target_domain TARGET_DOMAIN
                        Target domain
  -min SUBDOMAIN_MIN_LENGTH, --subdomain_min_length SUBDOMAIN_MIN_LENGTH
                        Minimum subdomain length
  -max SUBDOMAIN_MAX_LENGTH, --subdomain_max_length SUBDOMAIN_MAX_LENGTH
                        Maximum subdomain length
  -n NUM_ANSWERS, --num_answers NUM_ANSWERS
                        Number of answers to resolve
  -subdir, --enable_subdir
                        Enable subdirectory brute-forcing
  -subdom SUBDIR_FORMAT, --subdom_format SUBDOM_FORMAT
                        Subdomain format when -subdom is enabled
  -m, --enable_multithread
                        Enable multithreaded execution
  -t NUM_THREADS, --num_threads NUM_THREADS
                        Number of worker threads for multithreading
```

For example, to run the script with the target domain example.com and enable multithreading with 4 threads, you can use the following command:

`python sl0ppy-brute.py -d example.com -m -t 4`

The script will start brute-forcing the subdomains and subdirectories and print the found results in real-time. Please note that the execution time will vary depending on the complexity of the target domain and the specified options.
