import asyncio
import argparse
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

def brute_force_subdirs(domain, found_pages, subdir_format):  # Updated function signature
    characters = string.ascii_letters + string.digits + string.punctuation
    subdir = '/'
    target = construct_url(domain, subdir_format)  # Append subdir_format to domain

    try:
        response = requests.get(target)
        if response.status_code == 200:
            found_pages.append(target)
    except requests.exceptions.RequestException:
        pass

    with tqdm(total=1, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        if subdir_format:
            chars_msg = f"Brute forcing in progress...\nTesting: https://{domain}/"
            print(chars_msg)

        pbar.set_description(f'Testing: {target}')
        pbar.update(1)

def construct_url(domain, subdirectory=None):
    if subdirectory:
        target = f"https://{domain}{subdirectory}"
    else:
        target = f"https://{domain}"

    return target

def brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    characters = string.ascii_letters + string.digits + string.punctuation
    found_domains = []
    found_pages = []

    total_combinations = 0
    for length in range(subdomain_min_length, subdomain_max_length + 1):
        total_combinations += len(characters) ** length

    with tqdm(total=total_combinations, unit='combination', ncols=80,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        if enable_subdir:
            subdir_thread = threading.Thread(target=brute_force_subdirs, args=(target_domain, found_pages, subdir_format))
            subdir_thread.start()

        # Determine the number of worker threads based on the available CPU cores
        cpu_cores = psutil.cpu_count(logical=False)  # Get the number of physical cores
        max_threads = max(cpu_cores - 1, 1)  # Limit the number of threads to physical cores - 1 or at least 1
        worker_threads = min(cpu_cores, max_threads, num_threads)

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_threads)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []

        for length in range(subdomain_min_length, subdomain_max_length + 1):
            for combination in itertools.product(characters, repeat=length):
                subdomain = ''.join(combination)

                if not enable_subdir:
                    target = construct_url(f"{subdomain}.{target_domain}")
                else:
                    target = construct_url(target_domain)

                if target is None:
                    # Skip invalid URLs (likely IPv6)
                    continue

                try:
                    tasks.append(loop.run_in_executor(executor, resolve_domain, target, num_answers, pbar, found_domains, found_pages))
                except ValueError:
                    pass

        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

        if enable_subdir:
            subdir_thread.join()

    return found_domains, found_pages

def main(target_domain, subdomain_min_length, subdomain_max_length, num_answers, enable_subdir, subdir_format, enable_multithread, num_threads):
    print_banner()
    print("Brute forcing in progress...")

    found_domains, found_pages = brute_force_domains(target_domain, subdomain_min_length, subdomain_max_length, num_answers,
                                                     enable_subdir, subdir_format, enable_multithread, num_threads)

    print("\nFound subdomains:")
    for domain in found_domains:
        print(domain)

    print("\nFound pages:")
    for page in found_pages:
        print(page)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Domain brute-forcing script')
    parser.add_argument('-d', dest='target_domain', required=True, help='Target domain')
    parser.add_argument('-min', dest='subdomain_min_length', type=int, default=1, help='Minimum subdomain length')
    parser.add_argument('-max', dest='subdomain_max_length', type=int, default=3, help='Maximum subdomain length')
    parser.add_argument('-n', dest='num_answers', type=int, default=1, help='Number of answers to resolve')
    parser.add_argument('-subdir', dest='enable_subdir', action='store_true', help='Enable subdirectory brute-forcing')
    parser.add_argument('-subdom', dest='subdir_format', default="", help='Subdirectory format when -subdir is enabled')
    parser.add_argument('-m', dest='enable_multithread', action='store_true', help='Enable multithreaded execution')
    parser.add_argument('-t', dest='num_threads', type=int, default=2, help='Number of worker threads for multithreading')

    args = parser.parse_args()

    main(args.target_domain, args.subdomain_min_length, args.subdomain_max_length, args.num_answers,
         args.enable_subdir, args.subdir_format, args.enable_multithread, args.num_threads)
