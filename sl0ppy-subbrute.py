#!/usr/bin/env python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-subBrute

import argparse
import asyncio
import concurrent.futures
import dns.exception
import dns.resolver
import itertools
import os
import psutil
import urllib3
import string
import threading
from urllib.parse import urlparse
from colorama import Fore, Style, init
from tqdm import tqdm

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

def validate_subdomain(target):
    http = urllib3.PoolManager()
    response = http.request('HEAD', target)
    return response.status == 200

def resolve_domain(target, num_answers, pbar, found_domains, found_pages):
    try:
        answers = 'A' * num_answers
        for answer in answers:
            # Perform testing here and update the progress bar description accordingly
            pbar.set_description(f'Testing: {target}')
            pbar.update(1)

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
            found_domains.add(target)

def brute_force_subdirs(domain, subdir_format, found_pages):
    characters = string.ascii_letters + string.digits + string.punctuation

    with tqdm(total=len(characters), unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
        for char in characters:
            target = construct_url(domain, f"{subdir_format}{char}")
            if target not in found_pages and validate_subdomain(target):
                print(target)
                found_pages.add(target)

def construct_url(domain, subdirectory=None):
    if subdirectory:
        target = f"https://{domain}/{subdirectory}"
    else:
        target = f"https://{domain}"

    return target

def brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    characters = string.ascii_letters + string.digits + string.punctuation
    found_domains = set()
    found_pages = set()

    total_combinations = 0
    for length in range(subdomain_min_length, subdomain_max_length + 1):
        total_combinations += len(characters) ** length

    if enable_multithread:
        cpu_cores = psutil.cpu_count(logical=False)
        max_threads = max(cpu_cores - 1, 1)
        worker_threads = min(cpu_cores, max_threads, num_threads)

        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_threads) as executor:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = []

            for length in range(subdomain_min_length, subdomain_max_length + 1):
                for combination in itertools.product(characters, repeat=length):
                    subdomain = ''.join(combination)
                    target = construct_url(f"{subdomain}.{target_domain}")

                    if target is None:
                        continue

                    try:
                        tasks.append(loop.run_in_executor(executor, resolve_domain, target, num_answers, tqdm(total=total_combinations, unit='combination', ncols=80,
                                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'), found_domains, found_pages))
                    except ValueError:
                        pass

            loop.run_until_complete(asyncio.gather(*tasks))
            loop.close()

    else:
        with tqdm(total=total_combinations, unit='combination', ncols=80,
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
            for length in range(subdomain_min_length, subdomain_max_length + 1):
                for combination in itertools.product(characters, repeat=length):
                    subdomain = ''.join(combination)
                    target = construct_url(f"{subdomain}.{target_domain}")

                    if target is None:
                        continue

                    resolve_domain(target, num_answers, pbar, found_domains, found_pages)

    if enable_subdir:
        print("\n# Found subdirectories:")
        brute_force_subdirs(target_domain, subdir_format, found_pages)

    print("\n# Found subdomains:")
    for domain in found_domains:
        print(domain)

    print("\n# Found pages:")
    for page in found_pages:
        print(page)

def main(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    print_banner()
    print("Brute forcing in progress...")

    brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers,
                        enable_subdir, subdir_format, enable_multithread, num_threads)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Domain brute-forcing script')
    parser.add_argument('-d', dest='target_domain', required=True, help='Target domain')
    parser.add_argument('-min', dest='subdomain_min_length', type=int, default=1, help='Minimum subdomain length')
    parser.add_argument('-max', dest='subdomain_max_length', type=int, default=3, help='Maximum subdomain length')
    parser.add_argument('-n', dest='num_answers', type=int, default=1, help='Number of answers to resolve')
    parser.add_argument('-subdir', dest='enable_subdir', action='store_true', help='Enable subdirectory brute-forcing')
    parser.add_argument('-subdom', dest='subdir_format', default="brute-force", help='Subdirectory format when -subdir is enabled')
    parser.add_argument('-m', dest='enable_multithread', action='store_true', help='Enable multithreaded execution')
    parser.add_argument('-t', dest='num_threads', type=int, default=2, help='Number of worker threads for multithreading')

    args = parser.parse_args()

    main(args.target_domain, args.subdomain_min_length, args.subdomain_max_length, args.num_answers,
         args.enable_subdir, args.subdir_format, args.enable_multithread, args.num_threads)
