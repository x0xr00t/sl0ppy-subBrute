# sl0ppy-SubBrute
sl0ppy-subBrute a Python3 based brute forcer for subdomains and subdirectories. 

# GPU Support
* `AMD`
* `NVIDIA`

# gpu check
* `It has a automated gpu check function`
 
# legacy cpu check
* `A auto checks for legacy cpu up to 4core are seen as legacy, newer with 6 or more cores would be considered new.`

# optimizations
```
    Asynchronous DNS Resolution: The script uses asynchronous DNS resolution using the aiohttp library. This allows multiple DNS queries to be made simultaneously, reducing the overall time taken for the brute-forcing process.

    DNS Cache: The script maintains a DNS cache to store resolved domains, preventing redundant DNS queries for the same domain.

    Multithreading: The script provides an option to enable multithreading (-m or --enable-multithread). When enabled, it utilizes multiple worker threads to perform subdomain brute-forcing, further speeding up the process.

    Progress Bar: The script uses the tqdm library to display a progress bar, giving real-time updates on the progress of the brute-forcing process.

    Memory Monitoring: A separate thread is used to monitor memory usage. If memory usage exceeds a certain threshold, the script will pause for a short duration to prevent excessive memory consumption.

    Optimization of Subdomain and Subdirectory Generation: The script generates subdomains and subdirectories using iterators and generators, which reduces memory usage and improves performance.

    DNS Query Optimization: The script has been optimized to query for AAAA records as well, in addition to A records, to handle IPv6 addresses.
```  
# Lightweight 
* optimized it so its lightweight, can run whilst other processes run, like youtube in backgrond without exhausting the memory.

# Usage
`python sl0ppy-SubBrute.p -d example.com -min 1 -max 4 -num 2 -s -c 4 -m`

# Options
Run the script with the desired options. Here are the available command-line options:

```
usage: sl0ppy-SubBrute.py [-h] -d TARGET_DOMAIN [-min SUBDOMAIN_MIN_LENGTH] [-max SUBDOMAIN_MAX_LENGTH] [-n NUM_ANSWERS] [--subdir] [--subdir-format SUBDIR_FORMAT] [--subdom] [--subdom-format SUBDOM_FORMAT] [-m] [-t NUM_THREADS]

sl0ppy-SubBrute.p

optional arguments:
-d, --target-domain  : Target domain to brute-force (required)
-min, --subdomain-min-length : Minimum subdomain length (default: 1)
-max, --subdomain-max-length : Maximum subdomain length (default: 3)
-n, --num-answers : Number of answers to resolve (default: 1)
--subdir : Enable subdirectory brute-forcing (default: False)
--subdom : Enable subdomain brute-forcing (default: False)
-m, --enable-multithread : Enable multithreaded execution (default: False)
-t, --num-threads : Number of worker threads for multithreading (default: 2)
```

For example, to run the script with the target domain example.com and enable multithreading with 4 threads, you can use the following command:

`python sl0ppy-SubBrute.py -d example.com -m -t 4`

The script will start brute-forcing the subdomains and subdirectories and print the found results in real-time. Please note that the execution time will vary depending on the complexity of the target domain and the specified options.
