#!/usr/bin/env python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-subBrute

# imports
import os
import time
import psutil
import string
import asyncio
import aiohttp
import argparse
import itertools
import threading
import dns.resolver
import concurrent.futures
from tqdm import tqdm
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Global variable to store the current memory usage percentage
current_mem_usage = 0

def get_mem_usage():
    # Get the current memory usage percentage
    global current_mem_usage
    mem = psutil.virtual_memory()
    current_mem_usage = mem.percent

def monitor_memory():
    while True:
        # Check memory usage every 5 seconds
        get_mem_usage()
        if current_mem_usage > 90:
            # If memory usage is above 90%, sleep for 10 seconds and check again
            time.sleep(10)
        else:
            # If memory usage is below 90%, sleep for 1 second and check again
            time.sleep(1)

def has_gpu():
    try:
        sensors = psutil.sensors_temperatures()
        if 'nvidia' in sensors or 'amdgpu' in sensors:
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
    print("{I} Cause we brute-force all your subdomains & subdirs in a sl0ppy manner ;)")
    print(Style.RESET_ALL)

# Global DNS cache to store resolved domains
dns_cache = {}

async def resolve_domain(session, target, num_answers, pbar, found_domains, sem, tested_urls, enable_subdom):
    if target in dns_cache:
        answers = dns_cache[target]
    else:
        try:
            answers = 'A' * num_answers
            for answer in answers:
                # Perform testing here and update the progress bar description accordingly
                async with sem:
                    if target.startswith("http://") or target.startswith("https://"):
                        target_domain = urlparse(target).netloc
                    else:
                        target_domain = target
                    if enable_subdom:
                        if '.' in target_domain:
                            subdomain, _, target_domain = target_domain.partition('.')
                            if not subdomain.isalpha():
                                subdomain = "testchars"  # Default subdomain name for non-alphabetic characters
                            target_domain = f"{subdomain}.{target_domain}"
                        else:
                            target_domain = f"testchars.{target_domain}"  # Default subdomain name for no subdomain specified
                    if not target_domain.startswith("http://") and not target_domain.startswith("https://"):
                        target_domain = f"{target_domain}"  # Add http:// prefix for correct display
                    pbar.set_description(f'Testing: {target_domain}')
                    pbar.update(1)

                answers = dns.resolver.resolve(target, 'A')
                break
        except dns.resolver.NXDOMAIN:
            answers = None
        except dns.resolver.NoAnswer:
            answers = None
        except dns.resolver.NoNameservers:
            answers = None
        except dns.exception.Timeout:
            answers = None

        # Update the DNS cache
        dns_cache[target] = answers

    if answers:
        found_domains.add(target)
        if target not in tested_urls:
            tested_urls.add(target)
            async with sem:
                pbar.set_description(f'{Fore.GREEN}Found: {target_domain}{Style.RESET_ALL}')
                pbar.update(1)

async def brute_force_subdirs(session, target_domain, characters, pbar, found_pages, sem, tested_urls, enable_multithread, enable_subdir):
    async for subdir in generate_subdirs(target_domain, characters):
        subdir_url = subdir
        target = construct_url(target_domain, subdir_url)

        if target not in tested_urls:
            async with sem:
                if not subdir_url.startswith("http://") and not subdir_url.startswith("https://"):
                    subdir_url = f"http://{subdir_url}"  # Add http:// prefix for correct display
                subdir_url = subdir_url.rstrip(':')  # Remove trailing colon
                pbar.set_description(f'Testing: {subdir_url}:')  # Add trailing colon
                pbar.update(1)

            try:
                async with session.get(target) as response:
                    if response.status == 200:
                        found_pages.add(target)
                        tested_urls.add(target)
                        async with sem:
                            pbar.set_description(f'{Fore.GREEN}Found: {subdir_url}:{Style.RESET_ALL}')  # Add trailing colon
                            pbar.update(1)
            except aiohttp.ClientError:
                pass
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                pass


async def generate_subdirs(target_domain, characters):
    for length in range(1, 20):
        for combination in itertools.product(characters, repeat=length):
            subdir = ''.join(combination)
            yield f"{target_domain}/{subdir}"

async def generate_subdomains(target_domain, min_length, max_length, enable_subdom):
    characters = string.ascii_letters + string.digits
    for length in range(min_length, max_length + 1):
        for combination in itertools.product(characters, repeat=length):
            subdomain = ''.join(combination)
            if enable_subdom:
                yield subdomain  # Generate subdomains without testchars prefix
            else:
                yield f"testchars.{subdomain}"  # Add testchars prefix for non-subdomains

def construct_url(target_domain, subdomain_url):
    if target_domain.startswith("http://") or target_domain.startswith("https://"):
        parsed_url = urlparse(target_domain)
        if parsed_url.scheme:
            return f"{parsed_url.scheme}://{subdomain_url}.{parsed_url.netloc}"
        else:
            return f"{parsed_url.scheme}{subdomain_url}.{parsed_url.netloc}"  # Add scheme without "://"
    else:
        return f"{subdomain_url}.{target_domain}"

def check_memory_usage():
    mem = psutil.virtual_memory()
    return mem.percent

async def brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, enable_subdom, enable_multithread, num_threads):
    found_domains = set()
    found_pages = set()
    tested_urls = set()  # A set to keep track of tested URLs and avoid duplicates in the progress bar

    total_combinations = sum(len(string.ascii_letters + string.digits) ** length for length in range(subdomain_min_length, subdomain_max_length + 1))

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        sem = asyncio.Semaphore(num_threads)

        if enable_subdir:
            characters = string.ascii_letters + string.digits + string.punctuation
            async with aiohttp.ClientSession() as session:
                subdir_coroutine = brute_force_subdirs(session, target_domain, characters, pbar, found_pages, sem, tested_urls, enable_multithread, enable_subdir)
                subdir_task = asyncio.create_task(subdir_coroutine)

        memory_limit = check_memory_usage()

        if enable_multithread:
            if has_gpu() and enable_subdir:
                cpu_cores = psutil.cpu_count(logical=False)
                max_threads = max(cpu_cores - 1, 1)
                cpu_threads = min(cpu_cores, max_threads, num_threads)
                num_threads = cpu_threads
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_threads)
            else:
                cpu_threads = num_threads
                num_threads = 1
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_threads)

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = []

                async for subdomain in generate_subdomains(target_domain, subdomain_min_length, subdomain_max_length, enable_subdom):
                    if not enable_subdom:
                        subdomain_url = f"{subdomain}"
                    else:
                        subdomain_url = subdomain
                    if subdomain_url not in tested_urls:  # Skip if already tested to avoid duplicates
                        target = construct_url(target_domain, subdomain_url)
                        tasks.append(loop.run_in_executor(executor, resolve_domain, session, target, num_answers, pbar, found_domains, sem, tested_urls, enable_subdom))

                await asyncio.gather(*tasks)
                loop.close()
        else:
            async with aiohttp.ClientSession() as session:
                async for subdomain in generate_subdomains(target_domain, subdomain_min_length, subdomain_max_length, enable_subdom):
                    if not enable_subdom:
                        subdomain_url = f"{subdomain}"
                    else:
                        subdomain_url = subdomain
                    if subdomain_url not in tested_urls:  # Skip if already tested to avoid duplicates
                        target = construct_url(target_domain, subdomain_url)
                        await resolve_domain(session, target, num_answers, pbar, found_domains, sem, tested_urls, enable_subdom)

        if enable_subdir:
            await subdir_task

    return found_domains, found_pages

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sl0ppy Brute - A brute-force subdomain and subdirectory enumeration tool")
    parser.add_argument("target_domain", help="The target domain to brute-force")
    parser.add_argument("--subdomain-min-length", type=int, default=1, help="Minimum length of subdomains")
    parser.add_argument("--subdomain-max-length", type=int, default=3, help="Maximum length of subdomains")
    parser.add_argument("--num-answers", type=int, default=3, help="Number of DNS query answers to wait for")
    parser.add_argument("--subdir", action="store_true", help="Enable brute-forcing subdirectories")
    parser.add_argument("--subdom", action="store_true", help="Enable brute-forcing subdomains")
    parser.add_argument("--multithread", action="store_true", help="Enable multithreading")
    parser.add_argument("--num-threads", type=int, default=10, help="Number of threads to use for multithreading")

    args = parser.parse_args()

    print_banner()

    enable_subdir = args.subdir
    enable_subdom = args.subdom
    enable_multithread = args.multithread
    num_threads = args.num_threads

    if enable_subdir and enable_subdom:
        print(f"{Fore.YELLOW}[!] Warning: Both --subdir and --subdom are enabled. This may cause a longer runtime.{Style.RESET_ALL}")

    get_mem_usage()
    memory_monitor_thread = threading.Thread(target=monitor_memory)
    memory_monitor_thread.start()

    try:
        found_domains, found_pages = asyncio.run(
            brute_force_domains(
                args.target_domain,
                args.subdomain_min_length,
                args.subdomain_max_length,
                args.num_answers,
                enable_subdir,
                enable_subdom,
                enable_multithread,
                num_threads,
            )
        )
        print(f"\n{Fore.GREEN}[+] Found Domains:{Style.RESET_ALL}")
        for domain in found_domains:
            print(domain)
        print(f"\n{Fore.GREEN}[+] Found Pages:{Style.RESET_ALL}")
        for page in found_pages:
            print(page)
    except KeyboardInterrupt:
        print(f"{Fore.RED}\n[-] User interrupted the process. Exiting...{Style.RESET_ALL}")
        os._exit(0)

    memory_monitor_thread.join()
