#!/usr/bin/env python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-DomainBrute

import sys
import dns.resolver
import string
import itertools
import argparse
from colorama import Fore, Style, init
import random
import threading
import psutil
from tqdm import tqdm

def print_banner():
    init(autoreset=True)
    banner = """
           /$$  /$$$$$$                                        /$$$$$$$                        /$$              
          | $$ /$$$_  $$                                      | $$__  $$                      | $$              
  /$$$$$$$| $$| $$$$\ $$  /$$$$$$   /$$$$$$  /$$   /$$        | $$  \ $$  /$$$$$$  /$$   /$$ /$$$$$$    /$$$$$$ 
 /$$_____/| $$| $$ $$ $$ /$$__  $$ /$$__  $$| $$  | $$ /$$$$$$| $$$$$$$  /$$__  $$| $$  | $$|_  $$_/   /$$__  $$
|  $$$$$$ | $$| $$\ $$$$| $$  \ $$| $$  \ $$| $$  | $$|______/| $$__  $$| $$  \__/| $$  | $$  | $$    | $$$$$$$$
 \____  $$| $$| $$ \ $$$| $$  | $$| $$  | $$| $$  | $$        | $$  \ $$| $$      | $$  | $$  | $$ /$$| $$_____/
 /$$$$$$$/| $$|  $$$$$$/| $$$$$$$/|  $$$$$$$|  $$$$$$$        | $$$$$$$/| $$      |  $$$$$$/  |  $$$$/|  $$$$$$$
|_______/ |__/ \______/ | $$____/ | $$____/  \____  $$        |_______/ |__/       \______/    \___/   \_______/
                        | $$      | $$       /$$  | $$                                                          
                        | $$      | $$      |  $$$$$$/                                                          
                        |__/      |__/       \______/                                                           
                     /$$             /$$ /$$                 /$$$$$$$                        /$$                        
                    | $$            | $$|__/                | $$__  $$                      | $$                        
  /$$$$$$$ /$$   /$$| $$$$$$$   /$$$$$$$ /$$  /$$$$$$       | $$  \ $$  /$$$$$$  /$$   /$$ /$$$$$$    /$$$$$$   /$$$$$$ 
 /$$_____/| $$  | $$| $$__  $$ /$$__  $$| $$ /$$__  $$      | $$$$$$$  /$$__  $$| $$  | $$|_  $$_/   /$$__  $$ /$$__  $$
|  $$$$$$ | $$  | $$| $$  \ $$| $$  | $$| $$| $$  \__/      | $$__  $$| $$  \__/| $$  | $$  | $$    | $$$$$$$$| $$  \__/
 \____  $$| $$  | $$| $$  | $$| $$  | $$| $$| $$            | $$  \ $$| $$      | $$  | $$  | $$ /$$| $$_____/| $$      
 /$$$$$$$/|  $$$$$$/| $$$$$$$/|  $$$$$$$| $$| $$            | $$$$$$$/| $$      |  $$$$$$/  |  $$$$/|  $$$$$$$| $$      
|_______/  \______/ |_______/  \_______/|__/|__/            |_______/ |__/       \______/    \___/   \_______/|__/    
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


def brute_force_domains(domain):
    characters = string.ascii_letters + string.digits + string.punctuation
    found_domains = []

    total_combinations = 0
    for length in range(1, 60):
        total_combinations += len(characters) ** length

    with tqdm(total=total_combinations, unit='combination', ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
        for length in range(1, 60):
            for combination in itertools.product(characters, repeat=length):
                subdomain = ''.join(combination)
                target = subdomain + '.' + domain
                try:
                    answers = 'A' * 100
                    for answer in answers:
                        pass
                except dns.resolver.NXDOMAIN:
                    pass
                except dns.resolver.NoAnswer:
                    pass
                except dns.resolver.NoNameservers:
                    pass
                except dns.exception.Timeout:
                    pass
                except dns.resolver.NoNameservers:
                    pass
                else:
                    found_domains.append(target)

                # Check CPU usage and limit to 80%
                if psutil.cpu_percent() > 80:
                    threading.Event().wait(0.1)  # Sleep for 100ms to reduce CPU usage

                pbar.set_description(f'Testing: {subdomain}')  # Update the progress bar description
                pbar.update(1)  # Increment the progress bar

    return found_domains


def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser(description='Domain brute-forcing script')
    parser.add_argument('-d', dest='target_domain', help='Target domain to brute force')

    args = parser.parse_args()

    # Check if the target domain is provided
    if args.target_domain:
        target_domain = args.target_domain
        print_banner()
        print("Brute forcing in progress...")
        found_domains = brute_force_domains(target_domain)
        print("\nFound subdomains:")
        for domain in found_domains:
            print(domain)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
