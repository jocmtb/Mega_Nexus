# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from .models import Devices, Mcast_flows, Script_logs, Traffic_interfaces, ARP_data, IGMP_data
from django.http import HttpResponse,JsonResponse
from .forms import NameForm, IPForm, LoginForm, CompareForm, TrafficForm, IP_XR_Form
from django.template import RequestContext
from django.http import HttpResponseRedirect
from class2_device import BaseDevice, DeviceIOS, DeviceNXOS, DeviceIOSXR
from scripts_all import parse, Compare_flows, parse_interface, parse_arp, parse_igmp, parse_mcast
from scripts_all import parse_xr, Create_Excel_Table_xr
from datetime import datetime as dt
import time
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django import forms
from django.utils import timezone
import uuid
import json
from django.conf import settings
import os



@login_required(login_url='/polls/login/')
def index(request):
    #return HttpResponse("Hello, world. You're at the polls index.")
    #latest_question_list = Question.objects.order_by('-pub_date')[:5]
    #context = {'latest_question_list': latest_question_list}
    return render(request, 'polls/index.html')

def login_user(request):
    if request.method=='POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username= form.cleaned_data.get('your_email', 'default1')
            password= form.cleaned_data.get('your_password', 'default1')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/polls/')
            else:
                return HttpResponse('User does not exist')
    else:
        form = LoginForm()
        return render(request, 'polls/login.html', {'form': form} )

def logout_user(request):
    logout(request)
    return HttpResponse('User is now logout')

@login_required(login_url='/polls/login/')
def dashboard(request):
    if request.method=='POST':
        form = TrafficForm(request.POST)
        if form.is_valid():
            device_list = Devices.objects.all()
            host_ip= form.cleaned_data.get('devices')
            context = { 'form': form, 'hostname': host_ip.ip_address, 'device_list': device_list, 'host1': host_ip.hostname }
            return render(request, 'polls/dashboard.html', context)
    else:
        form = TrafficForm()
        device_list = Devices.objects.all()
        context = { 'form': form, 'hostname': '10.0.166.249', 'device_list': device_list, 'host1': 'TVD-SW-N9K-VIDEO1-QRO' }
        return render(request, 'polls/dashboard.html', context)

@login_required(login_url='/polls/login/')
def dashboard2(request,hostname):
    if request.method=='POST':
        '''form = TrafficForm(request.POST)
        if form.is_valid():
            device_list = Devices.objects.all()
            host_ip= form.cleaned_data.get('devices')
            context = { 'form': form, 'hostname': host_ip.ip_address, 'device_list': device_list, 'host1': host_ip.hostname }
            return render(request, 'polls/dashboard.html', context)'''
    else:
        form = TrafficForm()
        device_list = Devices.objects.all()
        host_fetch=Devices.objects.get(ip_address=hostname)
        if host_fetch:
            host_name=host_fetch.hostname
            context = { 'form': form, 'hostname': hostname, 'device_list': device_list, 'host1': host_name }
            return render(request, 'polls/dashboard.html', context)
        else:
            HttpResponse('No host in database with that IP-Address')


@login_required(login_url='/polls/login/')
def script_type(request, option_id):
    #tipo = get_object_or_404(Question, pk=option_id)
    return render(request, 'polls/detail.html', {'tiposc': option_id})

def thanks(request, name):
    return render(request, 'polls/thanks.html', {'user_id': name})
'''
def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)
'''
@login_required(login_url='/polls/login/')
def about(request):
    return render(request, 'polls/about.html', {'user_id': 'jocmtb'})
    #return HttpResponse("This page is created by %s." % 'jocmtb')

@login_required(login_url='/polls/login/')
def traffic_interface(request):
    if request.method == 'POST':
        form = IPForm(request.POST)
        if form.is_valid():
            host_ip= form.cleaned_data.get('alternativas').ip_address
            router=DeviceNXOS(host_ip, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            stdout=router.ssh_connect(['show interface'])
            if isinstance(stdout,tuple):
                return HttpResponse('{0} > {1}'.format(stdout[0],stdout[1]) )
            interfaces=parse_interface(stdout)
            for interfaz in interfaces.keys():
                device_now = Traffic_interfaces(host_id=host_ip,
                                            interface_id=interfaz,
                                             input_rate=interfaces[interfaz]['input_rate'],
                                             output_rate=interfaces[interfaz]['output_rate'],
                                             data_date=timezone.now() )
                device_now.save()
            return render(request, 'polls/thanks.html', {'user_id': host_ip} )
    else:
        form = IPForm()
        return render(request, 'polls/launch_script.html', {'form': form, 'type_var': 'traffic'} )

@login_required(login_url='/polls/login/')
def arp_info(request):
    if request.method == 'POST':
        form = IPForm(request.POST)
        if form.is_valid():
            host_ip= form.cleaned_data.get('alternativas').ip_address
            router=DeviceNXOS(host_ip, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            stdout=router.ssh_connect(['show interface description | i Vlan',
                                        'show mac address-table ',
                                        'show ip arp' ] )
            if isinstance(stdout,tuple):
                return HttpResponse('{0} > {1}'.format(stdout[0],stdout[1]) )
            dict_ARP,lista_MAC=parse_arp(stdout)
            for arp in lista_MAC:
                device_now = ARP_data(host_id=host_ip,
                                            arp_ip=arp['mac_ip'],
                                             arp_mac=arp['mac_add'],
                                             arp_intf=arp['mac_intf'],
                                             arp_vlan=arp['mac_vlan'],
                                             vlan_name=arp['vlan_name'],
                                             datetime=timezone.now() )
                device_now.save()
            return render(request, 'polls/thanks.html', {'user_id': host_ip} )
    else:
        form = IPForm()
        return render(request, 'polls/launch_script.html', {'form': form, 'type_var': 'arp_data'} )

@login_required(login_url='/polls/login/')
def xr_mcast(request):
    if request.method == 'POST':
        form = IP_XR_Form(request.POST)
        if form.is_valid():
            host_ip= form.cleaned_data.get('your_ip')
            x = dt.now()
            date1 = ("%s-%s-%s_%s-%s-%s" % (x.year, x.month, x.day,x.hour,x.minute,x.second) )
            router=BaseDevice(host_ip, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            output_data=router.send_command(parse_mcast,['show mrib vrf ?'])
            docfile='./polls/session_logs/'+host_ip+'_mcast_'+date1
            with open(docfile,'w') as file:
                file.write(router.buffer)
            f1 = open (docfile,'r')
            lista_MCAST_GRP,dict_MCAST_GRP=parse_xr(f1)
            f1.close()
            filename=Create_Excel_Table_xr(host_ip,date1,lista_MCAST_GRP)
            return render(request, 'polls/thanks.html', {'user_id': host_ip, 'file_name': filename} )
    else:
        form = IP_XR_Form()
        return render(request, 'polls/launch_script.html', {'form': form, 'type_var': 'xr_mcast'} )

@login_required(login_url='/polls/login/')
def join_igmp(request):
    if request.method == 'POST':
        form = IPForm(request.POST)
        if form.is_valid():
            host_ip= form.cleaned_data.get('alternativas').ip_address
            router=DeviceNXOS(host_ip, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            stdout=router.ssh_connect(['show ip igmp groups'] )
            if isinstance(stdout,tuple):
                return HttpResponse('{0} > {1}'.format(stdout[0],stdout[1]) )
            lista_IGMP=parse_igmp(stdout)
            for arp in lista_IGMP:
                device_now = IGMP_data(host_id=host_ip,
                                            mcast_grp=arp['mcast_grp'],
                                             mcast_src=arp['mcast_src'],
                                             reporter_ip=arp['reporter_ip'],
                                             intf=arp['intf'],
                                             version=arp['version'],
                                             datetime=timezone.now() )
                device_now.save()
            return render(request, 'polls/thanks.html', {'user_id': host_ip} )
    else:
        form = IPForm()
        return render(request, 'polls/launch_script.html', {'form': form, 'type_var': 'join_igmp'} )


@login_required(login_url='/polls/login/')
def get_name(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NameForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            host_ip= form.cleaned_data.get('your_ip')
            router=DeviceNXOS(host_ip, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            stdout=router.ssh_connect(['show version','show inventory'])
            router.get_hostname()
            router.get_version()
            router.parse_shinvchassis()
            device_now = Devices.objects.filter(ip_address=host_ip)
            if device_now.count() == 0:
                ts=time.time()
                st = dt.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                new_host = Devices(hostname=router.hostname, ip_address=host_ip
                         ,version=router.version, platform=router.platform )
                new_host.save()
            else:
                device_now = Devices.objects.get(ip_address=host_ip)
                device_now.hostname=router.hostname
                device_now.version=router.version
                device_now.platform=router.platform
                device_now.save()
            return render(request, 'polls/thanks.html', {'user_id': host_ip} )
            #return HttpResponse("Thanks for submitting your Form %s." % name1)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = NameForm()
    return render(request, 'polls/launch_script.html', {'form': form, 'type_var': 'addon'} )

@login_required(login_url='/polls/login/')
def delete_device(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NameForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            host_ip= form.cleaned_data.get('your_ip')
            router=DeviceNXOS(host_ip, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            stdout=router.ssh_connect(['show version','show inventory'])
            router.get_hostname()
            router.get_version()
            router.parse_shinvchassis()
            device_now = Devices.objects.filter(ip_address=host_ip)
            if device_now.count() == 0:
                return HttpResponse("Device with IP: %s does not Exist." % host_ip)
            else:
                device_now = Devices.objects.get(ip_address=host_ip)
                device_now.delete()
            return render(request, 'polls/thanks.html', {'user_id': host_ip} )
            #return HttpResponse("Thanks for submitting your Form %s." % name1)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = NameForm()
    return render(request, 'polls/launch_script.html', {'form': form, 'type_var': 'delete'} )

@login_required(login_url='/polls/login/')
def show_logs(request):
    if request.method == 'POST':
        form = IPForm(request.POST)
        if form.is_valid():
            ip1= form.cleaned_data.get('alternativas').ip_address
            router=BaseDevice(ip1, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            output_data=router.ssh_connect(['show ip mroute detail'])
            if type(output_data)==tuple:
                return HttpResponse('Hit Exception: {0} {1}'.format(output_data[0],output_data[1] ) )
            lista_MCAST_GRP,dict_MCAST_GRP=parse(output_data)
            file_name='mcastflow_'+str(uuid.uuid4())
            file_path='./polls/session_logs/'+file_name
            with open(file_path,'w') as file:
                file.write(output_data)
            date_now=timezone.now()
            entrada= Script_logs(host_id=ip1,script_type='mcastflow'
                                ,file_location=file_name
                                 ,data_date=date_now)
            entrada.save()
            for x in lista_MCAST_GRP:
                entrada= Mcast_flows(src_mcast=x['mcast_grp'][0],mcast_grp=x['mcast_grp'][1]
                                 ,host_id=ip1
                                ,in_intf=x['in_intf']
                                 ,rpf_neighbor=x['rpf_nbr']
                                 ,flow_status=x['stat_flow']
                                 ,out_intf=x['out_intfs']
                                 ,data_date=date_now)
                entrada.save()
            return render(request, 'polls/show_logs.html', {'form': form, 'log_file_contents': output_data, 'type_form': 'mcast_flows'} )
    else:
        form = IPForm()
    return render(request, 'polls/show_logs.html', {'form': form, 'type_form': 'mcast_flows'} )

@login_required(login_url='/polls/login/')
def session_logs(request):
    if request.method == 'POST':
        form = IPForm(request.POST)
        if form.is_valid():
            ip1= form.cleaned_data.get('alternativas').ip_address
            router=BaseDevice(ip1, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            output_data=router.ssh_connect(['show ip mroute detail'])
            if type(output_data)==tuple:
                return HttpResponse('Hit Exception: {0} {1}'.format(output_data[0],output_data[1] ) )
            date_now=timezone.now()
            return render(request, 'polls/show_logs.html', {'form': form, 'log_file_contents': output_data, 'type_form': 'session_logs'} )
    else:
        form = IPForm()
        file_name=request.GET.get('file_name', '')
        file_path='./polls/session_logs/'+file_name
        with open(file_path,'r') as file:
            file_data=file.read()
    return render(request, 'polls/show_logs.html', {'form': form, 'type_form': 'session_logs', 'log_file_contents': file_data} )

@login_required(login_url='/polls/login/')
def backup(request):
    if request.method == 'POST':
        form = IPForm(request.POST)
        if form.is_valid():
            ip1= form.cleaned_data.get('alternativas').ip_address
            router=BaseDevice(ip1, user=settings.TACACS_USER, password=settings.TACACS_PASSWORD)
            output_data=router.ssh_connect(settings.LISTA_CMD)
            if type(output_data)==tuple:
                return HttpResponse('Hit Exception: {0} {1}'.format(output_data[0],output_data[1] ) )
            date_now=timezone.now()
            file_name='backup_'+str(uuid.uuid4())
            file_path='./polls/session_logs/'+file_name
            with open(file_path,'w') as file:
                file.write(output_data)
            entrada= Script_logs(host_id=ip1,script_type='backup'
                                ,file_location=file_name
                                 ,data_date=date_now)
            entrada.save()
            return render(request, 'polls/show_logs.html', {'form': form, 'log_file_contents': output_data, 'type_form': 'backup'} )
    else:
        form = IPForm()
    return render(request, 'polls/show_logs.html', {'form': form, 'type_form': 'backup'} )

@login_required(login_url='/polls/login/')
def compare_mcast(request):
    if request.method == 'POST':
        form = CompareForm(request.POST)
        if form.is_valid():
            flow1= form.cleaned_data.get('alternativas1')
            flow2= form.cleaned_data.get('alternativas2')
            file_path1='./polls/session_logs/'+flow1.file_location
            with open(file_path1,'r') as file:
                lista_MCAST_GRP,dict_MCAST_GRP=parse(file.read())
            file_path2='./polls/session_logs/'+flow2.file_location
            with open(file_path2,'r') as file:
                lista_MCAST_GRP2,dict_MCAST_GRP2=parse(file.read())
            joc=Compare_flows(dict_MCAST_GRP,dict_MCAST_GRP2)
            data_tabla = json.dumps( {"data": joc} )
            return render(request, 'polls/compare_mcast.html', { 'form': form, 'log_file_contents': 'mcast_flows'
                                                            , 'lista_diffs': data_tabla } )
    else:
        form = CompareForm()
    return render(request, 'polls/compare_mcast.html', {'form': form, 'type_form': 'compare_flows'} )

### APi ###
# All Api method return JSON responses
### APi ###
def api_traffic_table(request,hostname):
    data_list = []
    devs = Traffic_interfaces.objects.filter(host_id=hostname).all()
    if devs.count() != 0:
        for x in devs:
            data_list.append( { 'interface_id':x.interface_id,
                       'input_rate':x.input_rate,
                       'output_rate':x.output_rate,
                       'datetime':x.data_date} )
    return JsonResponse( {'data':data_list} )

def api_traffic(request,hostname):
    data_list = []
    devs = Traffic_interfaces.objects.filter(host_id=hostname).all()
    if devs.count() != 0:
        for x in devs:
            ts_seconds= (x.data_date - dt(1970,1,1)).total_seconds()
            tiempo= int(ts_seconds*1000)
            data_list.append( { 'interface_id':x.interface_id,
                       'input_rate':x.input_rate,
                       'output_rate':x.output_rate,
                       'datetime':tiempo} )
    return JsonResponse( {'data':data_list} )

def api_host_stats(request,stat_id):
    joc=[]
    joc2=[]
    joc3=[]
    if stat_id=='statsnxos1':
      host_list = Devices.objects.all()
      for x in host_list:
         joc.append(x.version)
         if x.version not in joc2:
           joc2.append(x.version)
      for x in joc2:
         joc3.append([x,joc.count(x)])
    return JsonResponse({'data':joc3})

def hostnames(request):
    data = {'data':[]}
    query_results = Devices.objects.all();
    for x in query_results:
        data['data'].append({'hostname':x.hostname,'IP_Address':x.ip_address,'platform':x.platform,'version':x.version})
    return JsonResponse(data)

def ajax_mcast_flows(request):
    data = {'data':[]}
    query_results = Mcast_flows.objects.all();
    for x in query_results:
        data['data'].append({'mcast_src':x.src_mcast,'mcast_grp':x.mcast_grp
                            ,'in_intf':x.in_intf,'out_intf':x.out_intf
                            ,'flow_stat':x.flow_status,'rpf_nei':x.rpf_neighbor
                            ,'datetime':x.data_date,'host':x.host_id})
    return JsonResponse(data)

def script_logs(request):
    data = {'data':[]}
    query_results = Script_logs.objects.all();
    if query_results.count() != 0:
        for x in query_results:
            data['data'].append({'sc_type':x.script_type,'file_name':x.file_location
                            ,'datetime':x.data_date,'host':x.host_id})
    return JsonResponse(data)

def script_logs_by_host(request,hostname):
    data = {'data':[]}
    query_results = Script_logs.objects.filter(host_id=hostname).all();
    if query_results.count() != 0:
        for x in query_results:
            data['data'].append({'sc_type':x.script_type,'file_name':x.file_location
                            ,'datetime':x.data_date,'host':x.host_id})
    return JsonResponse(data)

def api_arp(request,hostname):
    data_list = []
    devs = ARP_data.objects.filter(host_id=hostname).all()
    if devs.count() != 0:
        for x in devs:
            data_list.append( {  'host_id':x.host_id,
                        'arp_ip':x.arp_ip,
                       'arp_mac':x.arp_mac,
                       'arp_vlan':x.arp_vlan,
                       'vlan_name':x.vlan_name,
                       'arp_intf':x.arp_intf,
                       'datetime':x.datetime} )
    return JsonResponse( {'data':data_list} )

def api_join_igmp(request,hostname):
    data_list = []
    devs = IGMP_data.objects.filter(host_id=hostname).all()
    if devs.count() != 0:
        for x in devs:
            data_list.append( {  'host_id':x.host_id,
                        'mcast_grp':x.mcast_grp,
                       'mcast_src':x.mcast_src,
                       'reporter_ip':x.reporter_ip,
                       'version':x.version,
                       'intf':x.intf,
                       'datetime':x.datetime} )
    return JsonResponse( {'data':data_list} )

###TEST defs###
def download(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404
