# -*- coding: utf-8 -*-

import json
from socket import socket, AF_INET, SOCK_STREAM
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.utils.encoding import force_text

from django.views import generic
from django.core.urlresolvers import reverse_lazy, reverse

from models import *
from forms import ServerAddForm, ServerEditForm, CollertorAddForm
from api.hostInfo import HostInfo
from api.socketPOperation import SocketOpt


# Agent Information
AGENT_IP = '223.167.85.2'
AGENT_PORT = 30024
ADDR = (AGENT_IP, AGENT_PORT)
BUFSIZ = 1024*1024

# Create your views here.
class IndexView(generic.TemplateView):
    template_name = 'server/index.html'

class MonitorView(generic.ListView):
    template_name = 'server/monitor.html'
    queryset = []

    def get_context_data(self, **kwargs):
        context = super(MonitorView, self).get_context_data(**kwargs)
        context['idcs'] = IDC.objects.all()
        context['tag'] = self.request.GET.get('tag')
        if context['tag']:
            idc = IDC.objects.get(name=context['tag'])
        else:
            idc = IDC.objects.get(name='ShangHai')
        context['servers'] = Server.objects.filter(location_id = idc.id)

        collertors = list(set([server.collector for server in context['servers']]))
        data = []
        for collertor in collertors:
            hostnames = [ server.hostname for server in collertor.collector_server.all()]
            hostnames = list(set(hostnames))
            socket = SocketOpt()
            data.extend(socket.getMonitorData(hostnames,collertor.hostname, collertor.port))

        hosts = [HostInfo(info_dict) for info_dict in data]

        context['hosts'] = hosts
        return context

class MonitorDetailView(generic.DetailView):
    template_name = 'server/monitor_detail.html'

class ManagerView(generic.ListView):
    template_name = 'server/manager.html'
    queryset = []

    def get_context_data(self, **kwargs):
        context = super(ManagerView,self).get_context_data(**kwargs)
        context['idcs'] = IDC.objects.all()
        context['tag'] = self.request.GET.get('tag')
        if context['tag']:
            idc = IDC.objects.get(name=context['tag'])
        else:
            idc = IDC.objects.get(name='ShangHai')
        context['servers'] = Server.objects.filter(location_id = idc.id)

        return context

class ServerAddView(generic.FormView):
    form_class = ServerAddForm
    success_url = reverse_lazy('newtouch:server:server_manager')
    template_name = 'server/manager_add.html'

    def post(self, request, *args, **kwargs):
        form = ServerAddForm(request.POST)
        if form.is_valid():
            print form.cleaned_data
            try:
                form.save(form)
            except Exception,e:
                print str(e)
                return self.form_invalid(form=form)
        else:
            return self.form_invalid(form=form)
        return super(ServerAddView,self).post(request, *args, **kwargs)


class ServerEditView(generic.FormView):
    form_class = ServerEditForm
    required_css_class = 'required'
    success_url = reverse_lazy('newtouch:server:server_manager')
    template_name = 'server/manager_edit.html'

    def get(self, request, *args, **kwargs):
        server = Server.objects.get(pk=kwargs.get('pk'))
        self.initial = {
            'id': kwargs.get('pk'),
            'hostname' : server.hostname,
            'location': server.location,
            'collector': server.collector,
            'user': server.user,
            'rules': server.rules.all(),
            'snmp_version': server.snmp_version,
            'snmp_commit': server.snmp_commit,
            'ssh_username':server.ssh_username ,
            'ssh_password':server.ssh_password
        }

        return super(ServerEditView,self).get(request,*args, **kwargs)

# class HypervisorDeleteView(generic.DeleteView):
#     success_url =  reverse_lazy('newtouch:hypervisors:hypervisors_manager')
#     model = Hypervisors

class CollectorView(generic.ListView):
    model = Collector
    template_name = 'server/collertor.html'
    context_object_name = 'collertors'

    def get_context_data(self, **kwargs):
        context = super(CollectorView, self).get_context_data(**kwargs)
        status = []
        for collector in context['collertors']:
            one_status = True
            # stauts = test_collertor(collector.hostname, collector.port)
            status.append(one_status)

        context['collertors'] = zip(context['collertors'], status)
        return  context


class CollectorDetailView(generic.DetailView):
    model = Collector
    template_name = 'server/collertor.html'
    context_object_name = 'collertor'

class CollertorAddView(generic.FormView):
    form_class = CollertorAddForm
    success_url = reverse_lazy('newtouch:server:server_collector')
    template_name = 'server/collertor_add.html'

    def get(self, request, *args, **kwargs):
        Collectors = Collector.objects.all().order_by('-id')
        if Collectors:
            id = Collectors[0].id + 1
        else:
            id = 1
        self.initial = {
            'id': id,
            'key' : uuid.uuid4()
        }

        return super(CollertorAddView,self).get(request,*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = CollertorAddForm(request.POST)
        if form.is_valid():
            print form.cleaned_data
            try:
                form.save(form)
            except Exception,e:
                return self.form_invalid(form=form)
        else:
            return self.form_invalid(form=form)
        return super(CollertorAddView,self).post(request, *args, **kwargs)

class CollertorEditView(generic.FormView):
    pass

# class CollertorDeteleView(generic.DeleteView):
#     pass