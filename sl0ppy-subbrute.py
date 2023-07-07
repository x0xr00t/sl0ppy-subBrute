#!/usr/bin/env python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-DomainBrute

#!/usr/bin/env python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-DomainBrute

import argparse
import asyncio
import concurrent.futures
import dns.exception
import dns.resolver
import itertools
import psutil
import string
import threading
from colorama import Fore, Style, init
from tqdm import tqdm
from urllib.parse import urljoin

def print_banner():
    init(autoreset=True)
    banner = """
           /$$  /$$$$$$                                            
          | $$ /$$$_  $$                                                  
  /$$$$$$$| $$| $$$$\ $$  /$$$$$$   /$$$$$$  /$$   /$$       
 /$$_____/| $$| $$ $$ $$ /$$__  $$ /$$__  $$| $$  | $$ /$$$$$$
|  $$$$$$ | $$| $$\ $$$$| $$  \ $$| $$  \ $$| $$  | $$|______/
 \____  $$| $$| $$ \ $$$| $$  | $$| $$  | $$| $$  | $$        
 /$$$$$$$/| $$|  $$$$$$/| $$$$$$$/|  $$$$$$$|  $$$$$$$        
|_______/ |__/ \______/ | $$____/ | $$____/  \____  $$        
                        | $$      | $$       /$$  | $$                                                          
                        | $$      | $$      |  $$$$$$/                                                          
                        |__/      |__/       \______/                                                           
                     /$$          /$$$$$$$                        /$$                        
                    | $$         | $$__  $$                      | $$                        
  /$$$$$$$ /$$   /$$| $$$$$$$    | $$  \ $$  /$$$$$$  /$$   /$$ /$$$$$$    /$$$$$$  
 /$$_____/| $$  | $$| $$__  $$   | $$$$$$$  /$$__  $$| $$  | $$|_  $$_/   /$$__  $$ 
|  $$$$$$ | $$  | $$| $$  \ $$   | $$__  $$| $$  \__/| $$  | $$  | $$    | $$$$$$$$
 \____  $$| $$  | $$| $$  | $$   | $$  \ $$| $$      | $$  | $$  | $$ /$$| $$_____/  
 /$$$$$$$/|  $$$$$$/| $$$$$$$/   | $$$$$$$/| $$      |  $$$$$$/  |  $$$$/|  $$$$$$$     
|_______/  \______/ |_______/    |_______/ |__/       \______/    \___/   \_______/ 
    """

    color_order = [Fore.RED, Fore.YELLOW]
    colored_banner = ""
    line_num = 0

    for line in banner.splitlines():
        color = color_order[line_num % len(color_order)]
        colored_line = f"{color}{line}"
        colored_banner += colored_line + "\n"
        line_num += 1

    print(colored_banner)
    print(Style.RESET_ALL)


def brute_force_domains(domain, min_length, max_length, num_answers, enable_subdir, cpu_count, enable_multithread):
    characters = string.ascii_letters + string.digits + string.punctuation
    found_domains = []
    found_subdirs = []

    total_combinations = 0
    for length in range(min_length, max_length + 1):
        total_combinations += len(characters) ** length

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        if enable_subdir:
            subdir_thread = threading.Thread(target=brute_force_subdirs, args=(domain,))
            subdir_thread.start()

        if enable_multithread:
            worker_threads = min(cpu_count, psutil.cpu_count()) * 0.7
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_threads)
            loop = asyncio.get_event_loop()
            tasks = []

            for length in range(min_length, max_length + 1):
                for combination in itertools.product(characters, repeat=length):
                    subdomain = ''.join(combination)
                    if enable_subdir:
                        target = urljoin(f"https://{domain}/", subdomain)
                    else:
                        target = subdomain + '.' + domain
                    tasks.append(loop.run_in_executor(executor, resolve_domain, target, num_answers, pbar, found_domains))

            loop.run_until_complete(asyncio.gather(*tasks))
            loop.close()

        else:
            for length in range(min_length, max_length + 1):
                for combination in itertools.product(characters, repeat=length):
                    subdomain = ''.join(combination)
                    if enable_subdir:
                        target = urljoin(f"https://{domain}/", subdomain)
                    else:
                        target = subdomain + '.' + domain
                    resolve_domain(target, num_answers, pbar, found_domains)

        if enable_subdir:
            subdir_thread.join()

    return found_domains, found_subdirs


def resolve_domain(target, num_answers, pbar, found_domains):
    try:
        # Check if the target is an IPv6 address
        if target.startswith("[") and target.endswith("]"):
            target = target[1:-1]  # Remove the square brackets

        answers = 'A' * num_answers
        for answer in answers:
            # Perform testing here and update the progress bar description accordingly
            pbar.set_description(f'Testing: {target} ({answer})')
            pbar.update(1)
            pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NoNameservers:
        pass
    except dns.exception.Timeout:
        pass
    else:
        if answer == 'A':
            found_domains.append(target)


def brute_force_subdirs(domain):
    # Perform subdirectory brute force here
    pass


def main(target_domain, min_length, max_length, num_answers, enable_subdir, cpu_count, enable_multithread):
    print_banner()
    print("Brute forcing in progress...")
    found_domains, found_subdirs = brute_force_domains(target_domain, min_length, max_length, num_answers,
                                                       enable_subdir, cpu_count, enable_multithread)

    print("\nFound subdomains:")
    for domain in found_domains:
        print(domain)

    print("\nFound subdirectories:")
    for subdir in found_subdirs:
        print(subdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Domain brute-forcing script')
    parser.add_argument('-d', dest='target_domain', help='target domain to brute force')
    parser.add_argument('-min', dest='min_length', type=int, default=1, help='minimum length of subdomains')
    parser.add_argument('-max', dest='max_length', type=int, default=3, help='maximum length of subdomains')
    parser.add_argument('-num', dest='num_answers', type=int, default=1, help='number of DNS answers to check')
    parser.add_argument('-s', dest='enable_subdir', action='store_true', help='enable brute forcing of subdirectories')
    parser.add_argument('-c', dest='cpu_count', type=int, default=1, help='number of CPU cores to use')
    parser.add_argument('-m', dest='enable_multithread', action='store_true', help='enable multithreading')

    args = parser.parse_args()

    main(args.target_domain, args.min_length, args.max_length, args.num_answers, args.enable_subdir, args.cpu_count,
         args.enable_multithread)
