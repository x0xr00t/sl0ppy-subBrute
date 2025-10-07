#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sl0ppy-subBrute v5.0 - Ultimate Subdomain & Path Fuzzer
Author: p.hoogeveen (x0xr00t)
Enhanced with Intel GPU detection and optimized resource management
"""

import os
import re
import sys
import time
import psutil
import string
import asyncio
import aiohttp
import argparse
import itertools
import threading
import subprocess
import dns.resolver
import platform
from urllib.parse import urlparse, urljoin
from tqdm import tqdm
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Character sets for brute-forcing
CHARSET_ALPHA_LOWER = string.ascii_lowercase
CHARSET_ALPHA_UPPER = string.ascii_uppercase
CHARSET_DIGITS = string.digits
CHARSET_SPECIAL = "-._~"  # URL-safe special chars
CHARSET_FUZZ = CHARSET_ALPHA_LOWER + CHARSET_ALPHA_UPPER + CHARSET_DIGITS + CHARSET_SPECIAL

# Common elements for targeted fuzzing
COMMON_PATHS = [
    'admin', 'api', 'backup', 'config', 'css', 'db', 'docs', 'images', 'include',
    'js', 'lib', 'login', 'logs', 'old', 'phpmyadmin', 'private', 'public', 'secure',
    'sql', 'static', 'temp', 'test', 'upload', 'uploads', 'wp-admin', 'wp-content',
    'wp-includes', 'wp-login', 'assets', 'cache', 'data', 'dist', 'download', 'files',
    'media', 'node_modules', 'src', 'vendor', 'console', 'debug', 'manager', 'adminer',
    'webmail', 'mail', 'cgi-bin', 'phpinfo', 'server-status', 'robots.txt', '.git',
    '.svn', '.env', '.htaccess', '.htpasswd', 'composer.json', 'package.json'
]

COMMON_EXTENSIONS = [
    '', '.php', '.html', '.htm', '.asp', '.aspx', '.jsp', '.json', '.xml', '.txt',
    '.bak', '.old', '.backup', '.sql', '.db', '.git', '.svn', '.env', '.config', '.log',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.pdf', '.doc', '.xls', '.ppt', '.csv',
    '.js', '.css', '.jpg', '.png', '.gif', '.svg', '.woff', '.ttf', '.eot', '.sh',
    '.py', '.rb', '.pl', '.java', '.c', '.cpp', '.go', '.swift', '.kt', '.scala'
]

COMMON_SUBDOMAINS = [
    'www', 'mail', 'ftp', 'webmail', 'ns1', 'ns2', 'pop', 'smtp', 'imap', 'dev',
    'test', 'staging', 'beta', 'alpha', 'demo', 'api', 'm', 'mobile', 'static',
    'cdn', 'assets', 'media', 'blog', 'shop', 'app', 'portal', 'admin', 'secure',
    'my', 'user', 'account', 'profile', 'support', 'help', 'docs', 'status', 'stats'
]

# Global variables
current_mem_usage = 0
dns_cache = {}
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
found_items = {}
update_lock = threading.Lock()
last_update_time = 0
update_interval = 3  # seconds between terminal updates

def detect_gpu():
    """Detect available GPUs (NVIDIA, AMD, Intel)"""
    gpus = {
        'nvidia': False,
        'amd': False,
        'intel': False
    }

    try:
        # Check for NVIDIA GPUs
        if 'nvidia' in psutil.sensors_temperatures():
            gpus['nvidia'] = True

        # Check for AMD GPUs
        if 'amdgpu' in psutil.sensors_temperatures():
            gpus['amd'] = True

        # Check for Intel GPUs
        try:
            # Try to detect Intel GPUs through lspci (Linux)
            if platform.system().lower() == 'linux':
                result = subprocess.run(['lspci'], capture_output=True, text=True)
                if 'VGA compatible controller: Intel' in result.stdout:
                    gpus['intel'] = True
            # Alternative method for other platforms
            elif platform.system().lower() == 'windows':
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if 'Intel' in gpu.Name:
                        gpus['intel'] = True
                        break
        except:
            pass

        # Fallback method using OpenCL
        try:
            import pyopencl
            platforms = pyopencl.get_platforms()
            for platform in platforms:
                if 'Intel' in platform.name:
                    gpus['intel'] = True
                    break
        except:
            pass

    except Exception as e:
        print(f"{Fore.YELLOW}[!] GPU detection error: {e}{Style.RESET_ALL}")

    return gpus

def has_sufficient_resources():
    """Check if system has sufficient resources for multithreading"""
    cpu_usage = psutil.cpu_percent()
    gpus = detect_gpu()

    has_dedicated_gpu = gpus['nvidia'] or gpus['amd'] or gpus['intel']

    # Be more conservative with GPU systems
    if has_dedicated_gpu:
        return cpu_usage < 80
    return cpu_usage < 90

def get_mem_usage():
    """Get current memory usage percentage"""
    global current_mem_usage
    mem = psutil.virtual_memory()
    current_mem_usage = mem.percent
    return current_mem_usage

def monitor_memory():
    """Monitor system memory usage"""
    while True:
        usage = get_mem_usage()
        if usage > 90:
            print(f"{Fore.YELLOW}[!] High memory usage: {usage}%{Style.RESET_ALL}")
            time.sleep(10)
        else:
            time.sleep(1)

class TerminalManager:
    """Handles cross-platform terminal spawning and updates"""

    def __init__(self):
        self.process = None
        self.temp_file = "/tmp/sl0ppy_findings.txt"
        self.terminal_cmd = self._detect_terminal_command()

    def _detect_terminal_command(self):
        """Detect the best terminal command for the current system"""
        system = platform.system().lower()

        if system == 'linux':
            terminals = ['xterm', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'terminator', 'rxvt']
            for term in terminals:
                if subprocess.run(['which', term], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                    return term
            return 'xterm'  # fallback

        elif system == 'darwin':  # macOS
            return 'open -a Terminal'

        else:  # Windows or unknown
            return None

    def _get_terminal_args(self):
        """Get terminal-specific arguments for displaying the file"""
        term = self.terminal_cmd

        if not term:
            return None

        if 'xterm' in term:
            return [term, '-hold', '-e', f'cat {self.temp_file}; echo; read -p "Press Enter to close..."']
        elif 'gnome-terminal' in term:
            return [term, '--', 'bash', '-c', f'cat {self.temp_file}; echo; read -p "Press Enter to close..."']
        elif 'konsole' in term:
            return [term, '-e', 'bash', '-c', f'cat {self.temp_file}; echo; read -p "Press Enter to close..."']
        elif 'mac' in term.lower() or 'open' in term:
            return [term, '-a', 'TextEdit', self.temp_file]
        else:
            return [term, '-e', f'cat {self.temp_file}; echo; read -p "Press Enter to close..."']

    def update_terminal(self, content):
        """Update the terminal window with new content"""
        global last_update_time

        current_time = time.time()
        if current_time - last_update_time < update_interval:
            return

        last_update_time = current_time

        try:
            with open(self.temp_file, 'w') as f:
                f.write(content)

            if not self.process or self.process.poll() is not None:
                args = self._get_terminal_args()
                if args:
                    self.process = subprocess.Popen(args)
        except Exception as e:
            print(f"{Fore.RED}[!] Terminal update error: {e}{Style.RESET_ALL}")

    def close(self):
        """Clean up terminal resources"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

def print_banner():
    """Print the tool banner"""
    banner = r"""
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
    color_order = [Fore.RED, Fore.YELLOW, Fore.CYAN, Fore.GREEN]
    colored_banner = ""
    for i, line in enumerate(banner.splitlines()):
        color = color_order[i % len(color_order)]
        colored_banner += f"{color}{line}\n"

    print(colored_banner)
    print(f"{Fore.GREEN}[{Fore.WHITE}I{Fore.GREEN}] {Fore.YELLOW}Ultimate {Fore.RED}subdomain {Fore.YELLOW}& {Fore.RED}path {Fore.YELLOW}fuzzer {Fore.WHITE}- {Fore.CYAN}10/10 {Fore.WHITE}detection{Style.RESET_ALL}")

def normalize_url(url):
    """Normalize URL by adding scheme if missing and removing fragments"""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    parsed = urlparse(url)
    return parsed.scheme + '://' + parsed.netloc + parsed.path.rstrip('/')

async def is_interesting_response(response):
    """Check if response is interesting based on multiple factors"""
    interesting_codes = {200, 204, 301, 302, 307, 401, 403, 405, 500, 400, 404, 418}

    if response.status in interesting_codes:
        return True

    content_type = response.headers.get('Content-Type', '').lower()
    content_length = int(response.headers.get('Content-Length', 0))

    # Check for interesting content types
    if content_type and any(x in content_type for x in [
        'text/', 'json', 'xml', 'javascript', 'html', 'css', 'plain'
    ]):
        return True

    # Check for interesting content in body
    if content_length > 0 and content_length < 100000:
        try:
            body_sample = (await response.read(200)).decode('utf-8', errors='ignore').lower()
            interesting_patterns = [
                'password', 'username', 'admin', 'login', 'error', 'warning',
                'database', 'sql', 'root', 'config', 'secret', 'key', 'token',
                'credentials', 'auth', 'session', 'cookie', 'private', 'internal',
                'debug', 'stack trace', 'exception', 'dump', 'backup', 'old',
                'test', 'dev', 'staging', 'database', 'connection', 'query'
            ]
            if any(pattern in body_sample for pattern in interesting_patterns):
                return True
        except:
            pass

    return False

async def check_url(session, url, semaphore, terminal_manager=None):
    """Check a single URL with proper error handling and response analysis"""
    global found_items

    try:
        async with semaphore:
            async with session.get(
                url,
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={'User-Agent': user_agent}
            ) as response:
                if await is_interesting_response(response):
                    # Read response body for analysis
                    try:
                        content_sample = (await response.read(200)).decode('utf-8', errors='ignore')[:100]
                    except:
                        content_sample = "Binary content"

                    result = {
                        'url': url,
                        'status': response.status,
                        'content_type': response.headers.get('Content-Type', ''),
                        'content_length': response.headers.get('Content-Length', '0'),
                        'location': response.headers.get('Location', ''),
                        'content_sample': content_sample,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    with update_lock:
                        found_items[url] = result

                    # Update terminal if manager exists
                    if terminal_manager:
                        terminal_manager.update_terminal(format_results(found_items))

                    return result

    except (aiohttp.ClientError, asyncio.TimeoutError, Exception) as e:
        pass

    return None

async def generate_fuzz_paths(base_url, max_depth=3, use_common=True):
    """Generate comprehensive paths for fuzzing with multiple levels"""
    parsed = urlparse(base_url)
    base_path = parsed.path.rstrip('/') if parsed.path else ''

    # First yield common paths if enabled
    if use_common:
        for path in COMMON_PATHS:
            for ext in COMMON_EXTENSIONS:
                test_path = f"{base_path}/{path}{ext}" if base_path else f"/{path}{ext}"
                yield urljoin(base_url, test_path.lstrip('/'))

    # Generate single-level paths with full charset
    for length in range(1, 8):  # 1-7 character paths
        for combo in itertools.product(CHARSET_FUZZ, repeat=length):
            path = ''.join(combo)
            for ext in COMMON_EXTENSIONS:
                test_path = f"{base_path}/{path}{ext}" if base_path else f"/{path}{ext}"
                yield urljoin(base_url, test_path.lstrip('/'))

    # Generate multi-level paths (e.g., /dir/subdir/file)
    if max_depth > 1:
        for depth in range(2, max_depth + 1):
            # Generate all possible path combinations for this depth
            for path_parts in itertools.product(CHARSET_FUZZ, repeat=depth*2):  # 2 chars per level
                path = '/'.join(
                    ''.join(path_parts[i*2:(i+1)*2])
                    for i in range(depth)
                )
                for ext in COMMON_EXTENSIONS:
                    test_path = f"{base_path}/{path}{ext}" if base_path else f"/{path}{ext}"
                    yield urljoin(base_url, test_path.lstrip('/'))

async def generate_fuzz_subdomains(base_domain, max_levels=3, use_common=True):
    """Generate subdomains including multi-level subdomains (e.g., a.b.example.com)"""
    # First yield common subdomains if enabled
    if use_common:
        for sub in COMMON_SUBDOMAINS:
            yield f"{sub}.{base_domain}"

    # Generate single-level subdomains
    for length in range(1, 12):  # 1-11 character subdomains
        for combo in itertools.product(CHARSET_FUZZ, repeat=length):
            sub = ''.join(combo)
            yield f"{sub}.{base_domain}"

    # Generate multi-level subdomains (e.g., a.b.example.com)
    if max_levels > 1:
        for level in range(2, max_levels + 1):
            for parts in itertools.product(CHARSET_FUZZ, repeat=level*2):  # 2 chars per level
                sub_parts = [
                    ''.join(parts[i*2:(i+1)*2])
                    for i in range(level)
                ]
                subdomain = '.'.join(reversed(sub_parts))  # a.b.c becomes c.b.a
                yield f"{subdomain}.{base_domain}"

async def brute_force_paths(session, base_url, semaphore, pbar, terminal_manager, max_depth=2, use_common=True):
    """Brute force paths with comprehensive fuzzing"""
    processed = set()

    async for url in generate_fuzz_paths(base_url, max_depth, use_common):
        if url in processed:
            continue
        processed.add(url)

        description = f"Testing: {url[:80]}..."  # Truncate long URLs
        pbar.set_description(description)
        pbar.update(1)

        await check_url(session, url, semaphore, terminal_manager)

async def brute_force_subdomains(session, base_domain, semaphore, pbar, terminal_manager, max_levels=2, use_common=True):
    """Brute force subdomains including multi-level subdomains"""
    processed = set()

    async for subdomain in generate_fuzz_subdomains(base_domain, max_levels, use_common):
        if subdomain in processed:
            continue
        processed.add(subdomain)

        description = f"Testing: {subdomain[:80]}..."
        pbar.set_description(description)
        pbar.update(1)

        try:
            # First try DNS resolution
            answers = await asyncio.get_event_loop().run_in_executor(
                None, lambda: dns.resolver.resolve(subdomain, 'A')
            )
            if answers:
                url = f"http://{subdomain}"
                await check_url(session, url, semaphore, terminal_manager)

        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            continue
        except Exception as e:
            continue

async def main_brute_force(args):
    """Main brute force function with proper resource management"""
    global found_items
    found_items = {}

    base_domain = args.target_domain
    terminal_manager = TerminalManager()

    # Detect GPUs and show system info
    gpus = detect_gpu()
    gpu_info = []
    if gpus['nvidia']:
        gpu_info.append("NVIDIA")
    if gpus['amd']:
        gpu_info.append("AMD")
    if gpus['intel']:
        gpu_info.append("Intel")

    print(f"{Fore.BLUE}[*] System Info:{Style.RESET_ALL}")
    print(f"{Fore.BLUE}    CPU Cores:{Style.RESET_ALL} {psutil.cpu_count(logical=True)}")
    print(f"{Fore.BLUE}    Memory:{Style.RESET_ALL} {psutil.virtual_memory().total / (1024**3):.2f} GB")
    print(f"{Fore.BLUE}    GPUs:{Style.RESET_ALL} {', '.join(gpu_info) if gpu_info else 'None detected'}")

    # Calculate total combinations for progress bar
    path_combinations = 0
    if args.subdir:
        path_combinations = (
            (len(COMMON_PATHS) * len(COMMON_EXTENSIONS) if not args.no_common else 0) +
            sum(len(CHARSET_FUZZ) ** l for l in range(1, 8)) * len(COMMON_EXTENSIONS) +
            sum(len(CHARSET_FUZZ) ** (d*2) for d in range(2, args.max_depth + 1)) * len(COMMON_EXTENSIONS)
        )

    subdom_combinations = 0
    if args.subdom:
        subdom_combinations = (
            (len(COMMON_SUBDOMAINS) if not args.no_common else 0) +
            sum(len(CHARSET_FUZZ) ** l for l in range(1, 12)) +
            sum(len(CHARSET_FUZZ) ** (l*2) for l in range(2, args.max_levels + 1))
        )

    total_combinations = path_combinations + subdom_combinations

    # Adjust threads based on GPU detection
    if any(gpus.values()) and args.threads > 50:
        print(f"{Fore.YELLOW}[!] GPU detected - reducing thread count to 50 for stability{Style.RESET_ALL}")
        args.threads = 50

    # Configure progress bar
    with tqdm(total=total_combinations, unit='test',
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

        semaphore = asyncio.Semaphore(args.threads)
        timeout = aiohttp.ClientTimeout(total=args.timeout)
        connector = aiohttp.TCPConnector(
            limit=args.threads,
            force_close=True,
            enable_cleanup_closed=True
        )

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            tasks = []

            if args.subdom:
                task = asyncio.create_task(
                    brute_force_subdomains(
                        session, base_domain,
                        semaphore, pbar, terminal_manager,
                        args.max_levels, not args.no_common
                    )
                )
                tasks.append(task)

            if args.subdir:
                base_url = f"http://{base_domain}" if not base_domain.startswith(('http://', 'https://')) else base_domain
                task = asyncio.create_task(
                    brute_force_paths(
                        session, base_url,
                        semaphore, pbar, terminal_manager,
                        args.max_depth, not args.no_common
                    )
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

    terminal_manager.close()
    return found_items

def format_results(found_items):
    """Format results for display with proper coloring and organization"""
    if not found_items:
        return f"{Fore.YELLOW}No findings yet.{Style.RESET_ALL}"

    output = f"{Fore.CYAN}=== Findings ({len(found_items)}) ==={Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}\n\n"

    # Group by type and status
    subdomains = {}
    paths = {}

    for url, details in found_items.items():
        if 'dns_resolved' in details:
            status = details.get('status', 'DNS_ONLY')
            subdomains.setdefault(status, []).append((url, details))
        else:
            status = details.get('status', '?')
            paths.setdefault(status, []).append((url, details))

    # Sort and display subdomains
    if subdomains:
        output += f"{Fore.CYAN}--- Subdomains ---{Style.RESET_ALL}\n"
        for status, items in sorted(subdomains.items()):
            color = Fore.GREEN if status == 200 else Fore.YELLOW if status == 'DNS_ONLY' else Fore.CYAN
            output += f"{color}[{status}] ({len(items)}){Style.RESET_ALL}\n"
            for url, details in sorted(items, key=lambda x: x[0]):
                sample = details.get('content_sample', '')[:30].replace('\n', ' ')
                output += f"  {color}{url}{Style.RESET_ALL}"
                if sample:
                    output += f" {Fore.WHITE}({sample}...){Style.RESET_ALL}"
                output += f" {Fore.BLUE}{details.get('timestamp', '')}{Style.RESET_ALL}\n"
            output += "\n"

    # Sort and display paths
    if paths:
        output += f"{Fore.CYAN}--- Paths ---{Style.RESET_ALL}\n"
        for status, items in sorted(paths.items()):
            color = Fore.GREEN if status == 200 else Fore.YELLOW if status == 403 else Fore.CYAN
            output += f"{color}[{status}] ({len(items)}){Style.RESET_ALL}\n"
            for url, details in sorted(items, key=lambda x: x[0]):
                sample = details.get('content_sample', '')[:30].replace('\n', ' ')
                output += f"  {color}{url}{Style.RESET_ALL}"
                if sample:
                    output += f" {Fore.WHITE}({sample}...){Style.RESET_ALL}"
                output += f" {Fore.BLUE}{details.get('timestamp', '')}{Style.RESET_ALL}\n"
            output += "\n"

    return output

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Sl0ppy Brute v5.0 - Ultimate Subdomain & Path Fuzzer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("target_domain", help="Target domain (e.g., example.com)")
    parser.add_argument("--subdom", action="store_true", help="Enable subdomain fuzzing")
    parser.add_argument("--subdir", action="store_true", help="Enable path/directory fuzzing")
    parser.add_argument("--min-length", type=int, default=1, help="Minimum length for brute-forcing")
    parser.add_argument("--max-length", type=int, default=12, help="Maximum length for single-level brute-forcing")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum depth for path brute-forcing")
    parser.add_argument("--max-levels", type=int, default=2, help="Maximum levels for subdomain brute-forcing")
    parser.add_argument("--threads", type=int, default=50, help="Number of concurrent threads")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")
    parser.add_argument("--no-xterm", action="store_true", help="Disable terminal output (use console instead)")
    parser.add_argument("--no-common", action="store_true", help="Disable common wordlists (brute-force only)")
    parser.add_argument("--output", type=str, help="Save results to file")
    return parser.parse_args()

def print_final_results(found_items, args):
    """Print final results to console and optionally save to file"""
    output = format_results(found_items)
    print("\n" + output)

    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(output.replace(Fore.RED, '').replace(Fore.GREEN, '').replace(Fore.YELLOW, '')
                        .replace(Fore.BLUE, '').replace(Fore.CYAN, '').replace(Fore.WHITE, '')
                        .replace(Style.RESET_ALL, ''))
            print(f"{Fore.GREEN}[+] Results saved to: {args.output}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to save results: {e}{Style.RESET_ALL}")

def main():
    args = parse_args()

    # Validate arguments
    if not (args.subdom or args.subdir):
        print(f"{Fore.RED}[!] Error: You must enable at least one of --subdom or --subdir{Style.RESET_ALL}")
        sys.exit(1)

    if args.max_length > 15:
        print(f"{Fore.YELLOW}[!] Warning: Max length >15 may take a very long time{Style.RESET_ALL}")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != 'y':
            sys.exit(0)

    if args.threads > 100:
        print(f"{Fore.YELLOW}[!] Warning: High thread count may cause connection issues{Style.RESET_ALL}")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != 'y':
            args.threads = 50

    print_banner()

    # Start memory monitor
    memory_thread = threading.Thread(target=monitor_memory, daemon=True)
    memory_thread.start()

    try:
        print(f"{Fore.BLUE}[*] Target:{Style.RESET_ALL} {args.target_domain}")
        print(f"{Fore.BLUE}[*] Threads:{Style.RESET_ALL} {args.threads}")
        print(f"{Fore.BLUE}[*] Timeout:{Style.RESET_ALL} {args.timeout}s")
        print(f"{Fore.BLUE}[*] Path Depth:{Style.RESET_ALL} {args.max_depth}")
        print(f"{Fore.BLUE}[*] Subdomain Levels:{Style.RESET_ALL} {args.max_levels}")
        print(f"{Fore.BLUE}[*] Common Wordlists:{Style.RESET_ALL} {'Disabled' if args.no_common else 'Enabled'}")
        print(f"{Fore.BLUE}[*] Terminal Output:{Style.RESET_ALL} {'Disabled' if args.no_xterm else 'Enabled'}")

        start_time = time.time()
        found_items = asyncio.run(main_brute_force(args))
        elapsed = time.time() - start_time

        print(f"\n{Fore.GREEN}[+] Scan completed in {elapsed:.2f} seconds{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Total findings: {len(found_items)}{Style.RESET_ALL}")

        print_final_results(found_items, args)

    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[-] User interrupted. Exiting...{Style.RESET_ALL}")
        print_final_results(found_items, args)
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        print_final_results(found_items, args)
    finally:
        # Clean up terminal if it exists
        if 'terminal_manager' in globals():
            terminal_manager.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}[!] Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)
