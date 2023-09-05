from flask import Flask, jsonify, request, Response, make_response
from flask_restful import Resource, Api
import sqlite3
import requests
from flask_httpauth import HTTPBasicAuth
import platform
import psutil
import socket
import importlib
import subprocess
from datetime import datetime, timedelta
import os 
import re
from threading import Thread
from time import sleep

def background_task(interval_sec):
    conn = sqlite3.connect("monitor.sqlite")
    cursor = conn.cursor()
    while True:
        sleep(interval_sec)
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024**3) 
        mem_used = mem.used / (1024**3)
        mem_usage = (mem_used/mem_total)*100 
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("INSERT INTO usage(sysname, cpu_usage, memory_usage, dateandtime) values(?, ?, ?, ?)",('127.0.0.1', str(cpu), f'{mem_usage:.2f}',dt_string ))
        conn.commit()
        

processes = {
    1: 'firefox',
    2: 'gedit',
    3: 'gnome-calendar',
    4: 'gnome-calculator',
    5: 'python3',
    6: 'systemd',
    7: 'code',
    8: 'hello.py',
    9: 'test1.py',
    10: 'task.py'
}

processes1 = {
    2: 'gedit',
    8: 'hello.py',
    9: 'test1.py',
    10: 'task.py',
    6: 'systemd',
    3: 'gnome-calendar',
    4: 'gnome-calculator'
}

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

def getip(systemip):
    conn = sqlite3.connect("clientip.sqlite")
    cursor = conn.cursor()
    ipadd = cursor.execute("SELECT systemname FROM systems WHERE systemip =?",(systemip,))
    ipadd = ipadd.fetchone()
    conn.close()
    if ipadd:
        return True
    else:
        return False
    
def log(user, sysname, task, dateandtime):
    conn = sqlite3.connect("clientip.sqlite")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs(user, sysname, task, dateandtime) values(?,?,?,?)",(user, sysname, task, dateandtime))
    conn.commit()
    conn.close()

class OSInfo(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire system operating system details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/os"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:  
            os_name = platform.system()
            os_release = platform.release()
            os_version = platform.version()
            os_architecture = platform.machine()

            info = {
                'Operating System': os_name,
                'Release': os_release,
                'Version': os_version,
                'Architecture': os_architecture
            }
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            print("From Local")
            return response
        
class CPUInfo(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire system processor details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/processor"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:  
            cpu_count = psutil.cpu_count(logical=False)
            total_cpu_count = psutil.cpu_count(logical=True)
            max_freq = psutil.cpu_freq().max / 1000 
            min_freq = psutil.cpu_freq().min / 1000 
            cur_freq = psutil.cpu_freq().current / 1000 
            cpu_percentages = psutil.cpu_percent(percpu=True)
            info = [{
                'num_physical_cores': cpu_count,
                'num_total_cores': total_cpu_count,
                'max_frequency': f"{max_freq:.2f} GHz",
                'min_frequency': f"{min_freq:.2f} GHz",
                'current_frequency': f"{cur_freq:.2f} GHz",
                'cpu_percentages': [f"{x:.2f}%" for x in cpu_percentages],
                'total_cpu_usage':f"{psutil.cpu_percent()}%"
            }]
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class DiskInfo(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire system secondary memory details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/disk"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:  
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            disk_total = disk.total / (1024**3) 
            disk_free = disk.free / (1024**3) 
            disk_used = disk.used / (1024**3) 
            disk_percent_used = disk.percent
            read_bytes = disk_io.read_bytes / (1024**3) 
            write_bytes = disk_io.write_bytes / (1024**3)

            info = [{
                'total_disk_space': f"{disk_total:.2f} GB",
                'free_disk_space': f"{disk_free:.2f} GB",
                'used_disk_space': f"{disk_used:.2f} GB",
                'disk_percent_used': f"{disk_percent_used:.2f} %",
                'total_read_since_boot': f"{read_bytes:.2f} GB",
                'total_write_since_boot': f"{write_bytes:.2f} GB"
            }]
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response
        
class System_Info(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire system runtime details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/runtime"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:  
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            system_time = datetime.fromtimestamp(psutil.time.time()).strftime("%Y-%m-%d %H:%M:%S")
            num_processes = len(psutil.pids())
            uptime = timedelta(seconds=psutil.boot_time())
            info = [{
            'boot_time': boot_time,
            'system_time': system_time,
            'num_of_processes_running': num_processes,
            'uptime': str(uptime)
            }]
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class MemoryInfo(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire system memory details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/memory"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:  
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            mem_total = mem.total / (1024**3) 
            mem_available = mem.available / (1024**3) 
            mem_used = mem.used / (1024**3) 
            mem_percent_used = mem.percent

            swap_total = swap.total / (1024**3) 
            swap_used = swap.used / (1024**3) 
            swap_free = swap.free / (1024**3) 
            swap_percent_used = swap.percent

            info = [{
            'memory_present': f"{mem_total:.2f} GB",
            'memory_available': f"{mem_available:.2f} GB",
            'memory_used': f"{mem_used:.2f} GB",
            'memory_percent_used': f"{mem_percent_used:.2f}%",
            'swap_total': f"{swap_total:.2f} GB",
            'swap_used': f"{swap_used:.2f} GB",
            'swap_free': f"{swap_free:.2f} GB",
             'swap_percent_used': f"{swap_percent_used:.2f}%"
            }]
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class NetworkInfo(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire system network details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/os"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:  
            addresses = psutil.net_if_addrs()
            network_info_list = []
            for interface in addresses:
                ip_address = ''
                mac_address = ''
                broadcast_ip = ''
                netmask = ''
                for address in addresses[interface]:
                    if address.family == socket.AF_INET:
                        ip_address = address.address
                    elif address.family == psutil.AF_LINK:
                        mac_address = address.address
            
                if ip_address:
                    ip_parts = ip_address.split('.')
                    netmask = '.'.join(['255'] * (len(ip_parts) - 1) + ['0'])
                    broadcast_parts = [str(int(ip_parts[i]) | int(netmask.split('.')[i])) for i in range(len(ip_parts))]
                    broadcast_ip = '.'.join(broadcast_parts)

        
                network_info = {'interface': interface,
                            'ip_address': ip_address,
                            'mac_address': mac_address,
                            'broadcast_ip': broadcast_ip,
                            'netmask': netmask}
                network_info_list.append(network_info)

            info = [{'network_info': network_info_list}]
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class inssoft(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire installed software details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/installed"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            output = subprocess.check_output(['apt-mark', 'showmanual']).decode('utf-8').strip().split('\n')
            packages = []
            for package in output:
                package_info = subprocess.check_output(['dpkg-query', '-W', '-f', '${Package}\t${Version}\t${Architecture}\t${Maintainer}\n', package]).decode('utf-8').strip().split('\t')
                package_dict = {
                    'package_name': package_info[0],
                    'version': package_info[1],
                    'architecture': package_info[2],
                    'maintainer': package_info[3]
                }
                packages.append(package_dict)
            response = make_response(jsonify(packages), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class usbdevices(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire connected usb devices details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/usb"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            output = subprocess.check_output(['lsusb']).decode('utf-8')
            devices = []
            for line in output.split('\n'):
                if not line:
                    continue
                parts = line.split()
                devices.append({
                    'bus_number': parts[1],
                    'device_number': parts[3][:-1],
                    'vendor_id': parts[5][:4],
                    'product_id': parts[5][5:],
                    'device_name': ' '.join(parts[6:])
                })
            response = make_response(jsonify(devices), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response
        
class scsi(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire scsi details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/scsi"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            cmd = ['lsscsi']
            output = subprocess.check_output(cmd, universal_newlines=True)
            devices = []
            for line in output.splitlines()[1:]:
                device_info = line.strip().split()
                device = {
                    'HBA': device_info[0],
                    'channel': device_info[1],
                    'ID': device_info[2],
                    'LUN': device_info[3],
                    'type': device_info[4],
                    'vendor': device_info[5],
                    'model': ' '.join(device_info[6:])
                }
                devices.append(device)
            response = make_response(jsonify(devices), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response
        
class pci(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire connected pci details"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/pci"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            output = subprocess.check_output(['lspci']).decode('utf-8')
            devices = []
            for line in output.split('\n'):
                if line:
                    device = {}
                    device['address'], device['name'] = line.split(' ', 1)
                    devices.append(device)

            response = make_response(jsonify(devices), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class listofrunning(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire the list of running softwares"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/services/running"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            running_processes = []
            for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if process.info['name'] in processes.values():
                    process_num = list(processes.keys())[list(processes.values()).index(process.info['name'])]
                    cpu_percent = process.cpu_percent(interval=1)  
                    running_processes.append({
                        'process_number': process_num,
                        'pid': process.info['pid'],
                        'process_name': process.info['name'],
                        'cpu_percent': cpu_percent,  
                        'memory_percent': process.info['memory_percent']
                    })
            response = make_response(jsonify(running_processes), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class listofstopped(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire list of stopped softwares"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/services/stopped"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            stopped_processes = []
            for pid, process in processes.items():
                if not is_process_running(process):
                    stopped_processes.append({'pid': pid, 'process_name': process})
            response = make_response(jsonify(stopped_processes), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class listofcontrollable(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Acquire list of controllable softwares"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/services/control"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            response = make_response(jsonify(processes1), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class startprocess(Resource):
    @auth.login_required
    def post(self, pid):
        user = auth.username()
        task = "Starting a software"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/services/control/start/{pid}"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.post(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            if pid in processes1:
                if processes1[pid].endswith('.py'):  
                    script_path = os.path.join(os.getcwd(), processes1[pid])
                    process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, error = process.communicate()  

                    module_name = os.path.splitext(processes1[pid])[0]
                    module = importlib.import_module(module_name)
                    response = make_response(jsonify({'message': f'{processes1[pid]} started successfully.', 'error': error.decode('utf-8')}),200)
                    response.headers["Content-Type"] = "application/json"
                    log(user, "local", task, dt_string)
                    return response
                else:
                    subprocess.Popen(processes1[pid])
                    response = make_response(jsonify({'message': f'{processes1[pid]} started successfully.'}), 200)
                    response.headers["Content-Type"] = "application/json"
                    log(user, "local", task, dt_string)
                    return response
            else:
                response = make_response(jsonify({'error': 'Invalid process ID.'}), 400)
                response.headers["Content-Type"] = "application/json"
                log(user, "local", task, dt_string)
                return response

class stopprocess(Resource):
    @auth.login_required
    def post(self, process_id):
        user = auth.username()
        task = "Stopping a software"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/services/control/stop/{process_id}"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.post(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            if process_id in processes1:
                if processes1[process_id].endswith('.py'):  
                    process_name = os.path.splitext(processes1[process_id])[0]
                    subprocess.call(['pkill', '-f', process_name])  
                else:
                    subprocess.call(['pkill', '-f', processes1[process_id]]) 
        
                response = make_response(jsonify({'message': f'{processes1[process_id]} stopped successfully.'}), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, "local", task, dt_string)
                return response
            else:
                response = make_response(jsonify({'error': 'Invalid process ID.'}), 400)
                response.headers["Content-Type"] = "application/json"
                log(user, "local", task, dt_string)
                return response

class osname(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve operating system name"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/os/name"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            os_name = platform.system()
            info = {
            'Operating System': os_name
            }
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class osver(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve operating system version"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/os/version"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            os_version = platform.version()
            info = {
                'Version': os_version,
            }
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class cpupercentage(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "retrieve real time processor usage information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/processor/usage"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            response = make_response(jsonify({'cpu_percentage': f"{psutil.cpu_percent()}%"}), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class cpucores(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve processor cores information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/processor/cores"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            core_count = psutil.cpu_count(logical=False)
            core_info = {
            'core_count': core_count,
            'core_details': []
            }
            for core in range(core_count):
                core_details = {
                'core_number': core,
                'frequency': psutil.cpu_freq().current,
                'usage': psutil.cpu_percent(interval=1, percpu=True)[core]
                }
                core_info['core_details'].append(core_details)

            response = make_response(jsonify(core_info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class diskpartition(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve disk partition information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/disk/partition"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            try:
                partitions = psutil.disk_partitions()
                disk_partitions = []

                for partition in partitions:
                    partition_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'filesystem': partition.fstype
                    }
                disk_partitions.append(partition_info)

                response = make_response(jsonify(disk_partitions), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, "local", task, dt_string)
                return response
            except Exception as e:
                response = make_response(jsonify({'message': str(e)}), 500)
                response.headers["Content-Type"] = "application/json"
                log(user, "local", task, dt_string)
                return response

class memoryusage(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve real time memory usage information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/memory/usage"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            mem = psutil.virtual_memory()
            mem_total = mem.total / (1024**3) 
            mem_used = mem.used / (1024**3)
            mem_usage = (mem_used/mem_total)*100 
            response = make_response(jsonify({'memory_usage' : f'{mem_usage:.2f}%'}), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class networkhost(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve network hostname information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/network/hostname"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            hostname = socket.gethostname()
            info = {
            'hostname': hostname 
            }
            response = make_response(jsonify(info), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class networkip(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve network ip information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/software/network/ipaddress"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            ip_address=socket.gethostbyname(socket.gethostname())
            response = make_response(jsonify(ip_address), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class hardwareee(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve basic hardware information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            ram_size = psutil.virtual_memory().total / (1024 ** 3)
            hdd_partitions = psutil.disk_partitions(all=False)
            hdd_size = sum(psutil.disk_usage(partition.mountpoint).total for partition in hdd_partitions) / (1024 ** 3)
            cpu_model = ''
            with open('/proc/cpuinfo', 'r') as file:
                cpu_info = file.read()

            model_regex = re.compile(r'model name\s+: (.+)')
            match = model_regex.search(cpu_info)
            if match:
                cpu_model = match.group(1)
            response = make_response(jsonify({'RAM Size (GB)': ram_size, 'HDD Size (GB)': hdd_size, 'CPU Model': cpu_model }), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response

class hardwardevices(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve all device information"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/devices"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            cmd = ['lshw', '-json']
            output = subprocess.check_output(cmd)
            output_str = output.decode('utf-8').replace('true', 'True').replace('false', 'False')
            device_info = eval(output_str)
        
            children = device_info['children']
            result = {}
            for device in device_info['children']:
                if device.get('class') == 'system':
                    continue
                device_dict = {}
                device_dict['name'] = device.get('id', '')
                device_dict['description'] = device.get('description', '')
                device_dict['product'] = device.get('product', '')
                device_dict['vendor'] = device.get('vendor', '')
                device_dict['serial'] = device.get('serial', '')
                device_dict['logical_name'] = device.get('logicalname', '')
                device_dict['phys_id'] = device.get('physid', '')
                device_dict['bus_info'] = device.get('businfo', '')
                device_dict['configuration'] = device.get('configuration', '')
                device_dict['capabilities'] = device.get('capabilities', '')
                device_dict['width'] = device.get('width', '')
                device_dict['clock'] = device.get('clock', '')
                children = device.get('children', [])
                if children:
                    device_dict['children'] = children
                result[device.get('class')] = result.get(device.get('class'), []) + [device_dict]

            response = make_response(jsonify(result), 200)
            response.headers["Content-Type"] = "application/json"
            log(user, "local", task, dt_string)
            return response
                                                                 
def is_process_running(process_name):
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            return True
    return False


class logging(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve API call logs of the system"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/devices"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            conn = sqlite3.connect("clientip.sqlite")
            cursor = conn.cursor()

            cursor = cursor.execute("SELECT logid, user, sysname, task, dateandtime FROM logs ORDER BY logid DESC LIMIT 10")
            data = [
                dict( logid = row[0], user = row[1], systemname = row[2], task = row[3], dateandtime = row[4]) for row in cursor.fetchall()
            ]
            conn.close()
            if data is not None:
                response = make_response(jsonify(data), 200)
                log(user, d["sysip"], task, dt_string)
                response.headers["Content-Type"] = "application/json"
                return response
            else:
                response = make_response(jsonify("No logs present"), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                return response

class monitoring(Resource):
    @auth.login_required
    def get(self):
        user = auth.username()
        task = "Retrieve CPU and memory usage logs from the system"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        d = request.args.to_dict()
        if "sysip" in d:
            ipadd = getip(d["sysip"])
            if not ipadd:
                response = make_response("System not present", 200)
                response.headers["Content-Type"] = "text/plain"
                return response

            endpoint = f"http://{d['sysip']}:5000/hardware/devices"
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            try:
                response = requests.get(endpoint, auth=(ip_address,'demo123'))
            except:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
    	
            if response.status_code == 403:
                response = make_response("System is inactive",200)
                response.headers["Content-Type"] = "text/plain"
                return response
            elif response.status_code == 200:
                data = response.json()
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                print('From Remote')
                return response
        else:
            conn = sqlite3.connect("monitor.sqlite")
            cursor = conn.cursor()
            cursor = cursor.execute("SELECT logid, sysname, cpu_usage, memory_usage, dateandtime FROM usage ORDER BY logid DESC LIMIT 20")
            data = [
                dict( logid = row[0], sysname = row[1], cpu_usage = row[2], memory_usage = row[3], dateandtime = row[4]) for row in cursor.fetchall()
            ]
            conn.close()
            if data is not None:
                response = make_response(jsonify(data), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                return response
            else:
                response = make_response(jsonify("No logs present"), 200)
                response.headers["Content-Type"] = "application/json"
                log(user, d["sysip"], task, dt_string)
                return response
        

def read_cpu_info(self):
        cpu_model = ''
        with open('/proc/cpuinfo', 'r') as file:
            cpu_info = file.read()

        model_regex = re.compile(r'model name\s+: (.+)')
        match = model_regex.search(cpu_info)
        if match:
            cpu_model = match.group(1)

        return cpu_model


@auth.verify_password
def authenticate(username, password):
    conn = sqlite3.connect("clientip.sqlite")
    cursor = conn.cursor()
    
    cursor = cursor.execute("SELECT password FROM users WHERE username=?",(username,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == password:
        return True
    else:
        return False

api.add_resource(NetworkInfo, "/software/network")
api.add_resource(MemoryInfo, "/hardware/memory")
api.add_resource(System_Info, "/software/runtime")
api.add_resource(DiskInfo, "/hardware/disk")
api.add_resource(CPUInfo, '/hardware/processor')
api.add_resource(OSInfo, '/software/os')
api.add_resource(logging,"/logs")
api.add_resource(inssoft,"/software/installed")
api.add_resource(usbdevices,"/hardware/usb")
api.add_resource(scsi,"/hardware/scsi")
api.add_resource(pci,"/hardware/pci")
api.add_resource(listofrunning,"/services/running")
api.add_resource(listofstopped,"/services/stopped")
api.add_resource(listofcontrollable,"/services/control")
api.add_resource(startprocess,"/services/control/start/<int:pid>")
api.add_resource(stopprocess,"/services/control/stop/<int:process_id>")
api.add_resource(osname, "/software/os/name")
api.add_resource(osver, "/software/os/version")
api.add_resource(cpupercentage, "/hardware/processor/usage")
api.add_resource(cpucores, "/hardware/processor/cores")
api.add_resource(diskpartition, "/hardware/disk/partition")
api.add_resource(memoryusage, "/hardware/memory/usage")
api.add_resource(networkhost, "/software/network/hostname")
api.add_resource(networkip, "/software/network/ipaddress")
api.add_resource(hardwareee, "/hardware")
api.add_resource(hardwardevices, "/hardware/devices")

if __name__ == "__main__":
    daemon = Thread(target=background_task, args=(3,), daemon=True, name='Background')
    daemon.start()
    app.run(port = 5001,debug=True)
