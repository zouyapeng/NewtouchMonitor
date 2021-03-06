# -*- coding: utf-8 -*-

import json
from socket import socket, AF_INET, SOCK_STREAM
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render
from django.utils.encoding import force_text
from django.conf import settings

from django.views import generic
from django.core.urlresolvers import reverse_lazy, reverse

from models import *
from forms import ServerAddForm, ServerEditForm, CollertorAddForm
from api.hostInfo import HostInfo
from api.collector_api import ClientAPI
from api.redisPOperation import RedisHashOprt

CHART_HOST = None
HOST_AGETN_IP = None
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

        collectors = list(set([server.collector for server in context['servers']]))
        data = []
        for collector in collectors:
            data.extend(ClientAPI.getHyperInfo(collector.hostname, collector.port))
#         print data
        hosts = [HostInfo(info_dict) for info_dict in data]

        context['hosts'] = hosts
        return context

class MonitorDetailView(generic.TemplateView):
    template_name = 'server/monitor_detail.html'
    def get_context_data(self, **kwargs):
        context = super(MonitorDetailView, self).get_context_data(**kwargs)
        return context


class ChartData(generic.View):
    def get(self, request):
        global CHART_HOST, HOST_AGETN_IP
        list_name = 'list-a:'+str(HOST_AGETN_IP)+'-h:'+str(CHART_HOST)
        hash_name = 'hash-a:'+str(HOST_AGETN_IP)+'-h:'+str(CHART_HOST)
        print list_name, hash_name
        try:
            redis_obj = RedisHashOprt(settings.REDIS_HOSTNAME, settings.REDIS_PORT, db_numb=1)
            keys = redis_obj.getListValue(list_name, list_len=11, instance=False)
            data = redis_obj.filterHashTimeKey(hash_name, keys)
            return HttpResponse(json.dumps(data),
                            content_type='application/json')
        except:
            return HttpResponse(json.dumps({}),
                            content_type='application/json')
 
#         data = redis_obj.filterHashTimeKey(hash_name = CHART_HOST, chart_data=True)
#         data = redis_obj.filterHashTimeKey(hash_name = CHART_HOST,
#                                            start = '2015-11-30-15:13:03', end ='2015-11-30-17:33:06',
#                                            chart_data=True)
#         return HttpResponse(json.dumps(data),
#                             content_type='application/json')

class ChartHost(generic.View):
    def get(self, request):
        global CHART_HOST, HOST_AGETN_IP
        CHART_HOST = request.GET.get('host_ip')
        HOST_AGETN_IP = request.GET.get('agent_ip')
        return HttpResponse(json.dumps({}),
                            content_type='application/json')

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
            try:
                form.save(form)
                collertor = form.cleaned_data['collector']
                ClientAPI.setHostIPToCfg(collertor.hostname, collertor.port,form.cleaned_data['hostname'], add_to_config=True)
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

    def post(self, request, *args, **kwargs):
        form = ServerEditForm(request.POST)
        if form.is_valid():
            form.save(form)
        else:
            return self.form_invalid(form=form)
        return super(ServerEditView,self).post(request, *args, **kwargs)

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

class ServerDeleteView(generic.DeleteView):
    success_url =  reverse_lazy('newtouch:server:server_manager')
    model = Server

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(ServerDeleteView, self).get_object()
        collector = obj.collector
        print collector.hostname
        print collector.port
        print obj.hostname
        ClientAPI.setHostIPToCfg(collector.hostname, collector.port, obj.hostname, add_to_config=False)
        return obj



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