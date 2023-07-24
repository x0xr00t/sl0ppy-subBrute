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
import psutil
import string
import threading
import requests
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

            response = requests.get(target)
            if response.status_code == 200:
                found_pages.append(target)

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

def brute_force_subdirs(domain, found_pages, found_subdirs, sdmin, sdmax):
    characters = string.ascii_letters + string.digits + string.punctuation
    total_combinations = len(characters) ** sdmax

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        # Determine the number of worker threads based on the available CPU cores
        cpu_cores = psutil.cpu_count(logical=False)  # Get the number of physical cores
        max_threads = max(cpu_cores - 1, 1)  # Limit the number of threads to physical cores - 1 or at least 1
        worker_threads = min(cpu_cores, max_threads)

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_threads)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []

        for length in range(sdmin, sdmax + 1):
            for combination in itertools.product(characters, repeat=length):
                subdir = ''.join(combination)
                target = construct_url(domain, subdir)  # Append subdir to domain

                # Skip IPv6 URLs
                if not is_ipv4(target):
                    continue

                tasks.append(loop.run_in_executor(executor, check_subdir, target, found_pages, found_subdirs, pbar))

        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

def check_subdir(target, found_pages, found_subdirs, pbar):
    try:
        response = requests.get(target)
        if response.status_code == 200:
            found_pages.append(target)
        elif response.status_code == 403 or response.status_code == 401:
            found_subdirs.append(target)

    except requests.exceptions.RequestException:
        pass

    pbar.update(1)

def construct_url(domain, subdirectory=None):
    if subdirectory:
        target = f"https://{domain}/{subdirectory}"
    else:
        target = f"https://{domain}"

    try:
        # Encode the target URL as bytes to handle both IPv4 and IPv6 URLs
        target = target.encode('utf-8')
    except UnicodeEncodeError:
        return None

    return target

def is_ipv6(url):
    if not url:
        return False

    try:
        # Decode the URL from bytes to string before parsing
        url = url.decode('utf-8')
        parsed_url = urlparse(url)
        # Check if the netloc is a valid IPv6 address
        if parsed_url.netloc and parsed_url.netloc.startswith('[') and parsed_url.netloc.endswith(']'):
            return True
    except UnicodeDecodeError:
        return False

    return False

def is_ipv4(url):
    if not url:
        return False

    try:
        # Decode the URL from bytes to string before parsing
        url = url.decode('utf-8')
        parsed_url = urlparse(url)
        # Check if the netloc is a valid IPv4 address
        if parsed_url.netloc and parsed_url.netloc.count('.') == 3:
            return True
    except UnicodeDecodeError:
        return False

    return False

def brute_force_domains(target_domain, min_length, max_length, num_answers, enable_subdir, enable_multithread, num_threads, enable_ipv6, sdmin, sdmax):
    characters = string.ascii_letters + string.digits + string.punctuation
    found_domains = []
    found_subdirs = []
    found_pages = []

    total_combinations = 0
    for length in range(min_length, max_length + 1):
        total_combinations += len(characters) ** length

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        if enable_subdir:
            subdir_thread = threading.Thread(target=brute_force_subdirs, args=(target_domain, found_pages, found_subdirs, sdmin, sdmax))
            subdir_thread.start()

        # Determine the number of worker threads based on the available CPU cores
        cpu_cores = psutil.cpu_count(logical=False)  # Get the number of physical cores
        max_threads = max(cpu_cores - 1, 1)  # Limit the number of threads to physical cores - 1 or at least 1
        worker_threads = min(cpu_cores, max_threads, num_threads)

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_threads)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []

        for length in range(min_length, max_length + 1):
            for combination in itertools.product(characters, repeat=length):
                subdomain = ''.join(combination)
                target = construct_url(target_domain, subdomain)

                if target is None:
                    # Skip invalid URLs (likely IPv6)
                    continue

                try:
                    # Check if the target is an IPv4 URL
                    if not enable_ipv6 and is_ipv4(target):
                        tasks.append(loop.run_in_executor(executor, resolve_domain, target, num_answers, pbar, found_domains, found_pages))
                except ValueError:
                    pass

        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

        if enable_subdir:
            subdir_thread.join()

    return found_domains, found_subdirs, found_pages

def main(target_domain, min_length, max_length, num_answers, enable_subdir, enable_multithread, num_threads, enable_ipv6, sdmin, sdmax):
    print_banner()
    print("Brute forcing in progress...")

    found_domains, _, found_pages = brute_force_domains(target_domain, min_length, max_length, num_answers,
                                                        enable_subdir, enable_multithread, num_threads, enable_ipv6, sdmin, sdmax)

    print("\nFound subdomains:")
    for domain in found_domains:
        print(domain)

    print("\nFound subdirectories:")
    for subdir in found_subdirs:
        print(subdir)

    print("\nFound pages:")
    for page in found_pages:
        print(page)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Domain brute-forcing script')
    parser.add_argument('-d', dest='target_domain', required=True, help='Target domain')
    parser.add_argument('-min', dest='min_length', type=int, default=1, help='Minimum subdomain length')
    parser.add_argument('-max', dest='max_length', type=int, default=3, help='Maximum subdomain length')
    parser.add_argument('-n', dest='num_answers', type=int, default=1, help='Number of answers to resolve')
    parser.add_argument('-subdir', dest='enable_subdir', action='store_true', help='Enable subdirectory brute-forcing')
    parser.add_argument('-m', dest='enable_multithread', action='store_true', help='Enable multithreaded execution')
    parser.add_argument('-t', dest='num_threads', type=int, default=2, help='Number of worker threads for multithreading')
    parser.add_argument('-ipv6', dest='enable_ipv6', action='store_true', help='Enable brute-forcing of IPv6 domains')
    parser.add_argument('-sdmin', dest='sdmin', type=int, default=1, help='Minimum subdirectory length')
    parser.add_argument('-sdmax', dest='sdmax', type=int, default=3, help='Maximum subdirectory length')

    args = parser.parse_args()

    main(args.target_domain, args.min_length, args.max_length, args.num_answers,
         args.enable_subdir, args.enable_multithread, args.num_threads, args.enable_ipv6, args.sdmin, args.sdmax)
