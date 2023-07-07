# sl0ppy-domainbrute
sl0ppy-SDSDBrute a Python3 based brute forcer for subdomains and subdirectories. 

# Usage
`python sl0ppy-sdsdbrute.py -d example.com -min 1 -max 4 -num 2 -s -c 4 -m`

Run the script with the desired command-line arguments. Here are the available options:

    -d or --target_domain: Specify the target domain to brute force.
    -min or --min_length: Set the minimum length of subdomains (default is 1).
    -max or --max_length: Set the maximum length of subdomains (default is 3).
    -num or --num_answers: Set the number of DNS answers to check (default is 1).
    -s or --enable_subdir: Enable brute forcing of subdirectories.
    -c or --cpu_count: Set the number of CPU cores to use (default is 1).
    -m or --enable_multithread: Enable multithreading.

This command will brute force subdomains and subdirectories for the domain example.com, with subdomains ranging from length 1 to 4. It will check 2 DNS answers per subdomain, use 4 CPU cores, and enable multithreading.

The script will start brute forcing the domains and display a progress bar. It will output the found subdomains and subdirectories once the process is complete.
