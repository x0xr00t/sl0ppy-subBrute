#!/usr/bin/env python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-subBrute

import argparse
import asyncio
import concurrent.futures
import dns.resolver
import itertools
import psutil
import string
import threading
import requests
import urllib3
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
            found_domains.append(target)

async def brute_force_subdirs(domain, found_pages, pool):
    characters = string.ascii_letters + string.digits + string.punctuation
    subdir_format = [''] if domain.endswith('/') else ['', '/']
    target = f"{domain}{subdir_format[0]}"

    try:
        with pool.request('GET', target, retries=urllib3.Retry(1, redirect=3), preload_content=False) as response:
            if response.status == 200:
                found_pages.append(target)
    except urllib3.exceptions.RequestError:
        pass

    with tqdm(total=len(characters) * len(subdir_format), unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:0.02f}% {elapsed}<{remaining}, {rate_fmt}]') as pbar:

        pbar.set_description(f'Testing: {target}')
        pbar.update(1)

async def construct_url(domain, subdirectory=None):
    if subdirectory:
        target = f"https://{domain}{subdirectory}"
    else:
        target = f"https://{domain}"

    return target

def get_total_combinations(target_domain, subdomain_min_length, subdomain_max_length, enable_subdir, subdir_format):
    characters = string.ascii_letters + string.digits
    total_combinations = sum(len(characters) ** length for length in range(subdomain_min_length, subdomain_max_length + 1))

    if enable_subdir:
        total_combinations *= len(subdir_format)

    return total_combinations

async def brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads, pool):
    characters = string.ascii_letters + string.digits
    found_domains = []
    found_pages = []

    total_combinations = get_total_combinations(target_domain, subdomain_min_length, subdomain_max_length, enable_subdir, subdir_format)

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:0.02f}% {elapsed}<{remaining}, {rate_fmt}]') as pbar:

        if enable_subdir:
            subdir_task = asyncio.create_task(brute_force_subdirs(target_domain, found_pages, pool))

        if enable_multithread:
            cpu_cores = psutil.cpu_count(logical=False)
            max_threads = max(cpu_cores - 1, 1)
            num_threads = min(cpu_cores, max_threads, num_threads)

        tasks = []
        for length in range(subdomain_min_length, subdomain_max_length + 1):
            for combination in itertools.product(characters, repeat=length):
                subdomain = ''.join(combination)

                if enable_subdir:
                    target = await construct_url(target_domain, subdir_format[1])
                else:
                    target = await construct_url(f"{subdomain}.{target_domain}")

                if target is None:
                    # Skip invalid URLs (likely IPv6)
                    continue

                tasks.append(resolve_domain(target, num_answers, pbar, found_domains, found_pages))

        await asyncio.gather(*tasks)

        if enable_subdir:
            await subdir_task

    return found_domains, found_pages

def main(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    print_banner()
    pool = urllib3.PoolManager()

    print("Brute forcing in progress...")
    found_domains, found_pages = asyncio.run(brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers,
                                                     enable_subdir, subdir_format, enable_multithread, num_threads, pool))

    print("\n# Found subdirs:")
    for page in found_pages:
        print(f"{page}")

    print("\n# Found subdomains:")
    for domain in found_domains:
        print(f"{domain}")

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

    http = urllib3.PoolManager()

    main(args.target_domain, args.subdomain_min_length, args.subdomain_max_length, args.num_answers,
         args.enable_subdir, args.subdir_format, args.enable_multithread, args.num_threads)
