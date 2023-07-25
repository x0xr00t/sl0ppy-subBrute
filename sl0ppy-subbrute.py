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
import os
import psutil
import string
import threading
import urllib3
from colorama import Fore, Style, init
from tqdm import tqdm

def has_gpu():
    try:
        sensors = psutil.sensors_temperatures()
        if 'nvidia' in sensors:
            return True
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.TimeoutExpired):
        pass
    return False

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

def resolve_domain(target, num_answers, pbar, found_domains):
    try:
        answers = 'A' * num_answers
        for answer in answers:
            # Perform testing here and update the progress bar description accordingly
            pbar.set_description(f'Testing: {target}')
            pbar.update(1)

            answers = dns.resolver.resolve(target, 'A')
            for answer in answers:
                found_domains.append(target)
                break

    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NoNameservers:
        pass
    except dns.exception.Timeout:
        pass

def brute_force_subdirs(domain, subdir_format):
    characters = string.ascii_letters + string.digits + string.punctuation
    subdir = '/'
    target = construct_url(domain, subdir)  # Append subdir to domain

    try:
        response = http.request('GET', target)
        if response.status == 200:
            yield target
    except urllib3.exceptions.RequestException:
        pass

    with tqdm(total=len(characters), unit='character', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        for character in characters:
            subdir = f'/{subdir_format}/{character}'
            target = construct_url(domain, subdir)
            try:
                response = http.request('GET', target)
                if response.status == 200:
                    yield target
            except urllib3.exceptions.RequestException:
                pass

            pbar.set_description(f'Testing: {target}')
            pbar.update(1)

def construct_url(domain, subdirectory=None):
    if subdirectory:
        target = f"https://{domain}{subdirectory}"
    else:
        target = f"https://{domain}"

    return target

def generate_subdomains(target_domain, min_length, max_length):
    characters = string.ascii_letters + string.digits
    for length in range(min_length, max_length + 1):
        for combination in itertools.product(characters, repeat=length):
            subdomain = ''.join(combination)
            yield f"{subdomain}.{target_domain}"

def brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    found_domains = set()
    found_pages = set()

    total_combinations = sum(len(string.ascii_letters + string.digits) ** length for length in range(subdomain_min_length, subdomain_max_length + 1))

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        if enable_subdir:
            subdir_thread = threading.Thread(target=brute_force_subdirs, args=(target_domain, subdir_format))
            subdir_thread.start()

        if enable_multithread:
            if has_gpu():
                cpu_cores = psutil.cpu_count(logical=False)
                max_threads = max(cpu_cores - 1, 1)
                cpu_threads = min(cpu_cores, max_threads, num_threads)
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_threads)
            else:
                cpu_threads = num_threads
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_threads)

            with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_threads) as executor:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = []

                for subdomain in generate_subdomains(target_domain, subdomain_min_length, subdomain_max_length):
                    target = construct_url(subdomain)

                    if target is None:
                        # Skip invalid URLs (likely IPv6)
                        continue

                    try:
                        tasks.append(loop.run_in_executor(executor, resolve_domain, target, num_answers, pbar, found_domains))
                    except ValueError:
                        pass

                loop.run_until_complete(asyncio.gather(*tasks))
                loop.close()

        else:
            for subdomain in generate_subdomains(target_domain, subdomain_min_length, subdomain_max_length):
                target = construct_url(subdomain)

                if target is None:
                    # Skip invalid URLs (likely IPv6)
                    continue

                resolve_domain(target, num_answers, pbar, found_domains)

        if enable_subdir:
            subdir_thread.join()

    return found_domains, found_pages

def main(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    print_banner()
    print("Brute forcing in progress...")

    found_domains, found_pages = brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers,
                                                     enable_subdir, subdir_format, enable_multithread, num_threads)

    print("\n# Found subdirs:")
    for page in found_pages:
        print(f"{Fore.GREEN}{{v}} {page}{Style.RESET_ALL}")

    print("\n# Found subdomains:")
    for domain in found_domains:
        print(f"{Fore.GREEN}{{v}} {domain}{Style.RESET_ALL}")

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

    http = urllib3.PoolManager()

    main(args.target_domain, args.subdomain_min_length, args.subdomain_max_length, args.num_answers,
         args.enable_subdir, args.subdir_format, args.enable_multithread, args.num_threads)
